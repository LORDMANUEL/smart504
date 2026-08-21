import { useCallback, useRef, useState } from 'react';
import { X } from 'lucide-react';

type PromptOptions = {
  label?: string;
  initialValue?: string;
  inputType?: 'text' | 'password' | 'number' | 'email';
  required?: boolean;
};

type PromptState = PromptOptions & { title: string };

export function useActionPrompt() {
  const [state, setState] = useState<PromptState | null>(null);
  const [value, setValue] = useState('');
  const resolver = useRef<((result: string | null) => void) | null>(null);

  const ask = useCallback((title: string, options: PromptOptions = {}) => {
    resolver.current?.(null);
    setValue(options.initialValue ?? '');
    setState({ title, inputType: 'text', required: true, ...options });
    return new Promise<string | null>((resolve) => { resolver.current = resolve; });
  }, []);

  const close = useCallback((result: string | null) => {
    resolver.current?.(result);
    resolver.current = null;
    setState(null);
  }, []);

  const dialog = state ? <div className="action-prompt-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) close(null); }}>
    <form className="action-prompt" role="dialog" aria-modal="true" aria-labelledby="action-prompt-title" onSubmit={(event) => { event.preventDefault(); if (!state.required || value.trim()) close(value.trim()); }}>
      <header><div><span>Confirmación operativa</span><h2 id="action-prompt-title">{state.title}</h2></div><button type="button" aria-label="Cancelar" onClick={() => close(null)}><X /></button></header>
      <label>{state.label ?? 'Detalle'}<input autoFocus type={state.inputType} autoComplete={state.inputType === 'password' ? 'off' : undefined} required={state.required} value={value} onChange={(event) => setValue(event.target.value)} /></label>
      <footer><button type="button" onClick={() => close(null)}>Cancelar</button><button className="role-primary" disabled={state.required && !value.trim()}>Continuar</button></footer>
    </form>
  </div> : null;

  return { ask, dialog };
}
