import json
import logging
import os
from datetime import datetime

from cloudevents.conversion import to_json
from parliament import Context

FUNC_NAME = os.environ.get('K_SERVICE', 'local')

FORMAT = f'%(asctime)s %(id)-36s {FUNC_NAME} %(message)s'
logging.basicConfig(format=FORMAT)

logger = logging.getLogger('boto3')
logger.setLevel(logging.INFO)


def main(context: Context):
    source_attributes = context.cloud_event.get_attributes()

    logger.info(
        f'REQUEST:: {to_json(context.cloud_event)}', extra=source_attributes)

    try:
        data = context.cloud_event.data

        data['workflowStatus'] = 'Complete'
        data['endTime'] = datetime.utcnow().isoformat(
            timespec='milliseconds')+'Z'

        for output in data['encodingOutput']['outputGroupDetails']:
            match output['type']:
                case 'HLS_GROUP':
                    data['hlsPlaylist'] = output['playlistFilePaths'][0]
                    data['hlsUrl'] = f"{data['cdnObjects']}/{data['destBucket']}/{data['hlsPlaylist']}"

                    break
                case 'DASH_ISO_GROUP':
                    data['dashPlaylist'] = output['playlistFilePaths'][0]
                    data['dashUrl'] = f"{data['cdnObjects']}/{data['destBucket']}/{data['dashPlaylist']}"

                    break

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
