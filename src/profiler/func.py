import json
import logging
import os

from cloudevents.conversion import to_json
from parliament import Context
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

FUNC_NAME = os.environ.get('K_SERVICE', 'local')
MONGODB_USERNAME = os.environ['MONGODB_USERNAME']
MONGODB_PASSWORD = os.environ['MONGODB_PASSWORD']
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'mongodb')
MONGODB_ADDRESS = os.environ['MONGODB_ADDRESS']
MONGODB_PORT = os.environ.get('MONGODB_PORT', 27017)

DB_URI = f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_ADDRESS}:{MONGODB_PORT}/{MONGODB_DATABASE}?authSource=admin&directConnection=true'


FORMAT = f'%(asctime)s %(id)-36s {FUNC_NAME} %(message)s'
logging.basicConfig(format=FORMAT)

logger = logging.getLogger('boto3')
logger.setLevel(logging.INFO)


def profile_check(profiles, videoHeight):
    lastProfile = profiles[0]
    encodeProfile = abs(videoHeight - profiles[0])

    for item in profiles:
        profile = abs(videoHeight - item)
        if profile > lastProfile:
            return encodeProfile

        encodeProfile = item
        lastProfile = profile

    return encodeProfile


def main(context: Context):
    source_attributes = context.cloud_event.get_attributes()

    logger.info(
        f'REQUEST:: {to_json(context.cloud_event)}', extra=source_attributes)

    client = MongoClient(DB_URI, serverSelectionTimeoutMS=1)
    try:
        client.admin.command('ismaster')
        print("Connected to the MongoDB database!")
    except ConnectionFailure:
        print("Server not available")
        raise ConnectionFailure

    try:
        data = context.cloud_event.data
        dbname = client[MONGODB_DATABASE]

        collection = dbname['videos']

        filter = {"_id": data['guid']}

        video = collection.find_one(filter)

        for k, v in video.items():
            data[k] = v

        mediaInfo = data['srcMediainfo']
        data['srcHeight'] = mediaInfo['video'][0]['height']
        data['srcWidth'] = mediaInfo['video'][0]['width']

        profiles = [2160, 1080, 720]

        data['encodingProfile'] = profile_check(
            profiles=profiles, videoHeight=data['srcHeight'])

        logger.info(f'RESPONSE:: {json.dumps(data)}',
                    extra=source_attributes)

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
