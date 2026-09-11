import { useEffect, useRef } from 'react';
import { useVoiceOS } from './useVoiceOS';

export default function Waveform() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { state } = useVoiceOS();

  useEffect(() => {
    if (state === 'Idle') return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let time = 0;

    const render = () => {
      time += 0.08;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const isListening = state === 'Listening';
      const isResponding = state === 'Responding';
      const amp = isListening ? 14 : (isResponding ? 10 : 6);
      
      const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
      if (isListening) {
        gradient.addColorStop(0, 'rgba(0, 240, 255, 0.2)');
        gradient.addColorStop(0.5, '#00f0ff');
        gradient.addColorStop(1, 'rgba(0, 240, 255, 0.2)');
      } else if (isResponding) {
        gradient.addColorStop(0, 'rgba(16, 185, 129, 0.2)');
        gradient.addColorStop(0.5, '#34d399');
        gradient.addColorStop(1, 'rgba(16, 185, 129, 0.2)');
      } else {
        gradient.addColorStop(0, 'rgba(99, 102, 241, 0.2)');
        gradient.addColorStop(0.5, '#818cf8');
        gradient.addColorStop(1, 'rgba(99, 102, 241, 0.2)');
      }

      ctx.beginPath();
      ctx.moveTo(0, canvas.height / 2);

      for (let i = 0; i < canvas.width; i++) {
        const freq = isListening ? 0.07 : 0.04;
        const y = Math.sin(i * freq + time) * amp + canvas.height / 2;
        ctx.lineTo(i, y);
      }

      ctx.strokeStyle = gradient;
      ctx.lineWidth = 2.5;
      ctx.stroke();

      animationId = requestAnimationFrame(render);
    };

    render();

    return () => cancelAnimationFrame(animationId);
  }, [state]);

  if (state === 'Idle') return null;

  return (
    <canvas
      ref={canvasRef}
      width={360}
      height={32}
      className="w-full h-[32px] opacity-90 block"
    />
  );
}
