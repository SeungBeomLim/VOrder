import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Order() {
  const navigate = useNavigate();
  const [chatLog, setChatLog] = useState<{ role: 'user' | 'assistant'; text: string }[]>([]);
  const [recording, setRecording] = useState(false);
  const [introPlayed, setIntroPlayed] = useState(false);
  const [assistantAudioUrl, setAssistantAudioUrl] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);

  const startRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'recording') {
      audioChunksRef.current = [];
      mediaRecorderRef.current.start();
      setRecording(true);

      setTimeout(() => {
        if (mediaRecorderRef.current?.state === 'recording') {
          mediaRecorderRef.current.stop();
        }
      }, 4000);
    }
  };

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => audioChunksRef.current.push(e.data);

      recorder.onstop = async () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio', blob, 'input.wav');

        const response = await fetch('http://localhost:8000/api/process/', {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const result = await response.json();
          const { user_text, assistant_text, audio_url, final } = result;
          console.log('Audio url: ', audio_url);

          setChatLog((prev) => [
            ...prev,
            { role: 'user', text: user_text },
            { role: 'assistant', text: assistant_text },
          ]);

          // 캐시 방지용 타임스탬프 추가
          setAssistantAudioUrl(`${audio_url}?t=${Date.now()}`);

          if (final) {
            setRecording(false);
            setTimeout(() => navigate('/confirm-order'), 1500);
            return;
          }
        }

        audioChunksRef.current = [];
        setRecording(false);
      };

      if (!introPlayed) {
        const introAudio = new Audio('http://localhost:8000/media/intro.mp3');
        introAudio.onended = () => {
          setIntroPlayed(true);
          startRecording();
        };
        introAudio.play();
      }
    });
  }, [navigate, introPlayed]);

  useEffect(() => {
    if (assistantAudioUrl && audioRef.current) {
      audioRef.current.src = assistantAudioUrl;

      audioRef.current.onended = () => {
        console.log('🔊 Assistant TTS finished, now recording...');
        startRecording();
      };

      audioRef.current
        .play()
        .then(() => console.log('🔊 Assistant audio playing'))
        .catch((err) => console.warn('Audio autoplay failed:', err));
    }
  }, [assistantAudioUrl]);

  const handleCancel = () => {
    setRecording(false); // ✅ cancel 시 녹음 중단
    navigate('/');
  };

  return (
    <div className="w-[390px] h-[844px] mx-auto bg-[#F6F6F6] flex flex-col pt-10 px-6 shadow-lg rounded-xl overflow-hidden relative">
      {/* Header */}
      <div className="absolute top-0 left-0 w-full bg-[#F6F6F6] z-10 flex items-center justify-between p-4 h-[60px]">
        <img src="/menu.svg" alt="Menu" className="w-5 h-5" />
        <h1 className="text-lg font-bold text-[#1C1B1F]">VOrder</h1>
        <img src="/notification.svg" alt="Notification" className="w-5 h-5" />
      </div>

      {/* Chat Section */}
      <div className="pt-[70px] pb-[140px] overflow-y-auto flex-1 w-full">
        {chatLog.map((msg, idx) => (
          <div
            key={idx}
            className={`px-4 py-2 my-2 rounded-xl max-w-[80%] ${
              msg.role === 'user' ? 'bg-[#DCF8C6] self-end ml-auto' : 'bg-white self-start mr-auto'
            }`}
          >
            <p className="text-sm text-[#1C1B1F] whitespace-pre-line">{msg.text}</p>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="absolute bottom-0 left-0 w-full px-6 py-4 border-t flex justify-center items-center z-10">
        <button
          onClick={handleCancel}
          className="bg-[#F24822] text-white rounded-full px-8 py-3 text-sm font-medium shadow"
        >
          Cancel
        </button>
      </div>

      <audio ref={audioRef} hidden />
    </div>
  );
}
