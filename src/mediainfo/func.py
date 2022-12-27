import json
import logging
import os
import subprocess

import boto3
from botocore.config import Config
from cloudevents.conversion import to_json
from parliament import Context

SSL_VERIFY = os.environ.get("SSL_VERIFY", True)
FUNC_NAME = os.environ.get('K_SERVICE', 'local')

FORMAT = f'%(asctime)s %(id)-36s {FUNC_NAME} %(message)s'
logging.basicConfig(format=FORMAT)

logger = logging.getLogger('boto3')
logger.setLevel(logging.INFO)


def parse_number(num):
    if num is None:
        return None

    try:
        return int(num)
    except ValueError:
        return float(num)


def compact(attributes):
    return {k: v for k, v in attributes.items() if v is not None}


def parse_common_attributes(track):
    attributes = {}

    attributes['codec'] = track.get('Format')

    level = track.get('Format_Level')
    profile_values = [
        track.get('Format_Profile'),
        None if level is None else 'L' + level,
        track.get('Format_Tier')
    ]

    profile = '@'.join([i for i in profile_values if i is not None])
    if profile != '':
        attributes['profile'] = profile

    attributes['bitrate'] = parse_number(track.get('BitRate'))
    attributes['duration'] = parse_number(track.get('Duration'))
    attributes['frameCount'] = parse_number(track.get('FrameCount'))

    return attributes


def parse_general_attributes(track):
    attributes = {}

    attributes['format'] = track.get('Format')
    attributes['fileSize'] = parse_number(track.get('FileSize'))
    attributes['duration'] = parse_number(track.get('Duration'))
    attributes['totalBitrate'] = parse_number(track.get('OverallBitRate'))

    return compact(attributes)


def parse_video_attributes(track):
    attributes = parse_common_attributes(track)

    attributes['width'] = parse_number(track.get('Width'))
    attributes['height'] = parse_number(track.get('Height'))
    attributes['framerate'] = parse_number(track.get('FrameRate'))
    attributes['scanType'] = track.get('ScanType')
    attributes['aspectRatio'] = track.get('DisplayAspectRatio')

    attributes['bitDepth'] = parse_number(track.get('BitDepth'))
    attributes['colorSpace'] = '{0} {1}'.format(
        track.get('ColorSpace'), track.get('ChromaSubsampling'))

    return compact(attributes)


def parse_audio_attributes(track):
    attributes = parse_common_attributes(track)

    attributes['bitrateMode'] = track.get('BitRate_Mode')
    attributes['language'] = track.get('Language')
    attributes['channels'] = parse_number(track.get('Channels'))
    attributes['samplingRate'] = parse_number(track.get('SamplingRate'))
    attributes['samplePerFrame'] = parse_number(track.get('SamplesPerFrame'))

    return compact(attributes)


def parse_text_attributes(track):
    attributes = {}

    attributes['id'] = track.get('ID')
    attributes['format'] = track.get('Format')
    attributes['duration'] = parse_number(track.get('Duration'))
    attributes['frameCount'] = parse_number(track.get('Count'))
    attributes['captionServiceName'] = parse_number(
        track.get('CaptionServiceName'))

    return compact(attributes)


def s3_client():
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


def get_signed_url(bucket, obj):
    # The number of seconds the presigned url is valid for. By default it expires in an hour (3600 seconds)
    SIGNED_URL_EXPIRATION = os.environ.get('SIGNED_URL_EXPIRATION', 3600)

    return s3_client().generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': obj},
        ExpiresIn=SIGNED_URL_EXPIRATION
    )


def main(context: Context):
    source_attributes = context.cloud_event.get_attributes()

    logger.info(
        f'REQUEST:: {to_json(context.cloud_event)}', extra=source_attributes)

    try:
        data = context.cloud_event.data
        srcBucket = data['srcBucket']
        srcVideo = data['srcVideo']

        metadata = {}
        metadata['filename'] = srcVideo

        signed_url = get_signed_url(
            srcBucket, srcVideo)
        logger.info(f'SIGNED URL:: {signed_url}', extra=source_attributes)

        if SSL_VERIFY:
            command = ['/usr/bin/mediainfo',
                       '--Output=JSON', signed_url]
        else:
            command = ['/usr/bin/mediainfo', '--Ssl_IgnoreSecurity=',
                       '--Output=JSON', signed_url]

        json_content = json.loads(subprocess.check_output(command))
        logger.info(
            f'MEDIAINFO OUTPUT:: {json.dumps(json_content)}', extra=source_attributes)

        tracks = json_content['media']['track']
        for track in tracks:
            track_type = track['@type']
            if (track_type == 'General'):
                metadata['container'] = parse_general_attributes(track)
            elif (track_type == 'Video'):
                metadata.setdefault('video', []).append(
                    parse_video_attributes(track))
            elif (track_type == 'Audio'):
                metadata.setdefault('audio', []).append(
                    parse_audio_attributes(track))
            elif (track_type == 'Text'):
                metadata.setdefault('text', []).append(
                    parse_text_attributes(track))
            else:
                logger.warning(
                    f'TRACK UNSUPPORTED:: {track_type}', extra=source_attributes)

        data['srcMediainfo'] = metadata

        logger.info(f'RESPONSE:: {json.dumps(metadata)}',
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
