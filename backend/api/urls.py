from django.urls import path
from .views import STTProcessView
from .views import IntroTTSView
from .views import ConfirmTTSView

urlpatterns = [
    path('process/', STTProcessView.as_view(), name='stt-process'),
    path("intro/", IntroTTSView.as_view(), name="intro-tts"),
    path('confirm-tts', ConfirmTTSView.as_view(), name='confirm-tts'),
]