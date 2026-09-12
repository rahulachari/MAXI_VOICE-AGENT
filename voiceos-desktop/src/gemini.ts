import { invoke } from '@tauri-apps/api/core';

export interface CommandResult {
  spoken_response: string;
  action: 'open_url' | 'search_web' | 'launch_app' | 'none';
  target: string;
}

let cachedApiKey: string | null = null;

async function getApiKey(): Promise<string> {
  if (cachedApiKey) return cachedApiKey;
  try {
    const key = await invoke<string>('get_gemini_key');
    if (key && key.trim()) {
      cachedApiKey = key.trim();
      return cachedApiKey;
    }
  } catch (e) {
    console.error('Failed to get API key from backend:', e);
  }
  return '';
}

export async function processCommandWithGemini(userPrompt: string): Promise<CommandResult> {
  const query = userPrompt.trim();
  if (!query) {
    return {
      spoken_response: "I didn't catch that. Please hold Ctrl+Alt to speak.",
      action: 'none',
      target: ''
    };
  }

  const apiKey = await getApiKey();
  const models = ['gemini-3.6-flash', 'gemini-3.7-flash', 'gemini-3.8-flash', 'gemini-flash-latest'];

  const systemInstruction = `You are JARVIS VoiceOS, an elite AI desktop companion.
Analyze the user's voice command and output ONLY valid JSON in this schema:
{
  "spoken_response": "1 warm, natural, concise sentence for out-loud speech.",
  "action": "open_url" | "search_web" | "launch_app" | "none",
  "target": "full url, search query, or application executable name"
}
Examples:
- "open gmail": {"spoken_response": "Opening your Gmail inbox.", "action": "open_url", "target": "https://mail.google.com"}
- "open youtube": {"spoken_response": "Opening YouTube for you now, Sir.", "action": "open_url", "target": "https://www.youtube.com"}
- "open linkedin": {"spoken_response": "Opening your LinkedIn profile.", "action": "open_url", "target": "https://www.linkedin.com"}
- "open github": {"spoken_response": "Opening GitHub.", "action": "open_url", "target": "https://www.github.com"}
- "search for quantum computing": {"spoken_response": "Searching Google for quantum computing.", "action": "search_web", "target": "quantum computing"}
- "open notepad": {"spoken_response": "Launching Notepad.", "action": "launch_app", "target": "notepad"}
- "open calculator": {"spoken_response": "Opening Calculator.", "action": "launch_app", "target": "calc"}
`;

  if (apiKey) {
    for (const model of models) {
      try {
        const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
        const payload = {
          contents: [
            {
              parts: [
                { text: `${systemInstruction}\n\nUser command: "${query}"` }
              ]
            }
          ],
          generationConfig: {
            response_mime_type: "application/json"
          }
        };

        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          const data = await res.json();
          const textResponse = data.candidates?.[0]?.content?.parts?.[0]?.text;
          if (textResponse) {
            const cleanJson = textResponse.replace(/```json/g, '').replace(/```/g, '').trim();
            const parsed = JSON.parse(cleanJson) as CommandResult;
            if (parsed.spoken_response) {
              return parsed;
            }
          }
        }
      } catch (err) {
        console.warn(`Model ${model} request error:`, err);
      }
    }
  }

  // Fast offline/fallback rule-based intent engine
  const lower = query.toLowerCase();
  if (lower.includes('gmail') || lower.includes('google mail')) {
    return { spoken_response: "Opening your Gmail inbox.", action: "open_url", target: "https://mail.google.com" };
  } else if (lower.includes('youtube')) {
    return { spoken_response: "Opening YouTube.", action: "open_url", target: "https://www.youtube.com" };
  } else if (lower.includes('linkedin')) {
    return { spoken_response: "Opening LinkedIn.", action: "open_url", target: "https://www.linkedin.com" };
  } else if (lower.includes('github')) {
    return { spoken_response: "Opening GitHub.", action: "open_url", target: "https://www.github.com" };
  } else if (lower.includes('notepad')) {
    return { spoken_response: "Launching Notepad.", action: "launch_app", target: "notepad" };
  } else if (lower.includes('calc') || lower.includes('calculator')) {
    return { spoken_response: "Opening Calculator.", action: "launch_app", target: "calc" };
  } else if (lower.includes('calendar')) {
    return { spoken_response: "Opening Google Calendar.", action: "open_url", target: "https://calendar.google.com" };
  } else if (lower.includes('apply for this') || lower.includes('apply for the job') || lower.includes('apply job')) {
    return { spoken_response: "Analyzing job posting on screen, matching resume projects, and generating your application package.", action: "none", target: "" };
  } else if (lower.startsWith('search ') || lower.startsWith('google ')) {
    const q = query.replace(/^(search\s+for|search|google)\s+/i, '');
    return { spoken_response: `Searching Google for ${q}.`, action: "search_web", target: q };
  } else if (lower.startsWith('open ')) {
    const app = query.replace(/^open\s+/i, '');
    return { spoken_response: `Opening ${app}.`, action: "search_web", target: `${app} official site` };
  }

  return {
    spoken_response: `Processing: ${query}`,
    action: "search_web",
    target: query
  };
}

export function speakResponse(text: string) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.05;
  utterance.pitch = 1.0;
  
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v => v.name.includes('Natural') || v.name.includes('Guy') || v.name.includes('David') || v.lang.startsWith('en'));
  if (preferred) {
    utterance.voice = preferred;
  }
  
  window.speechSynthesis.speak(utterance);
}
