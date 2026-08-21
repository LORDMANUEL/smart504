import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ChatWidget } from './ChatWidget';

beforeEach(() => {
  window.sessionStorage.clear();
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/api/v1/chat/sessions')) {
      return new Response(JSON.stringify({
        session_id: 'session-001',
        session_token: 'session-token-001',
        expires_at: '2099-08-13T12:00:00Z',
        welcome_message: 'Hola, soy el asistente de SmartDiag504.',
      }), { status: 201, headers: { 'Content-Type': 'application/json' } });
    }
    if (url.includes('/api/v1/chat/sessions/session-001/messages') && init?.method === 'POST') {
      return new Response(JSON.stringify({
        session_id: 'session-001',
        user_message: {
          id: 'message-user', role: 'user', content: '¿Cómo reservo?', created_at: '2026-08-12T12:00:00Z',
        },
        assistant_message: {
          id: 'message-assistant', role: 'assistant', content: 'Puede reservar desde el formulario de esta página.', created_at: '2026-08-12T12:00:01Z',
        },
        audit_id: 'audit-001',
        mode: 'fallback',
        suggested_actions: ['BOOK_SERVICE'],
      }), { status: 201, headers: { 'Content-Type': 'application/json' } });
    }
    throw new Error(`Unexpected fetch: ${url}`);
  }));
});

describe('SmartDiag504 public chatbot', () => {
  it('opens, creates a session and displays the assistant reply', async () => {
    const user = userEvent.setup();
    render(<ChatWidget />);

    await user.click(screen.getByRole('button', { name: /abrir asistente/i }));
    expect(await screen.findByText(/hola, soy el asistente de SmartDiag504/i)).toBeInTheDocument();

    const input = screen.getByRole('textbox', { name: /escriba su consulta/i });
    await user.type(input, '¿Cómo reservo?');
    await user.click(screen.getByRole('button', { name: /enviar mensaje/i }));

    expect(await screen.findByText(/puede reservar desde el formulario/i)).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/chat/sessions/session-001/messages'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ 'X-Chat-Session-Token': 'session-token-001' }),
      }),
    );
  });
});
