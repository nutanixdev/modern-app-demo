from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('video/<str:video_id>/', views.play_video, name='play-video')
]
