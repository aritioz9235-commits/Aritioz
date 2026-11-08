import { afterEach, describe, expect, it, vi } from 'vitest';
import { browserVoiceEnvironment, createVoiceInput, type RecognitionEngine, type VoiceEnvironment, type VoiceState } from './voice-input';

function setup() {
  const startCall = vi.fn();
  const stopCall = vi.fn();
  const abortCall = vi.fn();
  const recognition: RecognitionEngine = {
    lang: '', continuous: false, interimResults: false,
    onstart: null, onend: null, onresult: null, onerror: null,
    onspeechstart: null, onspeechend: null, onnomatch: null,
    start: startCall, stop: stopCall, abort: abortCall,
  };
  const track = { stop: vi.fn() };
  const stream = { getTracks: () => [track] } as unknown as MediaStream;
  const env: VoiceEnvironment = {
    secureContext: true,
    createRecognition: vi.fn(() => recognition),
    requestMicrophone: vi.fn(async () => stream),
  };
  let state: VoiceState = { status: 'idle', error: '' };
  let text = '';
  const onTranscript = vi.fn((value: string) => { text = value; });
  const controller = createVoiceInput(env, { onTranscript, onState: (value) => { state = value; } });
  function result(...phrases: Array<[string, boolean]>) {
    recognition.onresult?.({ results: phrases.map(([transcript, isFinal]) => ({ 0: { transcript }, length: 1, isFinal })) });
  }
  return { startCall, stopCall, abortCall, recognition, env, track, stream, controller, result, onTranscript, state: () => state, text: () => text };
}

afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

