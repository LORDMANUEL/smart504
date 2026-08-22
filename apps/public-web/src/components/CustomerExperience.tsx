import { useEffect, useState } from 'react';
import { AlertTriangle, ArrowRight, Award, CalendarDays, CarFront, CheckCircle2, Clock3, CreditCard, Eye, FileCheck2, FileText, Gauge, History, KeyRound, LogOut, PackageSearch, Plus, Printer, Settings, ShieldCheck, ShoppingCart, Store, UserRound, Wrench, XCircle } from 'lucide-react';
import { Brand } from './Brand';
import { addClientVehicle, clientDocument, createClientAppointment, decideClientQuoteLine, getAppointmentSlots, getClientAppointments, getClientCompatibleParts, getClientDashboard, getClientRegistrationOptions, loginClient, logoutClient, registerClient, updateClientProfile } from '../lib/api';
import type { ClientRegistrationOptions } from '../lib/api';
import type { AppointmentSlot, ClientAppointment, ClientDashboard, Product } from '../types';

const money = (value: number) => new Intl.NumberFormat('es-HN', { style: 'currency', currency: 'HNL' }).format(value);

async function downloadInvoice(invoiceNumber: string) {
  const url = URL.createObjectURL(await clientDocument(`/api/v1/client-documents/invoices/${encodeURIComponent(invoiceNumber)}.pdf`));
  const link = document.createElement('a');
  link.href = url; link.download = `${invoiceNumber}.pdf`; link.click();
  URL.revokeObjectURL(url);
}

export function AccessHub() {
  return <main className="access-hub">
    <header><a href="/lading">← Volver al taller</a><Brand /><span>SMARTDIAG504 DIGITAL</span><h1>¿Qué desea hacer?</h1><p>Compre repuestos compatibles o ingrese a la aplicación de cliente para administrar su vehículo y solicitar una cita.</p></header>
    <section>
      <a href="/lading/repuestos"><Store /><div><small>TIENDA EN LÍNEA</small><h2>Comprar repuestos</h2><p>Consulte disponibilidad, compatibilidad y precio antes de solicitar su pedido.</p><strong>Entrar a la tienda <ArrowRight /></strong></div></a>
      <a href="/lading/loginclie"><UserRound /><div><small>APLICACIÓN DEL CLIENTE</small><h2>Mi vehículo</h2><p>Registre y consulte carros, alertas, cotizaciones, facturas, promociones y citas.</p><strong>Ingresar como cliente <ArrowRight /></strong></div></a>
    </section>
    <footer>¿Trabaja en el taller? <a href="/tallerv1/login">Acceso para personal autorizado</a></footer>
  </main>;
}

