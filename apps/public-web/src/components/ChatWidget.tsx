import { FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from 'react';
import { Bot, CalendarCheck, ExternalLink, MessageCircle, PackageSearch, Send, ShieldCheck, X } from 'lucide-react';

import { createChatSession, createLead, getChatHistory, sendChatMessage } from '../lib/api';
import type { ChatMessage, ChatSession } from '../types';

const STORAGE_KEY = 'smartdiag504-public-chat-session';
const DEFAULT_PROMPTS = [
  '¿Cómo reservo un diagnóstico?',
  'Necesito buscar un repuesto',
  '¿Qué servicios ofrecen?',
];

const WHATSAPP_URL = (import.meta.env.VITE_WHATSAPP_URL ?? '').trim();

function newMessageId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return `web-${crypto.randomUUID()}`;
  return `web-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function loadStoredSession(): ChatSession | null {
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const value = JSON.parse(raw) as ChatSession;
    if (!value.session_id || !value.session_token || Date.parse(value.expires_at) <= Date.now()) {
      window.sessionStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return value;
  } catch {
    window.sessionStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

function displayTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return new Intl.DateTimeFormat('es-HN', { hour: '2-digit', minute: '2-digit' }).format(date);
}

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [leadOpen, setLeadOpen] = useState(false);
  const [leadSent, setLeadSent] = useState('');
  const messageEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!open || session || loading) return;
    let active = true;
    setLoading(true);
    setError('');
    const stored = loadStoredSession();
    const start = stored
      ? getChatHistory(stored).then((history) => ({ session: stored, messages: history.messages }))
      : createChatSession().then((created) => ({
          session: created,
          messages: [{
            id: `welcome-${created.session_id}`,
            role: 'assistant' as const,
            content: created.welcome_message,
            created_at: new Date().toISOString(),
            mode: 'welcome',
          }],
        }));

    start.then((result) => {
      if (!active) return;
      setSession(result.session);
      setMessages(result.messages);
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(result.session));
    }).catch(() => {
      if (!active) return;
      window.sessionStorage.removeItem(STORAGE_KEY);
      setError('El asistente no está disponible en este momento. Puede reservar o escribir por WhatsApp.');
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [open, session]);

  useEffect(() => {
    if (!open) return;
    messageEndRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'end' });
  }, [messages, sending, open]);

  useEffect(() => {
    if (open && session && !loading) inputRef.current?.focus();
  }, [open, session, loading]);

  const quickPrompts = useMemo(
    () => session?.quick_prompts?.length ? session.quick_prompts : DEFAULT_PROMPTS,
    [session],
  );

  async function submitMessage(message: string) {
    const clean = message.trim();
    if (!clean || !session || sending) return;
    setError('');
    setSending(true);
    setInput('');
    try {
      const reply = await sendChatMessage(session, clean, newMessageId());
      setMessages((current) => [...current, reply.user_message, {
        ...reply.assistant_message,
        suggested_actions: reply.suggested_actions,
      }]);
    } catch (requestError) {
      setInput(clean);
      setError(requestError instanceof Error ? requestError.message : 'No fue posible enviar el mensaje.');
    } finally {
      setSending(false);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitMessage(input);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void submitMessage(input);
    }
  }

  function actionFor(code: string) {
    if (code === 'BOOK_SERVICE') window.location.hash = 'reservar';
    if (code === 'SEARCH_PARTS') window.location.hash = 'repuestos';
    if (code === 'CONTACT_WHATSAPP') {
      if (/^https:\/\//i.test(WHATSAPP_URL)) {
        window.open(WHATSAPP_URL, '_blank', 'noopener,noreferrer');
      } else {
        window.location.hash = 'reservar';
        setError('El enlace de WhatsApp aún no está configurado. Use el formulario de reserva.');
      }
    }
  }

  const lastActions = [...messages].reverse().find((message) => message.role === 'assistant')?.suggested_actions ?? [];

  async function submitLead(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    try {
      const created = await createLead({
        full_name: String(data.get('full_name') || ''),
        phone: String(data.get('phone') || ''),
        email: String(data.get('email') || ''),
        vehicle_summary: String(data.get('vehicle_summary') || ''),
        interest: String(data.get('interest') || input || 'Solicita atención de un asesor'),
        chat_session_id: session?.session_id,
      });
      setLeadSent(created.number); setLeadOpen(false);
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'No se pudo solicitar asesor.'); }
  }

  return (
    <aside className={open ? 'chat-widget chat-widget--open' : 'chat-widget'} aria-label="Asistente SmartDiag504">
      {open && (
        <section className="chat-panel" role="dialog" aria-modal="false" aria-labelledby="chat-title">
          <header className="chat-panel__header">
            <div className="chat-panel__identity">
              <span><Bot size={21} aria-hidden="true" /></span>
              <div><strong id="chat-title">Asistente SmartDiag504</strong><small><i />Orientación, reservas y repuestos</small></div>
            </div>
            <button type="button" aria-label="Cerrar asistente" onClick={() => setOpen(false)}><X size={18} /></button>
          </header>

          <div className="chat-panel__messages" aria-live="polite" aria-busy={loading || sending}>
            {loading && <p className="chat-loading">Conectando con SmartDiag504…</p>}
            {messages.map((message) => (
              <article className={`chat-message chat-message--${message.role}`} key={message.id}>
                <p>{message.content}</p><time dateTime={message.created_at}>{displayTime(message.created_at)}</time>
              </article>
            ))}
            {sending && <div className="chat-typing" aria-label="El asistente está escribiendo"><span /><span /><span /></div>}
            <div ref={messageEndRef} />
          </div>

          {messages.length <= 1 && !loading && (
            <div className="chat-quick-actions" aria-label="Preguntas rápidas">
              {quickPrompts.slice(0, 4).map((prompt) => (
                <button type="button" key={prompt} onClick={() => void submitMessage(prompt)}>
                  {prompt.toLocaleLowerCase().includes('repuesto') ? <PackageSearch size={13} /> : <MessageCircle size={13} />}
                  {prompt}
                </button>
              ))}
            </div>
          )}

          {lastActions.length > 0 && (
            <div className="chat-action-bar">
              {lastActions.includes('BOOK_SERVICE') && <button type="button" onClick={() => actionFor('BOOK_SERVICE')}><CalendarCheck size={14} /> Reservar</button>}
              {lastActions.includes('SEARCH_PARTS') && <button type="button" onClick={() => actionFor('SEARCH_PARTS')}><PackageSearch size={14} /> Repuestos</button>}
              {lastActions.includes('CONTACT_WHATSAPP') && <button type="button" onClick={() => actionFor('CONTACT_WHATSAPP')}><ExternalLink size={14} /> WhatsApp</button>}
            </div>
          )}
          <div className="chat-advisor"><button type="button" onClick={() => setLeadOpen((value) => !value)}><MessageCircle size={14} /> Quiero que me atienda un asesor</button>{leadSent && <strong>Solicitud {leadSent} recibida. María, asesora del taller, dará seguimiento.</strong>}</div>
          {leadOpen && <form className="chat-lead-form" onSubmit={submitLead}><input name="full_name" required minLength={2} placeholder="Nombre" /><input name="phone" required minLength={7} placeholder="Teléfono / WhatsApp" /><input name="email" type="email" placeholder="Correo (opcional)" /><input name="vehicle_summary" placeholder="Marca, modelo y año" /><textarea name="interest" required minLength={3} placeholder="¿Qué necesita?" defaultValue={input} /><button type="submit">Enviar a un asesor</button></form>}

          {error && <p className="chat-error" role="alert">{error}</p>}
          <form className="chat-composer" onSubmit={onSubmit}>
            <label className="sr-only" htmlFor="smartdiag-chat-input">Escriba su consulta</label>
            <textarea
              id="smartdiag-chat-input"
              ref={inputRef}
              aria-label="Escriba su consulta"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Escriba su consulta…"
              maxLength={2000}
              disabled={!session || loading || sending}
            />
            <button type="submit" aria-label="Enviar mensaje" disabled={!session || !input.trim() || loading || sending}><Send size={18} /></button>
          </form>
          <footer className="chat-panel__footer"><ShieldCheck size={12} /><span>{session?.privacy_notice ?? 'No sustituye una inspección técnica ni confirma compatibilidad sin VIN.'}</span></footer>
        </section>
      )}
      <button
        className="chat-launcher"
        type="button"
        aria-label={open ? 'Cerrar asistente' : 'Abrir asistente SmartDiag504'}
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        {open ? <X size={20} /> : <MessageCircle size={21} />}<span>{open ? 'Cerrar' : '¿Necesita ayuda?'}</span>
      </button>
    </aside>
  );
}
