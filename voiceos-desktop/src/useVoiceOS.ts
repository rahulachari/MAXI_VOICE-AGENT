import { create } from 'zustand';

export type AppState = 'Idle' | 'Listening' | 'Thinking' | 'Responding' | 'ActionExecuting';

interface VoiceOSStore {
  state: AppState;
  transcript: string;
  lastActionText: string;
  explanation: { summary: string; deep_dive: string; key_takeaways: string[] } | null;
  setState: (state: AppState) => void;
  setTranscript: (text: string) => void;
  setLastActionText: (text: string) => void;
  setExplanation: (explanation: VoiceOSStore['explanation']) => void;
}

export const useVoiceOS = create<VoiceOSStore>((set) => ({
  state: 'Idle',
  transcript: '',
  lastActionText: '',
  explanation: null,
  setState: (state) => set({ state }),
  setTranscript: (transcript) => set({ transcript }),
  setLastActionText: (lastActionText) => set({ lastActionText }),
  setExplanation: (explanation) => set({ explanation }),
}));
