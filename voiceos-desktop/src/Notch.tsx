import { motion } from 'framer-motion';
import LiquidOrb from './LiquidOrb';
import { useVoiceOS } from './useVoiceOS';
import Waveform from './Waveform';
import GlassSurface from './GlassSurface';

export default function Notch() {
  const { state, transcript, lastActionText } = useVoiceOS();

  const isExpanded = state === 'Listening' || state === 'Thinking' || state === 'Responding';
  const width = isExpanded ? 520 : 170;
  const height = isExpanded ? 98 : 38;

  // Map state to hand-tuned ThinkingOrb states from libraries.dev:
  // "working" | "searching" | "solving" | "listening" | "connecting" | "weaving" | "composing" | "breathing" | "shaping"
  const getOrbState = (): string => {
    switch (state) {
      case 'Listening':
        return 'listening';
      case 'Thinking': {
        const text = (transcript || '').toLowerCase();
        if (text.includes('apply') || text.includes('resume') || text.includes('write') || text.includes('draft') || text.includes('email') || text.includes('letter')) {
          return 'composing';
        }
        if (text.includes('search') || text.includes('find') || text.includes('job') || text.includes('screen') || text.includes('look')) {
          return 'searching';
        }
        if (text.includes('open') || text.includes('portfolio') || text.includes('connect') || text.includes('github') || text.includes('linkedin') || text.includes('propcast') || text.includes('uniml') || text.includes('control-d')) {
          return 'connecting';
        }
        if (text.includes('analyze') || text.includes('rag') || text.includes('context') || text.includes('project') || text.includes('history')) {
          return 'weaving';
        }
        if (text.includes('solve') || text.includes('code') || text.includes('calculate') || text.includes('error') || text.includes('debug')) {
          return 'solving';
        }
        return 'working';
      }
      case 'Responding':
        return 'shaping';
      default:
        return 'breathing';
    }
  };

  const orbState = getOrbState();

  return (
    <div className="w-full h-full flex justify-center items-start pt-0 select-none">
      <motion.div
        initial={{ width: 170, height: 38 }}
        animate={{ width, height }}
        transition={{ type: 'spring', damping: 28, stiffness: 360 }}
        className="rounded-b-[26px] rounded-t-none overflow-hidden shadow-[0_20px_60px_rgba(0,0,0,0.95)]"
      >
        <GlassSurface
          width="100%"
          height="100%"
          borderRadius={26}
          borderWidth={0.08}
          brightness={15}
          opacity={0.96}
          blur={12}
          displace={4}
          backgroundOpacity={0.98}
          distortionScale={-170}
          redOffset={4}
          greenOffset={12}
          blueOffset={24}
          className="notch-glass-bg"
          style={{
            backgroundColor: '#000000',
            borderTopLeftRadius: 0,
            borderTopRightRadius: 0,
            borderBottomLeftRadius: 26,
            borderBottomRightRadius: 26,
            border: '1px solid rgba(255, 255, 255, 0.14)',
            borderTop: 'none',
          }}
        >
          {/* Notch Header Row */}
          <div className={`w-full flex items-center justify-between px-4 transition-all duration-300 ${isExpanded ? 'pt-3 pb-1' : 'h-[38px]'}`}>
            {/* Left: ThinkingOrb from thinking-orbs */}
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="flex items-center justify-center flex-shrink-0">
                <LiquidOrb
                  state={state === 'Listening' || state === 'Thinking' ? 'thinking' : 'idle'}
                  size={isExpanded ? 52 : 22}
                />
              </div>
              
              <div className="flex flex-col text-left flex-1 min-w-0 pr-2">
                {!isExpanded ? (
                  <div className="flex items-center gap-2">
                    <span className="text-[14px] font-bold text-white tracking-wider">
                      ✦
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-white/[0.04] text-[10.5px] font-medium text-zinc-400 tracking-wide">
                      Hold Ctrl+Alt
                    </span>
                  </div>
                ) : (
                  <>
                    <span className="text-[13px] font-medium text-white tracking-tight truncate">
                      {state === 'Listening' && (transcript ? `"${transcript}"` : 'Listening...')}
                      {state === 'Thinking' && (transcript ? `Processing: "${transcript}"` : 'Thinking...')}
                      {state === 'Responding' && (lastActionText || 'Action Executed ✓')}
                    </span>
                    <span className="text-[11px] text-zinc-400 mt-0.5 flex items-center gap-1.5">
                      {state === 'Listening' && (
                        <span className="text-cyan-400 font-medium flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                          Listening to speech
                        </span>
                      )}
                      {state === 'Thinking' && (
                        <span className="text-indigo-400 font-medium flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                          {orbState === 'searching'
                            ? 'Searching & Inspecting...'
                            : orbState === 'connecting'
                            ? 'Connecting to route...'
                            : orbState === 'composing'
                            ? 'Composing resume & application...'
                            : orbState === 'weaving'
                            ? 'Weaving profile & RAG memory...'
                            : orbState === 'solving'
                            ? 'Solving intent...'
                            : 'Working on request...'}
                        </span>
                      )}
                      {state === 'Responding' && (
                        <span className="text-emerald-400 font-medium flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                          Complete
                        </span>
                      )}
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Right Minimal Status Dot */}
            {!isExpanded && (
              <div className="flex items-center gap-1.5 opacity-70 flex-shrink-0">
                <span className="w-1.5 h-1.5 rounded-full bg-zinc-600" />
                <span className="text-[11px] text-zinc-400 font-medium">Ready</span>
              </div>
            )}
          </div>

          {/* Live Audio Waveform when listening/thinking */}
          {isExpanded && (
            <div className="w-full px-4 pb-2">
              <Waveform />
            </div>
          )}
        </GlassSurface>
      </motion.div>
    </div>
  );
}