describe('voice input lifecycle', () => {
  it.each(['hi-IN', 'en-IN', 'en-US'] as const)('requests audio and starts real recognition configured for %s', async (language) => {
    const f = setup();
    await f.controller.start('Typed', language);
    expect(f.env.requestMicrophone).toHaveBeenCalledOnce();
    expect(f.startCall).toHaveBeenCalledOnce();
    expect(f.recognition).toMatchObject({ lang: language, continuous: true, interimResults: true });
    expect(f.state().status).toBe('starting');
    f.recognition.onstart?.();
    expect(f.state().status).toBe('listening');
    f.controller.dispose();
  });

  it('replaces interim revisions, keeps all final segments and preserves typed text', async () => {
    const f = setup();
    await f.controller.start('Please explain:', 'hi-IN');
    f.result(['मुझे', false]);
    expect(f.text()).toBe('Please explain: मुझे');
    f.result(['मुझे झारखंड', false]);
    expect(f.text()).toBe('Please explain: मुझे झारखंड');
    f.result(['मुझे झारखंड', true], ['के बारे में', false]);
    f.result(['मुझे झारखंड', true], ['के बारे में बताओ', true]);
    f.result(['मुझे झारखंड', true], ['के बारे में बताओ', true]);
    expect(f.text()).toBe('Please explain: मुझे झारखंड के बारे में बताओ');
    f.recognition.onend?.();
    expect(f.text()).toBe('Please explain: मुझे झारखंड के बारे में बताओ');
    expect(f.track.stop).toHaveBeenCalledOnce();
    expect(f.state().status).toBe('idle');
  });

  it('handles interim removals without deleting the preexisting prefix', async () => {
    const f = setup();
    await f.controller.start('Typed  ', 'en-IN');
    f.result(['maybe', false]);
    f.result();
    expect(f.text()).toBe('Typed  ');
    f.controller.dispose();
  });

  it('stops on second click, accepts the last final result and releases audio', async () => {
    const f = setup();
    await f.controller.start('', 'en-US');
    f.recognition.onstart?.();
    f.result(['hello', false]);
    f.controller.stop();
    expect(f.stopCall).toHaveBeenCalledOnce();
    expect(f.track.stop).toHaveBeenCalledOnce();
    expect(f.state().status).toBe('stopping');
    f.result(['hello world', true]);
    f.recognition.onend?.();
    expect(f.text()).toBe('hello world');
    expect(f.state()).toEqual({ status: 'idle', error: '' });
  });

  it('does not launch a second session while permission or stop is pending', async () => {
    const f = setup();
    const first = f.controller.start('', 'hi-IN');
    await f.controller.start('', 'en-US');
    await first;
    f.controller.stop();
    await f.controller.start('', 'en-US');
    expect(f.env.requestMicrophone).toHaveBeenCalledOnce();
    expect(f.startCall).toHaveBeenCalledOnce();
    f.controller.dispose();
  });

  it('stops a permission stream that arrives after cancellation', async () => {
    const f = setup();
    let grant!: (stream: MediaStream) => void;
    f.env.requestMicrophone = () => new Promise((resolve) => { grant = resolve; });
    const pending = f.controller.start('', 'hi-IN');
    f.controller.stop();
    grant(f.stream);
    await pending;
    expect(f.track.stop).toHaveBeenCalledOnce();
    expect(f.startCall).not.toHaveBeenCalled();
    expect(f.state().status).toBe('idle');
  });

  it('ignores late events after editing, sending or unmounting', async () => {
    const f = setup();
    await f.controller.start('Before', 'en-IN');
    f.result(['voice', false]);
    const lateResult = f.recognition.onresult;
    f.controller.cancel();
    lateResult?.({ results: [{ 0: { transcript: 'stale' }, length: 1, isFinal: true }] });
    expect(f.text()).toBe('Before voice');
    expect(f.abortCall).toHaveBeenCalledOnce();
    expect(f.track.stop).toHaveBeenCalledOnce();
    expect(f.recognition.onresult).toBeNull();
    f.controller.dispose();
    await f.controller.start('', 'hi-IN');
    expect(f.startCall).toHaveBeenCalledOnce();
  });

  it('cleans up a permission grant after component disposal', async () => {
    const f = setup();
    let grant!: (stream: MediaStream) => void;
    f.env.requestMicrophone = () => new Promise((resolve) => { grant = resolve; });
    const pending = f.controller.start('', 'hi-IN');
    f.controller.dispose();
    grant(f.stream);
    await pending;
    expect(f.track.stop).toHaveBeenCalledOnce();
    expect(f.startCall).not.toHaveBeenCalled();
  });

  it('retains text on unexpected end and allows another session', async () => {
    const f = setup();
    await f.controller.start('First', 'en-US');
    f.result(['second', true]);
    f.recognition.onend?.();
    await f.controller.start(f.text(), 'en-IN');
    f.result(['third', true]);
    expect(f.text()).toBe('First second third');
    f.controller.dispose();
  });

  it('aborts if the browser fails to end after stop', async () => {
    vi.useFakeTimers();
    const f = setup();
    await f.controller.start('', 'hi-IN');
    f.controller.stop();
    vi.advanceTimersByTime(2000);
    expect(f.abortCall).toHaveBeenCalledOnce();
    expect(f.state().status).toBe('idle');
    expect(f.track.stop).toHaveBeenCalledOnce();
  });

  it('stops after a speech pause, but allows speech to resume before the deadline', async () => {
    vi.useFakeTimers();
    const f = setup();
    await f.controller.start('', 'hi-IN');
    f.recognition.onstart?.();
    f.result(['नमस्ते', true]);
    f.recognition.onspeechend?.();
    vi.advanceTimersByTime(1000);
    f.recognition.onspeechstart?.();
    vi.advanceTimersByTime(2000);
    expect(f.stopCall).not.toHaveBeenCalled();
    f.recognition.onspeechend?.();
    vi.advanceTimersByTime(2000);
    expect(f.stopCall).toHaveBeenCalledOnce();
    f.controller.dispose();
  });

  it('still stops when the final transcript arrives after speechend', async () => {
    vi.useFakeTimers();
    const f = setup();
    await f.controller.start('', 'hi-IN');
    f.recognition.onstart?.();
    f.recognition.onspeechend?.();
    f.result(['नमस्ते', true]);
    vi.advanceTimersByTime(2000);
    expect(f.stopCall).toHaveBeenCalledOnce();
    expect(f.text()).toBe('नमस्ते');
    f.controller.dispose();
  });

  it('reports no speech and shuts down when no speech arrives', async () => {
    vi.useFakeTimers();
    const f = setup();
    await f.controller.start('', 'hi-IN');
    f.recognition.onstart?.();
    vi.advanceTimersByTime(15000);
    expect(f.state().error).toMatch(/No speech detected/);
    expect(f.track.stop).toHaveBeenCalledOnce();
    expect(f.abortCall).toHaveBeenCalledOnce();
  });
});

