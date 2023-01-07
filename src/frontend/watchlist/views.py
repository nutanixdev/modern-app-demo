
import m3u8
import requests
import urllib3
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound, StreamingHttpResponse
from django.shortcuts import render

from .utils import get_signed_url

urllib3.disable_warnings()

URL = settings.VOD_BACKEND_API
SSL_VERIFY = settings.SSL_VERIFY


@login_required
def index(request):
    response = requests.get(URL, verify=SSL_VERIFY, timeout=5)

    print(request.META)
    print(request.headers)

    data = response.json()

    for video in data:
        if video.get('frameCapture'):
            if request.is_secure():
                video['frameCapture'] = get_signed_url(
                    video['destBucket'], video['frameCapture'])
            else:
                video['frameCapture'] = get_signed_url(
                    video['destBucket'], video['frameCapture'], scheme='http')

    context = {
        'videos': data,
    }
    return render(request, 'index.html', context)


@login_required
def player(request, video_guid):
    if request.GET.get('destBucket') and request.GET.get('hlsPlaylist'):
        bucket = request.GET['destBucket']
        fileobj = request.GET['hlsPlaylist']
    else:
        endpoint = '/'.join([URL, str(video_guid)])
        response = requests.get(endpoint, verify=SSL_VERIFY, timeout=5)

        if response.ok:
            bucket = response.json()['destBucket']
            fileobj = response.json()['hlsPlaylist']
        else:
            return HttpResponseNotFound(response.content)

    context = {
        'playlist': fileobj.split("/")[-1],
        'destBucket': bucket
    }
    return render(request, 'watchlist/player.html', context)


@login_required
def get_playlist(request, video_guid):
    if request.GET.get('destBucket'):
        bucket = request.GET['destBucket']
    else:
        endpoint = '/'.join([URL, str(video_guid)])
        response = requests.get(endpoint, verify=SSL_VERIFY, timeout=5)

        if response.ok:
            bucket = response.json()['destBucket']
        else:
            return HttpResponseNotFound(response.content)

    fileobj = request.path.strip('/').split('/', 1)[-1]

    if request.is_secure():
        signed_url = get_signed_url(bucket, fileobj)
    else:
        signed_url = get_signed_url(bucket, fileobj, 'http')

    playlist = m3u8.load(signed_url, verify_ssl=SSL_VERIFY)

    if playlist.is_variant:
        for variant in playlist.playlists:
            variant.uri = f'{variant.uri}?destBucket={bucket}'
    else:
        for segment in playlist.segments:
            ts_fileobj = '/'.join([str(video_guid), segment.uri])
            if request.is_secure():
                ts_signed_url = get_signed_url(bucket, ts_fileobj)
            else:
                ts_signed_url = get_signed_url(bucket, ts_fileobj, 'http')
            segment.uri = ts_signed_url

    return StreamingHttpResponse(playlist.dumps())
