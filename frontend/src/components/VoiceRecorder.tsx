import { useState } from 'react';

export default function VoiceRecorder() {
  const [recording, setRecording] = useState(false);

  const handleRecord = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    const chunks: BlobPart[] = [];

    mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
    mediaRecorder.onstop = async () => {
      const blob = new Blob(chunks, { type: 'audio/wav' });
      const formData = new FormData();
      formData.append('audio', blob, 'recording.wav');

      const response = await fetch('http://localhost:8000/api/stt/', {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();
      alert(result.text);
    };

    mediaRecorder.start();
    setRecording(true);
    setTimeout(() => {
      mediaRecorder.stop();
      setRecording(false);
    }, 3000); // 3초 후 자동 정지
  };

  return (
    <div>
      <button onClick={handleRecord}>
        {recording ? '녹음 중...' : '🎙️ 녹음 시작'}
      </button>
    </div>
  );
}