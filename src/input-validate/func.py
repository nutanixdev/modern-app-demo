import json
import logging
import os
from datetime import datetime
from uuid import uuid4

import boto3
from cloudevents.conversion import to_json
from parliament import Context

FUNC_NAME = os.environ.get('K_SERVICE', 'local')

FORMAT = f'%(asctime)s %(id)-36s {FUNC_NAME} %(message)s'
logging.basicConfig(format=FORMAT)

logger = logging.getLogger('boto3')
logger.setLevel(logging.INFO)


def categorize_source_file(filename):
    srcFileExt = os.path.splitext(filename)[1]
    match srcFileExt:
        case '.json':
            return 'Metadata'
        case '.mp4':
            return 'Video'


def s3_client():
    SSL_VERIFY = os.environ.get('SSL_VERIFY', False)
    AWS_REGION = os.environ['AWS_REGION']
    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    AWS_S3_ENDPOINT_URL = os.environ['AWS_S3_ENDPOINT_URL']

    session = boto3.Session()
    return session.client('s3',
                          endpoint_url=AWS_S3_ENDPOINT_URL,
                          aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                          region_name=AWS_REGION,
                          verify=SSL_VERIFY)


def main(context: Context):
    source_attributes = context.cloud_event.get_attributes()

    logger.info(
        f'REQUEST:: {to_json(context.cloud_event)}', extra=source_attributes)

    try:
        srcBucket = context.cloud_event.data['Records'][0]['s3']['bucket']['name']
        if srcBucket is not os.environ['S3_SOURCE_BUCKET']:
            logger.info(
                f'IGNORING:: Request for bucket {srcBucket}', extra=source_attributes)
            return None

        srcFile = context.cloud_event.data['Records'][0]['s3']['object']['key']

        data = {
            'guid': str(uuid4()),
            'kafkaGuid': source_attributes['id'],
            'kafkaTopic': source_attributes['source'],
            'startTime': datetime.utcnow().isoformat(timespec='milliseconds')+'Z',
            'workflowTrigger': categorize_source_file(srcFile),
            'workflowStatus': 'Ingest',
            'workflowName': FUNC_NAME,
            'srcBucket': srcBucket,
            'destBucket': os.environ['S3_DESTINATION_BUCKET'],
        }

        match data['workflowTrigger']:
            case 'Metadata':
                logger.info(f'Validating Metadata file::',
                            extra=source_attributes)

                data['srcMetadataFile'] = srcFile

                metadata = s3_client().get_object(Bucket=srcBucket, Key=srcFile)

                metadataFile = json.loads(metadata['Body'])
                try:
                    metadataFile['srcVideo']
                except KeyError:
                    raise Exception(
                        'srcVideo is not defined in metadata::', metadataFile)

                for k, v in metadataFile.items():
                    data[k] = v

            case 'Video':
                data['srcVideo'] = srcFile

        attributes = {
            "type": f'com.nutanix.gts.{FUNC_NAME}',
            "source": FUNC_NAME,
        }

        event = context.cloud_event.create(attributes, data)

        logger.info(
            f"Sent {event['id']} of type {event['type']}", extra=source_attributes)

        return event

    except Exception as err:
        payload = {
            'id': source_attributes['id'],
            'event': to_json(context.cloud_event),
            'function': FUNC_NAME,
            'error': str(err)
        }

        logger.error(f'ERROR:: {json.dumps(payload)}', extra=source_attributes)
        raise err
