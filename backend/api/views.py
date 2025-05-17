import os
import uuid
import tempfile
from django.conf import settings
from django.http import FileResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from .stt import listen_and_transcribe
from .llm import order_agent
from .tts import synthesize_and_save

class STTProcessView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        print("🛠️ Received POST request at /api/process/")
        
        audio_file = request.FILES.get('audio')
        if not audio_file:
            print("🚫 No audio file provided")
            return Response({"error": "No audio file provided"}, status=400)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            for chunk in audio_file.chunks():
                temp_audio.write(chunk)
            temp_audio_path = temp_audio.name

        try:
            print(f"🎧 Running STT on: {temp_audio_path}")
            text = listen_and_transcribe(temp_audio_path)
            print(f"📝 STT result: {text}")
        except Exception as e:
            print(f"❌ STT error: {e}")
            return Response({"error": f"STT failed: {e}"}, status=500)
        finally:
            os.remove(temp_audio_path)

        try:
            reply, final_flag = order_agent(text)
            print(f"🤖 LLM reply: {reply} | Final: {final_flag}")
        except Exception as e:
            print(f"❌ LLM error: {e}")
            return Response({"error": f"LLM failed: {e}"}, status=500)

        filename = "latest_reply"  # .mp3 확장자 없이 순수한 파일명 생성

        try:
            output_path = synthesize_and_save(text=reply, filename=filename)
            print(f"🔊 TTS saved at: {output_path}")
        except Exception as e:
            print(f"❌ TTS error: {e}")
            return Response({"error": f"TTS failed: {e}"}, status=500)
        
        base_url = request.build_absolute_uri('/')[:-1]  # ex) http://localhost:8000

        return Response({
            "user_text": text,
            "assistant_text": reply,
            "audio_url": f"{base_url}{settings.MEDIA_URL}{filename}.mp3",
            "final": final_flag,
        })
    

class IntroTTSView(APIView):
    def post(self, request):
        intro_path = os.path.join(settings.MEDIA_ROOT, "intro.mp3")

        # 파일이 존재하지 않으면 생성
        if not os.path.exists(intro_path):
            intro_text = "Hello! Welcome to Starbucks Voice Order Agent. Start ordering! Choose between normal ordering, recommendation, or order using nickname."
            try:
                synthesize_and_save(text=intro_text, filename="intro")
            except Exception as e:
                return Response({"error": f"TTS generation failed: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"audio_url": f"{settings.MEDIA_URL}intro.mp3"})
    

class ConfirmTTSView(APIView):
    def get(self, request):
        text = request.GET.get("text")
        if not text:
            return Response({"error": "Missing 'text' query parameter"}, status=status.HTTP_400_BAD_REQUEST)

        filename = f"latest_confirm_reply"
        try:
            output_path = synthesize_and_save(text, filename)
        except Exception as e:
            return Response({"error": f"TTS failed: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return FileResponse(open(output_path, "rb"), content_type="audio/mpeg")