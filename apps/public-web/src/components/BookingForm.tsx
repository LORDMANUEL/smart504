import { FormEvent, useState } from 'react';
import { CalendarCheck, LoaderCircle } from 'lucide-react';
import { createBooking } from '../lib/api';

export function BookingForm() {
  const [state, setState] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  const [message, setMessage] = useState('');

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    // Keep the form element before awaiting; React clears event.currentTarget after dispatch.
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setState('sending');
    try {
      const booking = await createBooking({
        customer_name: String(form.get('customer_name') ?? ''),
        phone: String(form.get('phone') ?? ''),
        email: String(form.get('email') ?? '') || undefined,
        vehicle_summary: String(form.get('vehicle_summary') ?? ''),
        requested_service: String(form.get('requested_service') ?? ''),
        preferred_date: String(form.get('preferred_date') ?? '') || undefined,
        notes: String(form.get('notes') ?? '') || undefined,
        idempotency_key: crypto.randomUUID(),
      });
      formElement.reset();
      setState('sent');
      setMessage(`Reserva recibida · referencia ${booking.id.slice(0, 8).toUpperCase()}. Nuestro equipo confirmará la disponibilidad contigo.`);
    } catch (error) {
      setState('error');
      setMessage(error instanceof Error ? error.message : 'No fue posible enviar la reserva.');
    }
  }

  return (
    <form className="booking-form" onSubmit={submit}>
      <div className="form-grid">
        <label>Nombre completo<input required name="customer_name" autoComplete="name" /></label>
        <label>Teléfono<input required name="phone" autoComplete="tel" /></label>
        <label>Correo<input name="email" type="email" autoComplete="email" /></label>
        <label>Vehículo<input required name="vehicle_summary" placeholder="Ej. Ford Explorer 2020" /></label>
        <label className="form-grid__wide">Servicio solicitado<select required name="requested_service" defaultValue="">
          <option value="" disabled>Seleccione un servicio</option>
          <option>Diagnóstico electrónico</option>
          <option>Transmisión</option>
          <option>Aire acondicionado</option>
          <option>Mantenimiento preventivo</option>
          <option>Frenos y suspensión</option>
          <option>Programación y módulos</option>
        </select></label>
        <label>Fecha preferida<input name="preferred_date" type="date" /></label>
        <label className="form-grid__wide">Explique el síntoma<textarea name="notes" rows={4} placeholder="Qué ocurre, desde cuándo y qué luces están encendidas..." /></label>
      </div>
      <button className="button button--gold" type="submit" disabled={state === 'sending'}>
        {state === 'sending' ? <LoaderCircle className="spin" size={19} /> : <CalendarCheck size={19} />}
        Solicitar reserva
      </button>
      {message && <p className={`form-message form-message--${state}`} role="status">{message}</p>}
    </form>
  );
}
