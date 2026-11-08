'use client';

import { useEffect, useRef, useState } from 'react';
import {
  browserVoiceEnvironment, createVoiceInput,
  type VoiceInputController, type VoiceLanguage, type VoiceState,
} from '@/lib/voice-input';

export function useVoiceInput(onTranscript: (text: string) => void) {
  const [state, setState] = useState<VoiceState>({ status: 'idle', error: '' });
  const [language, setLanguage] = useState<VoiceLanguage>('hi-IN');
  const [used, setUsed] = useState(false);
  const controller = useRef<VoiceInputController | null>(null);

  useEffect(() => {
    const voice = createVoiceInput(browserVoiceEnvironment(), { onTranscript, onState: setState });
    controller.current = voice;
    const stopWhenHidden = () => { if (document.hidden) voice.cancel(); };
    const stopOnPageExit = () => voice.cancel();
    document.addEventListener('visibilitychange', stopWhenHidden);
    window.addEventListener('pagehide', stopOnPageExit);
    return () => {
      document.removeEventListener('visibilitychange', stopWhenHidden);
      window.removeEventListener('pagehide', stopOnPageExit);
      voice.dispose();
      controller.current = null;
    };
  }, [onTranscript]);

  const active = state.status !== 'idle';
  return {
    ...state, active, language, used,
    setLanguage,
    toggle(prefix: string) {
      setUsed(true);
      if (active) controller.current?.stop();
      else void controller.current?.start(prefix, language);
    },
    cancel() { controller.current?.cancel(); },
  };
}