export function CustomerAccess() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [username, setUsername] = useState('');
  const [options, setOptions] = useState<ClientRegistrationOptions | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  useEffect(() => { void getClientRegistrationOptions().then(setOptions).catch(() => setOptions(null)); }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!email.includes('@') || password.length < 6) {
      setError('Ingrese un correo válido y una contraseña de al menos seis caracteres.');
      return;
    }
    setLoading(true); setError('');
    try {
      await loginClient(email, password);
      sessionStorage.setItem('smartdiag-client-session', 'authenticated');
      window.history.pushState({}, '', '/lading/cliente');
      window.dispatchEvent(new PopStateEvent('popstate'));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Acceso no válido.');
    } finally { setLoading(false); }
  }

  async function createAccount(event: React.FormEvent) {
    event.preventDefault(); setError(''); setSuccess('');
    if (fullName.trim().length < 3 || phone.trim().length < 8 || !email.includes('@') || password.length < 10) {
      setError('Complete nombre, teléfono, correo válido y una contraseña de al menos diez caracteres.'); return;
    }
    setLoading(true);
    try {
      const created = await registerClient({ full_name: fullName, phone, email, password, username: username || undefined });
      setSuccess(`${created.message} Usuario: ${created.username}. Correo reservado: ${created.managed_email}.`);
      setMode('login');
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'No se pudo crear la cuenta.'); }
    finally { setLoading(false); }
  }

  return <main className="client-login">
    <section className="client-login__brand"><Brand /><h1>El historial de su carro, en un solo lugar.</h1><p>Repuestos compatibles, alertas, cotizaciones, facturas y promociones del taller.</p></section>
    <form className="client-login__form" onSubmit={mode === 'login' ? submit : createAccount}>
      <a href="/lading/acceso">← Volver a accesos</a>
      <div className="client-auth-tabs" role="tablist"><button type="button" className={mode === 'login' ? 'active' : ''} onClick={() => { setMode('login'); setError(''); }}>Ingresar</button><button type="button" className={mode === 'register' ? 'active' : ''} onClick={() => { setMode('register'); setError(''); }}>Crear cuenta</button></div>
      <h2>{mode === 'login' ? 'Acceso de clientes' : 'Crear cuenta de cliente'}</h2><p>{mode === 'login' ? 'Ingrese con su correo personal y contraseña.' : 'Su correo personal se usará para recuperación y notificaciones.'}</p>
      {mode === 'register' && <><label>Nombre completo<input required autoComplete="name" value={fullName} onChange={(event) => setFullName(event.target.value)} /></label><label>Teléfono<input required autoComplete="tel" value={phone} onChange={(event) => setPhone(event.target.value)} /></label><label>Usuario preferido <small>(opcional)</small><input autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Se genera automáticamente" /></label></>}
      <label>Correo electrónico<input aria-label="Correo electrónico" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
      <label>Contraseña<input aria-label="Contraseña" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
      {error && <p className="form-error" role="alert">{error}</p>}
      {success && <p className="form-success" role="status">{success}</p>}
      <button className="button button--gold" disabled={loading}>{loading ? 'Procesando…' : mode === 'login' ? 'Ingresar a mi vehículo' : 'Crear mi cuenta'}</button>
      {mode === 'register' && <small>Se reservará un correo @{options?.managed_mail_domain ?? 'smartdiag504.com'}. El buzón se activa cuando el servicio de correo y el dominio estén configurados.</small>}
      {options?.social_login.enabled && options.social_login.login_url && <a className="client-social-login" href={options.social_login.login_url}>Continuar con una red social mediante ERPNext</a>}
    </form>
  </main>;
}

