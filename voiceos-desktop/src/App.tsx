import { useEffect, useRef } from 'react';
import { listen } from '@tauri-apps/api/event';
import { invoke } from '@tauri-apps/api/core';
import Notch from './Notch';
import { useVoiceOS } from './useVoiceOS';
import { processCommandWithGemini, speakResponse } from './gemini';

function App() {
  const { setState, setTranscript, setLastActionText } = useVoiceOS();
  const transcriptRef = useRef<string>('');
  const recognitionRef = useRef<any>(null);
  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // Setup Speech Recognition if available in the browser/Webview2
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onresult = (event: any) => {
          let current = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            current += event.results[i][0].transcript;
          }
          if (current.trim()) {
            transcriptRef.current = current.trim();
            setTranscript(current.trim());
          }
        };

        recognition.onerror = (err: any) => {
          console.warn('SpeechRecognition error:', err);
        };

        recognitionRef.current = recognition;
      } catch (e) {
        console.warn('Could not initialize SpeechRecognition:', e);
      }
    }

    const unlisten = listen<{ action: string }>('shortcut-triggered', async (event) => {
      const action = event.payload?.action;

      if (action === 'down') {
        if (hideTimerRef.current) {
          clearTimeout(hideTimerRef.current);
          hideTimerRef.current = null;
        }

        // Show window immediately
        await invoke('show_notch').catch(() => {});
        transcriptRef.current = '';
        setTranscript('');
        setState('Listening');

        if (recognitionRef.current) {
          try {
            recognitionRef.current.start();
          } catch {
            // Already started
          }
        }
      } else if (action === 'up') {
        if (recognitionRef.current) {
          try {
            recognitionRef.current.stop();
          } catch {
            // Ignore
          }
        }

        setState('Thinking');

        // Small delay to let final speech tokens settle
        setTimeout(async () => {
          const userQuery = transcriptRef.current.trim();
          if (!userQuery) {
            setState('Responding');
            setLastActionText("I didn't hear a command. Hold Ctrl+Alt to speak.");
            hideTimerRef.current = setTimeout(async () => {
              setState('Idle');
              await invoke('hide_notch').catch(() => {});
            }, 1800);
            return;
          }
          setTranscript(userQuery);

          try {
            // Call Gemini with the user query
            const result = await processCommandWithGemini(userQuery);
            setLastActionText(result.spoken_response);

            // Execute desktop action (open URL, launch app, search web)
            if (result.action !== 'none' && result.target) {
              await invoke('execute_action', {
                action: result.action,
                target: result.target
              }).catch(err => console.error('execute_action error:', err));
            }

            // Speak out loud confirmation
            speakResponse(result.spoken_response);
            setState('Responding');

            // After completing the task, the notch disappears!
            hideTimerRef.current = setTimeout(async () => {
              setState('Idle');
              await invoke('hide_notch').catch(() => {});
            }, 2600);
          } catch (e) {
            console.error('Command processing error:', e);
            setState('Idle');
            await invoke('hide_notch').catch(() => {});
          }
        }, 400);
      }
    });

    return () => {
      unlisten.then(f => f());
      if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    };
  }, [setState, setTranscript, setLastActionText]);

  return <Notch />;
}

export default App;
