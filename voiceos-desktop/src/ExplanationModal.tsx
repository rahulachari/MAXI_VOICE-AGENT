import { motion } from 'framer-motion';
import { useVoiceOS } from './useVoiceOS';

export default function ExplanationModal() {
  const { explanation, setExplanation, setState } = useVoiceOS();

  if (!explanation) return null;

  return (
    <motion.div 
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      className="action-card p-5 text-sm text-zinc-200 flex flex-col gap-3.5 mt-2"
    >
      {/* Header */}
      <div className="flex items-center justify-between pb-2.5 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <span className="w-6 h-6 rounded-lg bg-blue-600/30 border border-blue-400/40 flex items-center justify-center text-xs text-blue-300">
            ⚡
          </span>
          <span className="font-semibold text-white text-[13.5px] tracking-tight">
            VoiceOS Agent • Action Preview
          </span>
        </div>
        <button
          onClick={() => setExplanation(null)}
          className="text-zinc-500 hover:text-white transition-colors text-xs px-2 py-0.5 rounded"
        >
          ✕
        </button>
      </div>

      {/* Body Summary & Deep Dive */}
      <div>
        <h3 className="font-medium text-white text-[14px] leading-snug mb-1">
          {explanation.summary}
        </h3>
        <p className="text-[12.5px] text-zinc-400 leading-relaxed">
          {explanation.deep_dive}
        </p>
      </div>

      {/* Structured Key Takeaways / Field Tags */}
      {explanation.key_takeaways && explanation.key_takeaways.length > 0 && (
        <div className="flex flex-wrap gap-1.5 py-1">
          {explanation.key_takeaways.map((point, idx) => (
            <span
              key={idx}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/[0.07] border border-white/10 text-[11.5px] text-zinc-300"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              {point}
            </span>
          ))}
        </div>
      )}

      {/* Action Confirmation Footer */}
      <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-white/10">
        <button
          onClick={() => {
            setExplanation(null);
            setState('Idle');
          }}
          className="btn-secondary px-4 py-1.5 rounded-full text-xs font-medium cursor-pointer"
        >
          Dismiss
        </button>
        <button
          onClick={() => {
            setExplanation(null);
            setState('Responding');
            setTimeout(() => setState('Idle'), 2000);
          }}
          className="btn-primary px-5 py-1.5 rounded-full text-xs font-medium cursor-pointer"
        >
          Execute Action
        </button>
      </div>
    </motion.div>
  );
}
