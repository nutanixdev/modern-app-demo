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

        newvalues = {"$set": data}

        collection.update_one(
            filter, newvalues, upsert=True
        )

        imported_video = collection.find_one(filter)

        logger.info(
            f'UPDATE:: {imported_video}', extra=source_attributes)

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