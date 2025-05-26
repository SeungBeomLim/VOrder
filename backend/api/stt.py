import os
import sys
import numpy as np
import queue
import threading
import time
import tempfile
import soundfile as sf
import sounddevice as sd

from openai import OpenAI
from collections import deque

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
    
# 1) query_devices() 로 인덱스 확인 (한 번만 하면 됩니다)
print(sd.query_devices())
#    ... MacBook Pro Microphone 이 0번이면 ...
mic_index = 2

# 2) 기본 입력 장치로 설정
# (출력은 지정할 필요 없으면 None)
# sd.default.device = (mic_index, None)
sd.default.device = (None, None)
print(sd.device)

audio_queue = queue.Queue()
samplerate = 16000
block_size = 4000

caption_history = deque(maxlen=5)
current_caption = ""
caption_lock = threading.Lock()

# 종료어 설정
exit_keyword = "stop"  # 종료어 설정 (여기서는 'stop')

def audio_callback(indata, frames, time, status):
    if status:
        print(f"Status: {status}", file=sys.stderr)
    audio_queue.put(indata.copy())


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def update_captions():
    clear_screen()
    print("\n\n\n")
    print("=" * 60)
    print("🎙️ Real-time Speech-to-Text Captions (Press Ctrl+C to exit)")
    print("=" * 60)

    for prev in list(caption_history)[:-1]:
        print(f"\033[90m{prev}\033[0m")

    if caption_history:
        print(list(caption_history)[-1])

    if current_caption:
        print(f"\033[1m{current_caption}\033[0m", end="▋\n")
    else:
        print("▋")
    print("=" * 60)

def audio_collection_thread():
    try:
        with sd.InputStream(samplerate=samplerate, channels=1, 
                          callback=audio_callback, blocksize=block_size):
            print("🎙️ Real-time STT is starting... Please wait.")
            while True:
                time.sleep(0.1)
    except Exception as e:
        print(f"Audio stream error: {e}", file=sys.stderr)
    except KeyboardInterrupt:
        pass


def stt_processing_thread():
    global current_caption
    buffer = np.zeros((0, 1), dtype=np.float32)
    max_buffer_size = samplerate * 5
    stop_detected = False  # 종료어가 이미 감지되었는지 여부

    try:
        while True:
            try:
                data = audio_queue.get(timeout=1)
                buffer = np.concatenate((buffer, data), axis=0)

                if len(buffer) > max_buffer_size:
                    buffer = buffer[-max_buffer_size:]

                chunk_size = int(samplerate * 3.0)
                if len(buffer) >= chunk_size:
                    # 👉 Ignore very quiet sounds (for noise removal)
                    if np.abs(buffer).mean() < 0.01:
                        buffer = np.zeros((0, 1), dtype=np.float32)
                        continue
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        sf.write(f.name, buffer[:chunk_size], samplerate)
                        audio_file = open(f.name, "rb")
                        response = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language="en"
                        )
                        audio_file.close()
                        os.unlink(f.name)

                    text = response.text.strip()
                    # 👉 Ignore very short or meaningless texts
                    if not text:
                        buffer = np.zeros((0, 1), dtype=np.float32)
                        continue

                    with caption_lock:
                        if not current_caption or text[0].isupper() or any(current_caption.endswith(p) for p in ['.', '!', '?', '。', '！', '？']):
                            if current_caption:
                                caption_history.append(current_caption)
                            current_caption = text
                        else:
                            current_caption += " " + text
                    
                    # 종료어를 확인하여 프로그램 종료
                    if exit_keyword.lower() in text.lower() and not stop_detected:
                        stop_detected = True  # 종료어가 감지되었음을 기록
                        print("\n🛑 Exit keyword detected. Shutting down...")
                        with open("captions.txt", "w") as f:
                            for caption in caption_history:
                                f.write(caption + "\n")
                            if exit_keyword.lower() not in current_caption.lower():
                                f.write(current_caption + "\n")
                        os._exit(0)
                        
                    update_captions()
                    buffer = np.zeros((0, 1), dtype=np.float32)

                audio_queue.task_done()
            except queue.Empty:
                continue
    except KeyboardInterrupt:
        pass


def listen_and_transcribe(audio_path: str) -> str:
    """
    주어진 .wav 오디오 파일을 Whisper API로 텍스트로 변환합니다.
    """
    print(f"🎧 Running STT on: {audio_path}")
    try:
        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
        text = response.text.strip()
        print(f"📝 인식된 텍스트: {text}")
        return text
    except Exception as e:
        print(f"❌ STT error: {e}")
        return ""
    

if __name__ == "__main__":
    try:
        clear_screen()

        t1 = threading.Thread(target=audio_collection_thread)
        t2 = threading.Thread(target=stt_processing_thread)

        t1.daemon = True
        t2.daemon = True

        t1.start()
        t2.start()

        update_captions()

        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        clear_screen()
        print("\n🛑 Program is shutting down...")
        time.sleep(0.5)
        print("👋 Shutdown complete")

