import json
import logging
import os
import shutil
import subprocess
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from cloudevents.conversion import to_json
from parliament import Context

FUNC_NAME = os.environ.get('K_SERVICE', 'local')

FORMAT = f'%(asctime)s %(id)-36s {FUNC_NAME} %(message)s'
logging.basicConfig(format=FORMAT)

logger = logging.getLogger('boto3')
logger.setLevel(logging.INFO)

RENDITIONS = [
    {'name': '240p', 'resolution': '426x240',
        'bitrate': '600k', 'audiorate': '64k',
        'maxrate': '642k', 'bufsize': '900k'},
    {'name': '360p', 'resolution': '640x360',
        'bitrate': '900k', 'audiorate': '96k',
        'maxrate': '963k', 'bufsize': '1350k'},
    {'name': '480p', 'resolution': '842x480',
        'bitrate': '1600k', 'audiorate': '128k',
        'maxrate': '1712k', 'bufsize': '2400k'},
    {'name': '720p', 'resolution': '1280x720',
        'bitrate': '3200k', 'audiorate': '128k',
        'maxrate': '3424k', 'bufsize': '4800k'},
    {'name': '1080p', 'resolution': '1920x1080',
        'bitrate': '5300k', 'audiorate': '192k',
        'maxrate': '5671k', 'bufsize': '7950k'},
]

# FFMPEG_PATH = "/usr/local/bin"
# FFMPEG_BIN = "ffmpeg"
# FFMPEG_EXEC = os.path.join(FFMPEG_PATH, FFMPEG_BIN)

S3_DESTINATION_BUCKET = os.environ.get("S3_DESTINATION_BUCKET", None)


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


def get_signed_url(bucket, obj):
    SIGNED_URL_EXPIRATION = 60 * 60 * 2

    return s3_client().generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': obj},
        ExpiresIn=SIGNED_URL_EXPIRATION
    )


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    try:
        response = s3_client().upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def main(context: Context):
    source_attributes = context.cloud_event.get_attributes()

    logger.info(
        f'REQUEST:: {to_json(context.cloud_event)}', extra=source_attributes)

    try:
        data = context.cloud_event.data
        srcBucket = data['srcBucket']
        srcVideo = data['srcVideo']
        guid = data['guid']
        encodingProfile = data['encodingProfile']

        # To add output from encoding
        data['detail'] = {}
        data['detail']['outputGroupDetails'] = []

        Path(f'output/{guid}').mkdir(parents=True, exist_ok=True)

        # os.makedirs(f'output/{guid}')

        signed_url = get_signed_url(
            srcBucket, srcVideo)
        logger.info(f'SIGNED URL:: {signed_url}', extra=source_attributes)

        command = ['ffmpeg', '-i', signed_url,
                   '-ar', '48000', '-c:a', 'aac', '-c:v', 'h264', '-crf', '20',
                   '-g', '48', '-hls_playlist_type', 'vod',
                   '-hls_segment_filename', f'output/{guid}/%v_%03d.ts', '-hls_time', '4',
                   '-keyint_min', '48', '-master_pl_name', 'playlist.m3u8', '-profile:v', 'main',
                   '-sc_threshold', '0']

        params_maps_args = []
        params_filters_args = []
        params_stream_maps_args = []

        for i, v in enumerate(RENDITIONS):
            w = v['resolution'].split(
                'x')[0]
            h = v['resolution'].split('x')[1]

            if int(h) > encodingProfile:
                break

            params_maps_args.extend(['-map', '0:v:0', '-map', '0:a:0'])
            params_stream_maps_args.append(f'v:{i},a:{i},name:{v["name"]}')

            scale_filter = [
                f'-filter:v:{i}',
                f'scale=w={w}:h={h}:force_original_aspect_ratio=decrease',
                '-b:v',
                v['bitrate'],
                f'-maxrate:v:{i}',
                v['maxrate'],
                '-bufsize',
                v['bufsize'],
                f'-b:a:{i}',
                v['audiorate']
            ]
            params_filters_args.extend(scale_filter)

        command.extend([
            '-var_stream_map',
            '{}'.format(' '.join(params_stream_maps_args))])

        command.extend(params_maps_args)
        command.extend(params_filters_args)

        command.append(f'output/{guid}/out_%v.m3u8')

        subprocess.check_output(command)

        playlistFilePaths = []

        for root, dirs, files in os.walk(f'output/{guid}'):
            for filename in files:

                # construct the full local path
                local_path = os.path.join(root, filename)

                # construct the full Dropbox path
                relative_path = os.path.relpath(local_path, f'output/{guid}')
                s3_path = os.path.join(guid, relative_path)

                logger.info(
                    f'Searching {s3_path} in {S3_DESTINATION_BUCKET}', extra=source_attributes)

                upload_file(local_path, S3_DESTINATION_BUCKET, s3_path)

                playlistFilePaths.append(s3_path)

        data['detail']['outputGroupDetails'].append(
            {
                'type': 'HLS_GROUP',
                'playlistFilePaths': playlistFilePaths
            }
        )

        shutil.rmtree(f'output/{guid}')

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
