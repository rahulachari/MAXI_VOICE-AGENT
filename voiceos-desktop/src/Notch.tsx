import { motion } from 'framer-motion';
import { useVoiceOS } from './useVoiceOS';
import Waveform from './Waveform';

export default function Notch() {
  const { state, transcript, lastActionText } = useVoiceOS();

  const isExpanded = state === 'Listening' || state === 'Thinking' || state === 'Responding';
  const width = isExpanded ? 500 : 340;
  const height = isExpanded ? 96 : 46;

  return (
    <div className="w-full h-full flex justify-center items-start pt-1.5 select-none">
      <motion.div
        initial={{ width: 340, height: 46 }}
        animate={{ width, height }}
        transition={{ type: 'spring', damping: 28, stiffness: 360 }}
        className="voiceos-notch-container flex flex-col"
      >
        {/* Notch Header Row */}
        <div className={`w-full flex items-center justify-between px-5 transition-all duration-300 ${isExpanded ? 'pt-3.5 pb-1' : 'h-[46px]'}`}>
          {/* Left: 3D VoiceOS Gradient Orb */}
          <div className="flex items-center gap-3.5 flex-1 min-w-0">
            <div className={isExpanded ? 'voiceos-orb-active' : 'voiceos-orb'} />
            
            <div className="flex flex-col text-left flex-1 min-w-0 pr-2">
              {!isExpanded ? (
                <div className="flex items-center gap-2.5">
                  <span className="text-[13px] font-semibold text-white tracking-tight">
                    JARVIS <span className="text-zinc-400 font-normal">VoiceOS</span>
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-white/[0.07] border border-white/10 text-[10px] font-medium text-zinc-400 tracking-wide">
                    ⚡ Hold Ctrl+Alt
                  </span>
                </div>
              ) : (
                <>
                  <span className="text-[13px] font-semibold text-white tracking-tight truncate">
                    {state === 'Listening' && (transcript ? `"${transcript}"` : 'Listening to your command...')}
                    {state === 'Thinking' && 'Gemini AI reasoning & analyzing intent...'}
                    {state === 'Responding' && (lastActionText || 'Executing Desktop Action...')}
                  </span>
                  <span className="text-[11px] text-zinc-400 mt-0.5 flex items-center gap-1.5">
                    {state === 'Listening' && (
                      <span className="inline-flex items-center gap-1 text-cyan-400 font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                        Release Ctrl+Alt to Execute
                      </span>
                    )}
                    {state === 'Thinking' && (
                      <span className="inline-flex items-center gap-1 text-indigo-400 font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                        Gemini Flash Multimodal
                      </span>
                    )}
                    {state === 'Responding' && (
                      <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        Action Complete • Closing...
                      </span>
                    )}
                  </span>
                </>
              )}
            </div>
          </div>

          {/* Right Status Indicator */}
          {!isExpanded && (
            <div className="flex items-center gap-1.5 opacity-80 flex-shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
              <span className="text-[11px] text-zinc-400 font-medium">Ready</span>
            </div>
          )}
        </div>

        {/* Live Audio Waveform when listening/thinking */}
        {isExpanded && (
          <div className="w-full px-5 pb-2">
            <Waveform />
          </div>
        )}
      </motion.div>
    </div>
  );
}
