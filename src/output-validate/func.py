import json
import logging
import os
from datetime import datetime

from cloudevents.conversion import to_json
from parliament import Context
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

FUNC_NAME = os.environ.get('K_SERVICE', 'local')

FORMAT = f'%(asctime)s %(id)-36s {FUNC_NAME} %(message)s'
logging.basicConfig(format=FORMAT)

logger = logging.getLogger('boto3')
logger.setLevel(logging.INFO)


def mongo_client():
    MONGODB_USERNAME = os.environ['MONGODB_USERNAME']
    MONGODB_PASSWORD = os.environ['MONGODB_PASSWORD']
    MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'mongodb')
    MONGODB_ADDRESS = os.environ['MONGODB_ADDRESS']
    MONGODB_PORT = os.environ.get('MONGODB_PORT', 27017)

    DB_URI = f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_ADDRESS}:{MONGODB_PORT}/{MONGODB_DATABASE}?authSource=admin&directConnection=true'

    client = MongoClient(DB_URI, serverSelectionTimeoutMS=1)
    try:
        client.admin.command('ismaster')
        print("Connected to the MongoDB database!")
    except ConnectionFailure:
        print("Server not available")
        raise ConnectionFailure

    return client[MONGODB_DATABASE]


def main(context: Context):
    source_attributes = context.cloud_event.get_attributes()

    logger.info(
        f'REQUEST:: {to_json(context.cloud_event)}', extra=source_attributes)

    try:
        data = context.cloud_event.data
        dbname = mongo_client()

        collection = dbname['videos']

        filter = {"_id": data['guid']}

        video = collection.find_one(filter)

        video['encodingOutput'] = data['detail']
        video['workflowStatus'] = 'Complete'
        video['endTime'] = datetime.utcnow().isoformat(
            timespec='milliseconds')+'Z'

        for output in data['detail']['outputGroupDetails']:
            match output['type']:
                case 'HLS_GROUP':
                    video['hlsPlaylist'] = output['playlistFilePaths'][0]
                    video['hlsUrl'] = f"{data['cdnObjects']}/{video['destBucket']}/{video['hlsPlaylist']}"

                    break
                case 'DASH_ISO_GROUP':
                    video['dashPlaylist'] = output['playlistFilePaths'][0]
                    video['dashUrl'] = f"{data['cdnObjects']}/{video['destBucket']}/{video['dashPlaylist']}"

                    break

        attributes = {
            "type": f'com.nutanix.gts.{FUNC_NAME}',
            "source": FUNC_NAME,
        }

        event = context.cloud_event.create(attributes, video)

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
