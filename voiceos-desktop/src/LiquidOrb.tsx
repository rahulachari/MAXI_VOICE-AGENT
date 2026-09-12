import React, { useEffect, useRef } from 'react';
import {
  shaderSource,
  stateSeeds,
  activationDurationMs,
  settleDurationMs,
} from './liquidOrbShader';

export interface LiquidOrbProps {
  state?: 'idle' | 'thinking';
  size?: number;
  className?: string;
}

const LiquidOrb: React.FC<LiquidOrbProps> = ({
  state = 'idle',
  size = 56,
  className = '',
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const stateRef = useRef<'idle' | 'thinking'>(state);
  const setStateFnRef = useRef<((nextState: 'idle' | 'thinking') => void) | null>(null);

  useEffect(() => {
    stateRef.current = state;
    if (setStateFnRef.current) {
      setStateFnRef.current(state);
    }
  }, [state]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const cvs: HTMLCanvasElement = canvas;

    let stopped = false;
    let animationFrame = 0;
    let device: any = null;

    let currentState = stateRef.current;
    let transitionTargetState = currentState;
    let fromUniforms = new Float32Array(stateSeeds[currentState]);
    let targetUniforms = new Float32Array(stateSeeds[currentState]);
    const displayedUniforms = new Float32Array(stateSeeds[currentState]);
    let transitionStartedAt = 0;
    let activeTransitionDuration = 0;
    let lastFrameAt: number | null = null;
    let motionPhase = 0;

    function srgbToLinear(value: number) {
      return value <= 0.04045
        ? value / 12.92
        : ((value + 0.055) / 1.055) ** 2.4;
    }

    function linearToSrgb(value: number) {
      return value <= 0.0031308
        ? value * 12.92
        : 1.055 * value ** (1 / 2.4) - 0.055;
    }

    function mixSrgb(from: number, to: number, progress: number) {
      return linearToSrgb(
        srgbToLinear(from) + (srgbToLinear(to) - srgbToLinear(from)) * progress
      );
    }

    function transitionProgress(now: number) {
      if (activeTransitionDuration === 0) return 1;
      const raw = Math.min(1, Math.max(0, (now - transitionStartedAt) / activeTransitionDuration));
      return transitionTargetState === 'thinking'
        ? 1 - (1 - raw) ** 3
        : raw * raw * (3 - 2 * raw);
    }

    function sampleTransition(now: number) {
      const progress = transitionProgress(now);
      for (let index = 3; index < displayedUniforms.length; index += 1) {
        const colorComponent = index >= 40 && (index - 40) % 4 < 3;
        displayedUniforms[index] = colorComponent
          ? mixSrgb(fromUniforms[index], targetUniforms[index], progress)
          : fromUniforms[index] + (targetUniforms[index] - fromUniforms[index]) * progress;
      }
      return displayedUniforms;
    }

    function setOrbState(nextState: 'idle' | 'thinking') {
      if (nextState === currentState) return;
      const now = performance.now();
      sampleTransition(now);
      fromUniforms = new Float32Array(displayedUniforms);
      targetUniforms = new Float32Array(stateSeeds[nextState]);
      transitionTargetState = nextState;
      transitionStartedAt = now;
      activeTransitionDuration = nextState === 'thinking' ? activationDurationMs : settleDurationMs;
      currentState = nextState;
    }

    setStateFnRef.current = setOrbState;

    async function initWebGPU() {
      const nav = navigator as any;
      if (!nav.gpu) {
        throw new Error('WebGPU not supported');
      }
      const adapter = await nav.gpu.requestAdapter();
      if (!adapter) throw new Error('No compatible WebGPU adapter');
      device = await adapter.requestDevice();
      const context: any = cvs.getContext('webgpu');
      if (!context) throw new Error('Unable to create WebGPU canvas context');

      const format = nav.gpu.getPreferredCanvasFormat();
      context.configure({ device, format, alphaMode: 'premultiplied' });

      const shader = device.createShaderModule({ code: shaderSource });
      const pipeline = device.createRenderPipeline({
        layout: 'auto',
        vertex: { module: shader, entryPoint: 'vs_main' },
        fragment: {
          module: shader,
          entryPoint: 'fs_main',
          targets: [
            {
              format,
              blend: {
                color: {
                  srcFactor: 'one',
                  dstFactor: 'one-minus-src-alpha',
                  operation: 'add',
                },
                alpha: {
                  srcFactor: 'one',
                  dstFactor: 'one-minus-src-alpha',
                  operation: 'add',
                },
              },
            },
          ],
        },
        primitive: { topology: 'triangle-list' },
      });

      const values = new Float32Array(displayedUniforms);
      const uniformBuffer = device.createBuffer({
        size: values.byteLength,
        usage: 64 | 8, // UNIFORM | COPY_DST
      });

      const bindGroup = device.createBindGroup({
        layout: pipeline.getBindGroupLayout(0),
        entries: [{ binding: 0, resource: { buffer: uniformBuffer } }],
      });

      function frame(now: number) {
        if (stopped) return;
        try {
          const dpr = Math.min(window.devicePixelRatio || 1, 2);
          const width = Math.max(1, Math.floor(cvs.clientWidth * dpr));
          const height = Math.max(1, Math.floor(cvs.clientHeight * dpr));
          if (cvs.width !== width || cvs.height !== height) {
            cvs.width = width;
            cvs.height = height;
          }

          values.set(sampleTransition(now));
          const frameDelta = lastFrameAt === null ? 0 : Math.min(0.1, Math.max(0, (now - lastFrameAt) / 1000));
          lastFrameAt = now;
          motionPhase += frameDelta * Math.max(values[3], 0);

          values[0] = width;
          values[1] = height;
          values[2] = motionPhase / Math.max(values[3], 0.001);

          device.queue.writeBuffer(uniformBuffer, 0, values);

          const encoder = device.createCommandEncoder();
          const pass = encoder.beginRenderPass({
            colorAttachments: [
              {
                view: context.getCurrentTexture().createView(),
                clearValue: { r: 0, g: 0, b: 0, a: 0 },
                loadOp: 'clear',
                storeOp: 'store',
              },
            ],
          });
          pass.setPipeline(pipeline);
          pass.setBindGroup(0, bindGroup);
          pass.draw(3);
          pass.end();
          device.queue.submit([encoder.finish()]);

          animationFrame = requestAnimationFrame(frame);
        } catch {
          // fallback
        }
      }

      animationFrame = requestAnimationFrame(frame);
    }

    // High-performance Canvas Fallback if WebGPU is disabled
    function initCanvasFallback() {
      const ctx = cvs.getContext('2d');
      if (!ctx) return;
      const context2d: CanvasRenderingContext2D = ctx;

      let phase = 0;
      function renderFallback(_now: number) {
        if (stopped) return;
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        const w = Math.max(1, Math.floor(cvs.clientWidth * dpr));
        const h = Math.max(1, Math.floor(cvs.clientHeight * dpr));
        if (cvs.width !== w || cvs.height !== h) {
          cvs.width = w;
          cvs.height = h;
        }

        const isThinking = currentState === 'thinking';
        const speed = isThinking ? 0.06 : 0.02;
        phase += speed;

        context2d.clearRect(0, 0, w, h);
        const cx = w / 2;
        const cy = h / 2;
        const r = Math.min(w, h) * 0.44;

        // Base circular body
        const bgGrad = context2d.createRadialGradient(cx, cy, 0, cx, cy, r);
        bgGrad.addColorStop(0, 'rgba(5, 10, 24, 0.95)');
        bgGrad.addColorStop(0.7, 'rgba(2, 4, 12, 0.98)');
        bgGrad.addColorStop(1, 'rgba(0, 0, 0, 1)');
        context2d.fillStyle = bgGrad;
        context2d.beginPath();
        context2d.arc(cx, cy, r, 0, Math.PI * 2);
        context2d.fill();

        // Siri chromatic wave bands
        const bandCount = 4;
        const colors = isThinking
          ? ['rgba(0, 240, 255, 0.65)', 'rgba(59, 130, 246, 0.60)', 'rgba(168, 85, 247, 0.55)', 'rgba(236, 72, 153, 0.45)']
          : ['rgba(56, 189, 248, 0.45)', 'rgba(37, 99, 235, 0.40)', 'rgba(99, 102, 241, 0.35)', 'rgba(147, 197, 253, 0.30)'];

        for (let b = 0; b < bandCount; b++) {
          context2d.save();
          context2d.beginPath();
          context2d.arc(cx, cy, r - 1, 0, Math.PI * 2);
          context2d.clip();

          context2d.beginPath();
          const offset = (b * Math.PI) / 2;
          const amp = (isThinking ? 0.35 : 0.22) * r;

          context2d.moveTo(cx - r, cy);
          for (let x = -r; x <= r; x += 4) {
            const xNorm = x / r;
            const env = Math.cos((Math.PI / 2) * xNorm);
            const y = amp * env * Math.sin(xNorm * 3.2 + phase * 1.8 + offset);
            context2d.lineTo(cx + x, cy + y);
          }
          context2d.lineTo(cx + r, cy + r);
          context2d.lineTo(cx - r, cy + r);
          context2d.closePath();

          context2d.fillStyle = colors[b];
          context2d.fill();
          context2d.restore();
        }

        // White core filament crest
        context2d.save();
        context2d.beginPath();
        context2d.arc(cx, cy, r - 1, 0, Math.PI * 2);
        context2d.clip();
        context2d.beginPath();
        const coreAmp = (isThinking ? 0.32 : 0.18) * r;
        context2d.moveTo(cx - r, cy);
        for (let x = -r; x <= r; x += 3) {
          const xNorm = x / r;
          const env = Math.cos((Math.PI / 2) * xNorm);
          const y = coreAmp * env * Math.sin(xNorm * 3.4 + phase * 1.8);
          context2d.lineTo(cx + x, cy + y);
        }
        context2d.strokeStyle = 'rgba(255, 255, 255, 0.75)';
        context2d.lineWidth = isThinking ? 2.5 : 1.5;
        context2d.stroke();
        context2d.restore();

        // Liquid glass refraction rim
        context2d.beginPath();
        context2d.arc(cx, cy, r, 0, Math.PI * 2);
        context2d.strokeStyle = 'rgba(255, 255, 255, 0.25)';
        context2d.lineWidth = 1;
        context2d.stroke();

        // Top specular highlight arc
        const specGrad = context2d.createLinearGradient(cx - r * 0.4, cy - r * 0.7, cx + r * 0.4, cy);
        specGrad.addColorStop(0, 'rgba(255, 255, 255, 0.55)');
        specGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');
        context2d.fillStyle = specGrad;
        context2d.beginPath();
        context2d.ellipse(cx, cy - r * 0.42, r * 0.46, r * 0.22, 0, 0, Math.PI * 2);
        context2d.fill();

        animationFrame = requestAnimationFrame(renderFallback);
      }

      animationFrame = requestAnimationFrame(renderFallback);
    }

    initWebGPU().catch(() => {
      initCanvasFallback();
    });

    return () => {
      stopped = true;
      cancelAnimationFrame(animationFrame);
      if (device) {
        device.destroy?.();
      }
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className={`liquid-orb-canvas ${className}`}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        display: 'block',
        borderRadius: '50%',
        pointerEvents: 'none',
      }}
      aria-label="Liquid Siri Orb"
    />
  );
};

export default LiquidOrb;