export function CustomerPortal() {
  if (sessionStorage.getItem('smartdiag-client-session') !== 'authenticated') {
    window.location.replace('/lading/loginclie');
    return null;
  }
  const [section, setSection] = useState(() => window.location.hash.replace('#', '') || 'vehicle');
  const [dashboard, setDashboard] = useState<ClientDashboard | null>(null);
  const [portalError, setPortalError] = useState('');
  const [vehicleId, setVehicleId] = useState('');
  const [cart, setCart] = useState<string[]>([]);
  const [parts, setParts] = useState<Product[]>([]);
  const [partsLoading, setPartsLoading] = useState(false);
  const [partsError, setPartsError] = useState('');
  const [appointmentDate, setAppointmentDate] = useState('');
  const [appointmentSlot, setAppointmentSlot] = useState('');
  const [appointmentService, setAppointmentService] = useState('Diagnóstico electrónico');
  const [appointmentConcern, setAppointmentConcern] = useState('Revisión solicitada desde mi vehículo.');
  const [slots, setSlots] = useState<AppointmentSlot[]>([]);
  const [appointments, setAppointments] = useState<ClientAppointment[]>([]);
  const [appointmentMessage, setAppointmentMessage] = useState('');
  const [showVehicleForm, setShowVehicleForm] = useState(false);
  const [vehicleDraft, setVehicleDraft] = useState({ vin: '', plate: '', make: 'Ford', model: '', model_year: 2020, engine: '', mileage_km: 0 });
  const [profileMessage, setProfileMessage] = useState('');
  const selected = dashboard?.vehicles.find((vehicle) => vehicle.id === vehicleId) ?? dashboard?.vehicles[0];
  const selectedVehicleId = selected?.id ?? '';
  async function reloadDashboard() {
    try { const data = await getClientDashboard(); setDashboard(data); setVehicleId((current) => current || data.vehicles[0]?.id || ''); }
    catch (error) { setPortalError(error instanceof Error ? error.message : 'No se pudo cargar el portal.'); }
  }
  useEffect(() => {
    void reloadDashboard();
    void getClientAppointments().then(setAppointments).catch(() => setAppointments([]));
    const onHash = () => setSection(window.location.hash.replace('#', '') || 'vehicle');
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);
  useEffect(() => {
    if (!appointmentDate) { setSlots([]); return; }
    void getAppointmentSlots(appointmentDate).then((items) => { setSlots(items); setAppointmentSlot(''); }).catch((error: Error) => setAppointmentMessage(error.message));
  }, [appointmentDate]);
  useEffect(() => {
    if (!selectedVehicleId) { setParts([]); return; }
    let active = true;
    setPartsLoading(true);
    setPartsError('');
    void getClientCompatibleParts(selectedVehicleId)
      .then((items) => { if (active) setParts(items); })
      .catch((error: Error) => { if (active) { setParts([]); setPartsError(error.message); } })
      .finally(() => { if (active) setPartsLoading(false); });
    return () => { active = false; };
  }, [selectedVehicleId]);

  async function reserveAuthenticatedAppointment(event: React.FormEvent) {
    event.preventDefault(); setAppointmentMessage('');
    if (!appointmentSlot) { setAppointmentMessage('Seleccione un horario disponible.'); return; }
    try {
      if (!selected) return;
      const created = await createClientAppointment({ vehicle_id: selected.id, vehicle_summary: selected.label, service_requested: appointmentService, scheduled_at: appointmentSlot, concern: appointmentConcern });
      setAppointments((items) => [created, ...items]);
      setAppointmentMessage(`Cita confirmada · ${new Date(created.scheduled_at).toLocaleString('es-HN')}`);
      setSlots((items) => items.map((slot) => slot.starts_at === appointmentSlot ? { ...slot, available: false } : slot));
      setAppointmentSlot('');
    } catch (error) { setAppointmentMessage(error instanceof Error ? error.message : 'No se pudo reservar.'); }
  }

  function go(target: string) { window.location.hash = target; setSection(target); }
  async function openDocument(path: string, filename?: string) {
    try { const blob = await clientDocument(path); const url = URL.createObjectURL(blob); if (filename) { const link = document.createElement('a'); link.href = url; link.download = filename; link.click(); } else window.open(url, '_blank', 'noopener,noreferrer'); setTimeout(() => URL.revokeObjectURL(url), 15000); }
    catch (error) { setPortalError(error instanceof Error ? error.message : 'No se pudo abrir el documento.'); }
  }
  async function saveVehicle(event: React.FormEvent) {
    event.preventDefault(); try { const created = await addClientVehicle(vehicleDraft); setDashboard((current) => current ? { ...current, vehicles: [...current.vehicles, created] } : current); setVehicleId(created.id); setShowVehicleForm(false); setVehicleDraft({ vin: '', plate: '', make: 'Ford', model: '', model_year: 2020, engine: '', mileage_km: 0 }); }
    catch (error) { setPortalError(error instanceof Error ? error.message : 'No se pudo registrar el vehículo.'); }
  }
  async function saveProfile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!dashboard) return; const form = new FormData(event.currentTarget);
    try { const newPassword = String(form.get('new_password') || '') || undefined; const profile = await updateClientProfile({ full_name: String(form.get('full_name')), email: String(form.get('email')), username: String(form.get('username')), credit_requested: form.get('credit_requested') === 'on', credit_amount: Number(form.get('credit_amount') || 0) || undefined, new_password: newPassword }); setDashboard({ ...dashboard, profile }); setProfileMessage(newPassword ? 'Configuración y contraseña guardadas.' : 'Configuración guardada.'); }
    catch (error) { setProfileMessage(error instanceof Error ? error.message : 'No se pudo guardar.'); }
  }
  if (!dashboard || !selected) return <div className="client-portal client-portal--loading"><p>{portalError || 'Cargando su información…'}</p></div>;
  const nav = [['vehicle', CarFront, 'Mi vehículo'], ['appointments', CalendarDays, 'Agendar cita'], ['parts', PackageSearch, 'Repuestos compatibles'], ['alerts', AlertTriangle, 'Alertas'], ['quotes', FileCheck2, 'Cotizaciones'], ['invoices', FileText, 'Facturas']] as const;
  return <div className="client-portal">
    <aside><Brand /><nav>{nav.map(([id, Icon, label]) => <a className={section === id ? 'active' : ''} href={`#${id}`} key={id}><Icon /> {label}{id === 'alerts' && <b>{dashboard.alerts.length}</b>}</a>)}</nav><div className="client-account-actions"><a className={section === 'settings' ? 'active' : ''} href="#settings"><Settings /> Configuración</a><a href="/lading/loginclie" onClick={() => { sessionStorage.removeItem('smartdiag-client-session'); void logoutClient(); }}><LogOut /> Cerrar sesión</a></div></aside>
    <main><header><div><p>Bienvenido, {dashboard.profile.full_name}</p><h1>{section === 'vehicle' ? selected.label : nav.find(([id]) => id === section)?.[2] ?? 'Configuración'}</h1></div><label>Vehículo<select aria-label="Vehículo" value={vehicleId} onChange={(event) => setVehicleId(event.target.value)}>{dashboard.vehicles.map((vehicle) => <option key={vehicle.id} value={vehicle.id}>{vehicle.label}</option>)}</select></label></header>
      {portalError && <p className="portal-error" role="alert">{portalError}<button onClick={() => setPortalError('')}>Cerrar</button></p>}
      {section === 'vehicle' && <section className="vehicle-dashboard"><article className="vehicle-hero"><div><p>Estado de mantenimiento</p><h2>{selected.label}</h2><span>{selected.engine} · {selected.mileage_km.toLocaleString('es-HN')} km</span><dl><div><dt>Placa</dt><dd>{selected.plate || 'Sin placa'}</dd></div><div><dt>VIN</dt><dd>{selected.vin}</dd></div><div><dt>Próximo servicio</dt><dd>{selected.maintenance.next_service_km.toLocaleString('es-HN')} km</dd></div></dl></div><img src={selected.photo_url || '/vehicles/ford-escape-2020.png'} alt={`${selected.label} sin fondo`} /></article><div className="vehicle-health"><article><Gauge /><span><small>Servicio preventivo</small><strong>Faltan 800 km</strong></span></article><article><Wrench /><span><small>Último cambio de aceite</small><strong>{selected.maintenance.oil_last_km.toLocaleString('es-HN')} km</strong></span></article><article><CalendarDays /><span><small>Próximo cambio</small><strong>{selected.maintenance.oil_next_km.toLocaleString('es-HN')} km</strong></span></article></div><div className="vehicle-detail-grid"><section><h2><History /> Historial reciente</h2>{selected.history.length ? selected.history.map((item) => <article key={item.id}><span><strong>{item.summary}</strong><small>{new Date(item.date).toLocaleDateString('es-HN')} · {item.reference}</small></span><b>{item.mileage_km?.toLocaleString('es-HN')} km</b></article>) : <p>Aún no hay mantenimientos registrados para este vehículo.</p>}</section><section><h2><ShieldCheck /> Consejos preventivos</h2>{selected.advice.map((item) => <p key={item}><CheckCircle2 /> {item}</p>)}</section></div><section className="other-vehicles"><header><div><h2>Mis vehículos</h2><p>Seleccione uno para consultar su historial y compatibilidad.</p></div><button onClick={() => setShowVehicleForm((value) => !value)}><Plus /> Agregar vehículo</button></header><div>{dashboard.vehicles.map((vehicle) => <button className={vehicle.id === selected.id ? 'active' : ''} onClick={() => setVehicleId(vehicle.id)} key={vehicle.id}><img src={vehicle.photo_url || '/vehicles/ford-escape-2020.png'} alt={vehicle.label} /><span><strong>{vehicle.label}</strong><small>{vehicle.plate || vehicle.vin}</small></span></button>)}</div>{showVehicleForm && <form className="vehicle-add-form" onSubmit={saveVehicle}><label>Marca<input value={vehicleDraft.make} onChange={(event) => setVehicleDraft({ ...vehicleDraft, make: event.target.value })} /></label><label>Modelo<input required value={vehicleDraft.model} onChange={(event) => setVehicleDraft({ ...vehicleDraft, model: event.target.value })} /></label><label>Año<input type="number" required value={vehicleDraft.model_year} onChange={(event) => setVehicleDraft({ ...vehicleDraft, model_year: Number(event.target.value) })} /></label><label>VIN<input required minLength={11} value={vehicleDraft.vin} onChange={(event) => setVehicleDraft({ ...vehicleDraft, vin: event.target.value })} /></label><label>Placa<input value={vehicleDraft.plate} onChange={(event) => setVehicleDraft({ ...vehicleDraft, plate: event.target.value })} /></label><label>Kilometraje<input type="number" value={vehicleDraft.mileage_km} onChange={(event) => setVehicleDraft({ ...vehicleDraft, mileage_km: Number(event.target.value) })} /></label><button>Guardar vehículo</button></form>}</section></section>}
      {section === 'appointments' && <section className="client-appointments"><div><small>CITA AUTENTICADA</small><h2>Reservar en el calendario</h2><p>La cita queda vinculada a su cuenta y al vehículo seleccionado.</p></div><form onSubmit={reserveAuthenticatedAppointment}><label>Fecha<input type="date" min={new Date(Date.now() + 86400000).toISOString().slice(0, 10)} value={appointmentDate} onChange={(event) => setAppointmentDate(event.target.value)} /></label><label>Servicio<select value={appointmentService} onChange={(event) => setAppointmentService(event.target.value)}><option>Diagnóstico electrónico</option><option>Mantenimiento preventivo</option><option>Frenos y suspensión</option><option>Aire acondicionado</option><option>Transmisión</option></select></label><label>Horario<div className="appointment-slots">{slots.map((slot) => <button type="button" disabled={!slot.available} className={appointmentSlot === slot.starts_at ? 'active' : ''} onClick={() => setAppointmentSlot(slot.starts_at)} key={slot.starts_at}><Clock3 /> {new Date(slot.starts_at).toLocaleTimeString('es-HN', { hour: '2-digit', minute: '2-digit' })}</button>)}{appointmentDate && !slots.length && <span>No hay horarios disponibles.</span>}</div></label><label>Motivo<textarea rows={3} value={appointmentConcern} onChange={(event) => setAppointmentConcern(event.target.value)} /></label><button className="button button--gold">Confirmar cita</button>{appointmentMessage && <p role="status">{appointmentMessage}</p>}</form><div className="appointment-history"><h3>Mis próximas citas</h3>{appointments.map((item) => <article key={item.id}><CalendarDays /><span><strong>{item.service_requested}</strong><small>{new Date(item.scheduled_at).toLocaleString('es-HN')} · {item.vehicle_summary}</small></span><b>{item.status}</b></article>)}</div></section>}
      {section === 'parts' && <section><div className="portal-heading"><div><h2>Repuestos para {selected.label}</h2><p>Catálogo publicado y validado para este vehículo. Confirme siempre por VIN antes de instalar.</p></div><span><ShoppingCart /> {cart.length} seleccionados</span></div>{partsLoading && <p role="status">Consultando inventario compatible…</p>}{partsError && <p className="portal-error" role="alert">{partsError}</p>}<div className="compatible-parts">{parts.map((part) => { const image = part.images.find((item) => item.is_primary) ?? part.images[0]; return <article key={part.id}>{image ? <img src={image.url} alt={image.alt_text} /> : <PackageSearch aria-label="Sin fotografía" />}<div><small>{part.sku} · {part.stock_status}</small><h3>{part.name}</h3><strong>{money(Number(part.display_price))}</strong></div><button disabled={part.stock_status === 'OUT_OF_STOCK'} onClick={() => setCart((items) => items.includes(part.id) ? items.filter((id) => id !== part.id) : [...items, part.id])}>{cart.includes(part.id) ? 'Quitar' : part.stock_status === 'OUT_OF_STOCK' ? 'Sin existencia' : 'Agregar'}</button></article>; })}</div>{!partsLoading && !partsError && !parts.length && <p className="portal-empty">No hay repuestos publicados para este VIN. Solicite una búsqueda al taller.</p>}</section>}
      {section === 'alerts' && <section className="client-alerts"><header><h2>Aprobaciones y estados</h2><p>Decisiones pendientes, mantenimientos y cambios del taller.</p></header>{dashboard.alerts.map((alert) => <article key={alert.id}><AlertTriangle /><span><strong>{alert.title}</strong><small>{alert.detail}</small></span><b>{alert.status}</b>{alert.quote_id && <button onClick={() => go('quotes')}>Revisar</button>}</article>)}</section>}
      {section === 'quotes' && <section className="client-quotes"><header><h2>Cotizaciones por fecha</h2><p>Abra, imprima y apruebe cada concepto antes de que pase a caja.</p></header>{dashboard.quotes.map((quote) => <article key={quote.id}><header><div><strong>{quote.number}</strong><small>{new Date(quote.created_at).toLocaleString('es-HN')}</small></div><span>{quote.status}</span><b>{money(Number(quote.total))}</b></header><div className="quote-client-lines">{quote.lines.map((line) => <div key={line.id}><span><strong>{line.description}</strong><small>{line.code} · {line.quantity} × {money(Number(line.unit_price))}</small></span><b>{money(Number(line.line_total))}</b><em className={`decision-${line.approval_status.toLowerCase()}`}>{line.approval_status}</em>{line.approval_status === 'PENDING' && <span className="quote-decisions"><button onClick={async () => { await decideClientQuoteLine(quote.id, line.id, 'APPROVED'); await reloadDashboard(); }}><CheckCircle2 /> Aprobar</button><button onClick={async () => { await decideClientQuoteLine(quote.id, line.id, 'REJECTED'); await reloadDashboard(); }}><XCircle /> Rechazar</button></span>}</div>)}</div><footer><button onClick={() => void openDocument(`/api/v1/client-documents/quotes/${quote.id}.html`)}><Eye /> Ver HTML</button><button onClick={() => void openDocument(`/api/v1/client-documents/quotes/${quote.id}.pdf`, `${quote.number}.pdf`)}><Printer /> Descargar PDF</button></footer></article>)}{!dashboard.quotes.length && <p className="portal-empty">Aún no hay cotizaciones para este cliente.</p>}</section>}
      {section === 'invoices' && <section className="client-invoices"><header><h2>Facturas y recibos</h2><p>Documentos ordenados desde el más reciente.</p></header>{dashboard.invoices.map((invoice) => <article key={invoice.number}><FileText /><span><strong>{invoice.number}</strong><small>{new Date(invoice.created_at).toLocaleString('es-HN')}</small></span><b>{money(Number(invoice.total))}</b><button onClick={() => void downloadInvoice(invoice.number)}><Printer /> Descargar</button></article>)}{!dashboard.invoices.length && <p className="portal-empty">Aún no hay facturas emitidas para este cliente.</p>}</section>}
      {section === 'settings' && <section className="client-settings"><header><h2>Configuración de la cuenta</h2><p>Actualice sus datos, seguridad, crédito y programa de lealtad.</p></header><form onSubmit={saveProfile}><div className="settings-group"><UserRound /><label>Nombre completo<input name="full_name" defaultValue={dashboard.profile.full_name} /></label><label>Correo<input name="email" type="email" defaultValue={dashboard.profile.email} /></label><label>Usuario<input name="username" defaultValue={dashboard.profile.username} /></label></div><div className="settings-group"><KeyRound /><label>Nueva contraseña<input name="new_password" type="password" minLength={10} placeholder="Deje vacío para conservarla" /></label><span>MFA: <b>{dashboard.profile.mfa_enabled ? 'Activo' : 'No configurado'}</b></span><small>La activación MFA requiere enrolamiento y confirmación con código; no se activa con una casilla.</small></div><div className="settings-group"><CreditCard /><label className="check-setting"><input name="credit_requested" type="checkbox" defaultChecked={dashboard.profile.credit_requested} /> Solicitar evaluación de crédito</label><label>Monto solicitado<input name="credit_amount" type="number" min="1000" step="500" /></label><span>Estado: <b>{dashboard.profile.credit_status}</b></span></div><div className="loyalty-box"><Award /><span><strong>{dashboard.profile.loyalty_points} puntos</strong><small>{dashboard.profile.loyalty_enabled ? 'Programa de lealtad activo' : 'El dueño aún no activa el programa'}</small></span></div><button className="button button--gold">Guardar cambios</button>{profileMessage && <p role="status">{profileMessage}</p>}</form></section>}
    </main></div>;
}
