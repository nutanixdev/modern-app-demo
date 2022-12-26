import requests
import urllib3
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

urllib3.disable_warnings()

url = settings.VOD_BACKEND_API
SSL_VERIFY = settings.SSL_VERIFY


@login_required
def index(request):
    response = requests.get(url, verify=SSL_VERIFY, timeout=5)
    context = {
        'videos': response.json(),
    }
    return render(request, 'index.html', context)


@login_required
def play_video(request, video_id):
    endpoint = '/'.join([url, video_id])
    response = requests.get(endpoint, verify=SSL_VERIFY, timeout=5)

    context = {
        'video': response.json()
    }

    return render(request, 'watchlist/player.html', context)