describe('voice errors', () => {
  it.each([
    ['NotAllowedError', /permission/i], ['NotFoundError', /No microphone/i],
    ['NotReadableError', /audio|microphone/i], ['SecurityError', /permission/i],
  ])('handles permission/capture error %s without starting recognition', async (name, message) => {
    const f = setup();
    f.env.requestMicrophone = async () => { throw new DOMException('private detail', name); };
    await f.controller.start('', 'hi-IN');
    expect(f.state().error).toMatch(message);
    expect(f.state().error).not.toContain('private detail');
    expect(f.state().status).toBe('idle');
    expect(f.startCall).not.toHaveBeenCalled();
  });

  it.each([
    ['not-allowed', /permission/i], ['service-not-allowed', /permission/i],
    ['no-speech', /No speech detected/], ['network', /network|connection/i],
    ['audio-capture', /audio|microphone/i], ['language-not-supported', /language/i],
  ])('handles recognition error %s and releases audio', async (error, message) => {
    const f = setup();
    await f.controller.start('Keep me', 'hi-IN');
    f.recognition.onerror?.({ error });
    expect(f.state().error).toMatch(message);
    expect(f.state().status).toBe('idle');
    expect(f.track.stop).toHaveBeenCalledOnce();
    expect(f.abortCall).toHaveBeenCalledOnce();
  });

  it('does not request permission when recognition is unsupported', async () => {
    const f = setup();
    f.env.createRecognition = undefined;
    await f.controller.start('', 'hi-IN');
    expect(f.state().error).toBe('Voice recognition is not supported in this browser.');
    expect(f.env.requestMicrophone).not.toHaveBeenCalled();
  });

  it('rejects insecure contexts without requesting microphone access', async () => {
    const f = setup();
    f.env.secureContext = false;
    await f.controller.start('', 'hi-IN');
    expect(f.state().error).toMatch(/HTTPS|localhost/);
    expect(f.env.requestMicrophone).not.toHaveBeenCalled();
  });

  it('reports unavailable microphone APIs', async () => {
    const f = setup();
    f.env.requestMicrophone = undefined;
    await f.controller.start('', 'hi-IN');
    expect(f.state().error).toMatch(/Microphone access is unavailable/);
    expect(f.startCall).not.toHaveBeenCalled();
  });

  it('releases audio when the browser never begins recognition', async () => {
    vi.useFakeTimers();
    const f = setup();
    await f.controller.start('', 'hi-IN');
    vi.advanceTimersByTime(10000);
    expect(f.state().error).toMatch(/did not start/);
    expect(f.track.stop).toHaveBeenCalledOnce();
    expect(f.abortCall).toHaveBeenCalledOnce();
  });

  it('retains the displayed transcript if stop throws', async () => {
    const f = setup();
    await f.controller.start('Typed', 'en-IN');
    f.result(['spoken', true]);
    f.recognition.stop = () => { throw new Error('already stopped'); };
    f.controller.stop();
    expect(f.state().status).toBe('idle');
    expect(f.text()).toBe('Typed spoken');
    expect(f.track.stop).toHaveBeenCalledOnce();
    expect(f.abortCall).toHaveBeenCalledOnce();
  });

  it('cleans up if recognition.start throws', async () => {
    const f = setup();
    f.recognition.start = () => { throw new Error('private detail'); };
    await f.controller.start('', 'en-US');
    expect(f.state().status).toBe('idle');
    expect(f.state().error).not.toContain('private detail');
    expect(f.state().error).toMatch(/start/i);
    expect(f.track.stop).toHaveBeenCalledOnce();
  });
});


describe('browser audio adapter', () => {
  it.each(['SpeechRecognition', 'webkitSpeechRecognition'])('detects %s and requests audio only', async (key) => {
    const f = setup();
    const getUserMedia = vi.fn(async () => f.stream);
    vi.stubGlobal('window', { isSecureContext: true, [key]: class { constructor() { return f.recognition; } } });
    vi.stubGlobal('navigator', { mediaDevices: { getUserMedia } });
    const env = browserVoiceEnvironment();
    expect(env.secureContext).toBe(true);
    expect(env.createRecognition?.(f.stream)).toBe(f.recognition);
    await env.requestMicrophone?.();
    expect(getUserMedia).toHaveBeenCalledWith({ audio: true });
  });

  it('prefers standard recognition over the legacy prefixed API', () => {
    const f = setup();
    vi.stubGlobal('window', {
      isSecureContext: true,
      SpeechRecognition: class { constructor() { return f.recognition; } },
      webkitSpeechRecognition: class { constructor() { throw new Error('Must use standard API'); } },
    });
    vi.stubGlobal('navigator', {});
    expect(browserVoiceEnvironment().createRecognition?.(f.stream)).toBe(f.recognition);
  });

  it('detects missing browser APIs without throwing', () => {
    vi.stubGlobal('window', { isSecureContext: false });
    vi.stubGlobal('navigator', {});
    expect(browserVoiceEnvironment()).toEqual({
      secureContext: false, createRecognition: undefined, requestMicrophone: undefined,
    });
  });
});
