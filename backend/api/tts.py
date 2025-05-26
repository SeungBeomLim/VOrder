import os
import subprocess
import json

from pathlib import Path
from openai import OpenAI
from django.conf import settings

# --- Configuration ---
LANGUAGE_MODE = "English"   # Language Mode 
SPEECH_MODE = "Senior"       # Speech Mode : Child, Adult, Senior
VOICE = "ballad"            # Voice Setting (can change later )
## available options 
# Voice Profiles (TTS OpenAI & RelyWP)
# alloy  – young male, natural & smooth (friendly narration)
# echo   – young male, articulate & precise (clear, clipped delivery)
# fable  – young male, warm & engaging (storytelling)
# onyx   – older male, deep & authoritative (formal narration)
# nova   – young female, bright & energetic (upbeat)
# shimmer– young female, soft & gentle (calm/soothing)
# coral  – young female, cheerful & community-oriented (approachable)
# sage   – young female, wise & calm (tutorials/explanations)
# ash    – young male, enthusiastic & lively (energetic)
# ballad – poetic, melodic (storybook/lyric narration)
# verse  – expressive & dynamic (dramatic readings/poetry)

TTS_MODEL = "gpt-4o-mini-tts"

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("Please set the OPENAI_API_KEY environment variable.")
client = OpenAI(api_key=api_key)


def synthesize_and_play(text: str, filename: str):
    """
    Generate speech from text, save as MP3 (<filename>.mp3), then play.
    """
    output_path = Path(f"{filename}.mp3")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build mode-specific instructions
    if SPEECH_MODE == "Child":
        instr = (
            f"Speak the following text in a very high tone and a bit slowly with easier intonation and extra friendly style, "
            f"in {LANGUAGE_MODE} language."
        )
    elif SPEECH_MODE == "Adult":
        instr = (
            f"Speak the following text in a normal and clear voice, "
            f"in {LANGUAGE_MODE} language."
        )
    elif SPEECH_MODE == "Senior":
        instr = (
            f"Speak the following text quite a bit slowed down, more loud and clear, "
            f"with easier intonation—nice, kind, and friendly—"
            f"in {LANGUAGE_MODE} language."
        )
    else:
        instr = (
            f"Speak the following text clearly, "
            f"in {LANGUAGE_MODE} language."
        )

    # Call the TTS endpoint
    with client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=VOICE,
        input=text,
        instructions=instr,
    ) as response:
        response.stream_to_file(output_path)

    print(f"✅ Saved speech file: {output_path}")

    # Auto-play on macOS (afplay) or fallback
    try:
        subprocess.run(["afplay", str(output_path)], check=True)
    except FileNotFoundError:
        print("⚠️ 'afplay' not found—install it or replace with your OS player.")

if __name__ == "__main__":
    # Use the user's name field for text and filename
    user_name = "Justin"
    if not user_name:
        raise ValueError("Missing 'name' in data for TTS filename.")

    # Here, text to speak is the user name (customize if needed)
    synthesize_and_play(text="Welcome startbucks", filename=user_name)


def synthesize_and_save(text: str, filename: str) -> Path:
    output_path = Path(settings.MEDIA_ROOT) / f"{filename}.mp3"

    if SPEECH_MODE == "Child":
        instr = (
            f"Speak the following text in a very high tone and a bit slowly with easier intonation and extra friendly style, "
            f"in {LANGUAGE_MODE} language."
        )
    elif SPEECH_MODE == "Adult":
        instr = (
            f"Speak the following text in a normal and clear voice, "
            f"in {LANGUAGE_MODE} language."
        )
    elif SPEECH_MODE == "Senior":
        instr = (
            f"Speak the following text quite a bit slowed down, more loud and clear, "
            f"with easier intonation—nice, kind, and friendly—"
            f"in {LANGUAGE_MODE} language."
        )
    else:
        instr = (
            f"Speak the following text clearly, "
            f"in {LANGUAGE_MODE} language."
        )
    
    with client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=VOICE,
        input=text,
        instructions=instr,
    ) as response:
        response.stream_to_file(str(output_path))
    return output_path