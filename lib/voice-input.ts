export type VoiceLanguage = 'hi-IN' | 'en-IN' | 'en-US';
export type VoiceStatus = 'idle' | 'requesting' | 'starting' | 'listening' | 'stopping';
export interface VoiceState { status: VoiceStatus; error: string }

interface RecognitionResult {
  readonly isFinal: boolean;
  readonly length: number;
  readonly [index: number]: { readonly transcript: string };
}
export interface RecognitionEvent { readonly results: ArrayLike<RecognitionResult> }

/** Minimal native contract. A future backend STT adapter can implement this
 * lifecycle and emit cumulative result snapshots without changing the composer.
 * No fallback records or uploads audio until a provider is explicitly connected.
 */
export interface RecognitionEngine {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onresult: ((event: RecognitionEvent) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onspeechstart: (() => void) | null;
  onspeechend: (() => void) | null;
  onnomatch: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}
export interface VoiceEnvironment {
  secureContext: boolean;
  /** A backend adapter can consume this stream; the native adapter captures its own audio. */
  createRecognition?: (stream: MediaStream) => RecognitionEngine;
  requestMicrophone?: () => Promise<MediaStream>;
}
export interface VoiceCallbacks {
  onTranscript(text: string): void;
  onState(state: VoiceState): void;
}
export interface VoiceInputController {
  start(prefix: string, language: VoiceLanguage): Promise<void>;
  stop(): void;
  cancel(): void;
  dispose(): void;
}

/** Called only on the client. Feature detection also covers prefixed browsers. */
export function browserVoiceEnvironment(): VoiceEnvironment {
  const browser = window as Window & {
    SpeechRecognition?: new () => RecognitionEngine;
    webkitSpeechRecognition?: new () => RecognitionEngine;
  };
  const Recognition = browser.SpeechRecognition || browser.webkitSpeechRecognition;
  return {
    secureContext: window.isSecureContext,
    createRecognition: Recognition ? () => new Recognition() : undefined,
    requestMicrophone: navigator.mediaDevices?.getUserMedia
      ? () => navigator.mediaDevices.getUserMedia({ audio: true })
      : undefined,
  };
}

function errorMessage(code: string): string {
  switch (code) {
    case 'NotAllowedError': case 'SecurityError': case 'not-allowed': case 'service-not-allowed':
      return 'Microphone permission is required. Allow microphone access in your browser settings and try again.';
    case 'NotFoundError': case 'DevicesNotFoundError':
      return 'No microphone is available. Connect a microphone and try again.';
    case 'NotReadableError': case 'AbortError': case 'audio-capture':
      return 'Could not capture microphone audio. Check your microphone and close other apps using it.';
    case 'no-speech':
      return 'No speech detected. Please try again.';
    case 'network':
      return 'Voice recognition could not connect. Check your internet connection and try again.';
    case 'language-not-supported':
      return 'This voice language is not supported by your browser. Select another language and try again.';
    default:
      return 'Voice recognition could not start or was interrupted. Please try again.';
  }
}

function stopTracks(stream?: MediaStream) {
  stream?.getTracks().forEach((track) => track.stop());
}

type Timer = ReturnType<typeof setTimeout>;
interface Session {
  prefix: string;
  engine?: RecognitionEngine;
  stream?: MediaStream;
  stopping: boolean;
  heardText: boolean;
  speechEnded: boolean;
  startupTimer?: Timer;
  silenceTimer?: Timer;
  stopTimer?: Timer;
}

export function createVoiceInput(env: VoiceEnvironment, callbacks: VoiceCallbacks): VoiceInputController {
  let active: Session | null = null;
  let disposed = false;

  function publish(status: VoiceStatus, error = '') {
    if (!disposed) callbacks.onState({ status, error });
  }

  function release(session: Session, error = '', abort = false) {
    if (active !== session) return;
    active = null; // Invalidate callbacks before invoking browser methods.
    clearTimeout(session.startupTimer);
    clearTimeout(session.silenceTimer);
    clearTimeout(session.stopTimer);
    stopTracks(session.stream);
    session.stream = undefined;
    const engine = session.engine;
    if (engine) {
      engine.onstart = engine.onend = engine.onresult = engine.onerror = null;
      engine.onspeechstart = engine.onspeechend = engine.onnomatch = null;
      if (abort) {
        try { engine.abort(); } catch { /* Already stopped by the browser. */ }
      }
    }
    publish('idle', error);
  }

  function stop() {
    const session = active;
    if (!session || session.stopping) return;
    if (!session.engine) {
      // getUserMedia permission dialogs cannot be programmatically dismissed.
      // A late grant is immediately released by start's identity check.
      release(session);
      return;
    }
    session.stopping = true;
    clearTimeout(session.startupTimer);
    clearTimeout(session.silenceTimer);
    stopTracks(session.stream);
    session.stream = undefined;
    publish('stopping');
    // stop() allows a last final result. Bound buggy/missing onend events.
    session.stopTimer = setTimeout(() => release(session, '', true), 1500);
    try { session.engine.stop(); } catch { release(session, '', true); }
  }

  return {
    async start(prefix, language) {
      if (disposed || active) return;
      if (!env.secureContext) {
        publish('idle', 'Microphone access requires HTTPS or localhost.');
        return;
      }
      if (!env.createRecognition) {
        publish('idle', 'Voice recognition is not supported in this browser.');
        return;
      }
      if (!env.requestMicrophone) {
        publish('idle', 'Microphone access is unavailable in this browser.');
        return;
      }
      const session: Session = { prefix, stopping: false, heardText: false, speechEnded: false };
      active = session;
      publish('requesting');
      try {
        const stream = await env.requestMicrophone();
        if (disposed || active !== session) {
          stopTracks(stream);
          return;
        }
        session.stream = stream;
        const engine = env.createRecognition(stream);
        session.engine = engine;
        engine.lang = language;
        engine.continuous = true;
        engine.interimResults = true;
        engine.onstart = () => {
          if (active !== session || session.stopping) return;
          clearTimeout(session.startupTimer);
          publish('listening');
          session.silenceTimer = setTimeout(() => release(session, errorMessage('no-speech'), true), 15000);
        };
        engine.onresult = (event) => {
          if (active !== session) return;
          // The native result list is a cumulative snapshot. Rebuild its suffix
          // rather than appending revisions (interim entries may also disappear).
          const parts = Array.from(event.results, (result) => result[0]?.transcript.trim() || '');
          const spoken = parts.filter(Boolean).join(' ');
          if (spoken) {
            session.heardText = true;
            clearTimeout(session.silenceTimer);
            if (session.speechEnded && !session.stopping) session.silenceTimer = setTimeout(stop, 2000);
          }
          const separator = prefix && !/\s$/.test(prefix) && spoken ? ' ' : '';
          callbacks.onTranscript(prefix + separator + spoken);
        };
        engine.onspeechstart = () => {
          if (active === session && !session.stopping) {
            session.speechEnded = false;
            clearTimeout(session.silenceTimer);
          }
        };
        engine.onspeechend = () => {
          if (active !== session || session.stopping) return;
          session.speechEnded = true;
          clearTimeout(session.silenceTimer);
          session.silenceTimer = setTimeout(stop, 2000);
        };
        engine.onnomatch = () => release(session, errorMessage('no-speech'), true);
        engine.onerror = ({ error }) => {
          if (active !== session) return;
          release(session, error === 'aborted' ? '' : errorMessage(error), true);
        };
        engine.onend = () => release(session, !session.heardText && !session.stopping ? errorMessage('no-speech') : '');
        publish('starting');
        session.startupTimer = setTimeout(() => release(session, 'Voice recognition did not start. Please try again.', true), 10000);
        // Native recognition owns its audio capture; the explicit getUserMedia
        // stream above establishes real audio permission and is also cleaned up.
        engine.start();
      } catch (error) {
        const name = error instanceof Error ? error.name : '';
        release(session, errorMessage(name), true);
      }
    },
    stop,
    cancel() { if (active) release(active, '', true); },
    dispose() {
      disposed = true;
      if (active) release(active, '', true);
    },
  };
}
