import { CalendarCheck, CalendarClock, CheckCircle2, Mail, Phone, XCircle } from 'lucide-react';
import type { Booking, BookingStatus } from '../types';

const labels: Record<BookingStatus, string> = {
  NEW: 'Nueva',
  CONTACTED: 'Cliente contactado',
  CONFIRMED: 'Confirmada',
  CANCELLED: 'Cancelada',
};

export function BookingsView({
  bookings,
  busy,
  onStatusChange,
}: {
  bookings: Booking[];
  busy: boolean;
  onStatusChange: (booking: Booking, status: BookingStatus) => Promise<void>;
}) {
  return <div className="role-view bookings-view">
    <header className="content-header"><div><span>Recepción digital</span><h1>Citas solicitadas</h1><p>Distinga la captación pública de la cita confirmada por un cliente autenticado.</p></div></header>
    <div className="booking-kpis">
      <article><CalendarClock /><span>Nuevas<strong>{bookings.filter((item) => item.status === 'NEW').length}</strong></span></article>
      <article><CalendarCheck /><span>Confirmadas<strong>{bookings.filter((item) => item.status === 'CONFIRMED').length}</strong></span></article>
    </div>
    <section className="booking-list">
      {bookings.map((booking) => <article className={`booking-card booking-card--${booking.status.toLowerCase()}`} key={booking.id}>
        <header><div><small>{booking.source === 'CLIENT_PORTAL' ? 'Cliente autenticado' : booking.source === 'KANBAN' ? 'Recepción / Kanban' : 'Landing pública'} · {booking.scheduled_at ? new Date(booking.scheduled_at).toLocaleString('es-HN') : booking.preferred_date ? `Fecha solicitada ${booking.preferred_date}` : 'Fecha por coordinar'}</small><h2>{booking.full_name}</h2></div><b>{labels[booking.status]}</b></header>
        <dl><div><dt>Vehículo</dt><dd>{booking.vehicle_summary}</dd></div><div><dt>Servicio</dt><dd>{booking.service_requested}</dd></div></dl>
        <p>{booking.concern}</p>
        <div className="booking-contact"><span><Phone /> {booking.phone}</span>{booking.email && <span><Mail /> {booking.email}</span>}</div>
        <footer>
          {booking.status === 'NEW' && <button disabled={busy} onClick={() => void onStatusChange(booking, 'CONTACTED')}>Marcar contactado</button>}
          {!['CONFIRMED', 'CANCELLED'].includes(booking.status) && <button className="role-primary" disabled={busy} onClick={() => void onStatusChange(booking, 'CONFIRMED')}><CheckCircle2 /> Confirmar cita</button>}
          {booking.status !== 'CANCELLED' && <button className="danger-action" disabled={busy} onClick={() => void onStatusChange(booking, 'CANCELLED')}><XCircle /> Cancelar</button>}
        </footer>
      </article>)}
      {bookings.length === 0 && <div className="empty-bookings"><CalendarClock /><h2>Sin citas pendientes</h2><p>Las solicitudes de la landing y del portal aparecerán aquí.</p></div>}
    </section>
  </div>;
}
