from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    re_path(r'^video/(?P<video_guid>.*)/.*\.m3u8/?$',
            views.get_playlist, name='get-playlist'),
    path('video/<uuid:video_guid>/',
         views.player, name='player'),
]
