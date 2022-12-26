import boto3
from django.conf import settings


def s3_client():
    SSL_VERIFY = settings.SSL_VERIFY
    AWS_REGION = settings.AWS_S3_REGION_NAME
    AWS_ACCESS_KEY_ID = settings.AWS_S3_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = settings.AWS_S3_SECRET_ACCESS_KEY
    AWS_S3_ENDPOINT_URL = settings.AWS_S3_ENDPOINT_URL

    session = boto3.Session()
    return session.client('s3',
                          endpoint_url=AWS_S3_ENDPOINT_URL,
                          aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                          region_name=AWS_REGION,
                          verify=SSL_VERIFY)


def get_signed_url(bucket, obj):
    # The number of seconds the presigned url is valid for. By default it expires in an hour (3600 seconds)
    SIGNED_URL_EXPIRATION = settings.AWS_PRESIGNED_EXPIRY

    return s3_client().generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': obj},
        ExpiresIn=SIGNED_URL_EXPIRATION
    )
