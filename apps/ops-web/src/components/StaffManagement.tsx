import { useEffect, useState } from 'react';
import { Calculator, Clock3, Save, ShieldCheck, UserCheck, UserPlus, UserX } from 'lucide-react';
import { createStaffUser, getStaffAccessEvents, getStaffCompensationProfiles, getStaffUsers, updateStaffCompensation, updateStaffUser } from '../lib/api';
import type { StaffAccessEvent, StaffCompensationProfile, StaffRole, StaffUser } from '../types';

const ROLES: StaffRole[] = ['OWNER', 'ADMIN', 'MANAGER', 'ACCOUNTANT', 'TECHNICIAN', 'CASHIER', 'WAREHOUSE', 'RECEPTION', 'MARKETING', 'AUDITOR'];
const ROLE_LABELS: Record<StaffRole, string> = { OWNER: 'Propietario', ADMIN: 'Administrador', MANAGER: 'Gerente', ACCOUNTANT: 'Contador', TECHNICIAN: 'Técnico', CASHIER: 'Caja', WAREHOUSE: 'Bodega', RECEPTION: 'Recepción', MARKETING: 'Mercadeo', AUDITOR: 'Auditor' };
type CompensationDraft = { fixed_monthly_salary: string; productive_hours_monthly: string; base_hourly_wage: string; specialized_hourly_wage: string; employer_burden_percent: string; standard_sale_rate: string; specialized_sale_rate: string; currency: string; effective_from: string; source_system: string; source_reference: string | null };
const emptyCompensation = (): CompensationDraft => ({ fixed_monthly_salary: '', productive_hours_monthly: '176', base_hourly_wage: '0', specialized_hourly_wage: '0', employer_burden_percent: '35', standard_sale_rate: '', specialized_sale_rate: '', currency: 'HNL', effective_from: new Date().toISOString().slice(0, 10), source_system: 'LOCAL_PROJECTION', source_reference: null });

export function StaffManagement({ token }: { token: string }) {
  const [users, setUsers] = useState<StaffUser[]>([]);
  const [events, setEvents] = useState<StaffAccessEvent[]>([]);
  const [profiles, setProfiles] = useState<StaffCompensationProfile[]>([]);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [draft, setDraft] = useState({ email: '', password: '', full_name: '', job_title: '', phone: '', role: 'TECHNICIAN' as StaffRole });
  const [technicianId, setTechnicianId] = useState('');
  const [compensation, setCompensation] = useState(emptyCompensation);

  async function reload() {
    const [nextUsers, nextEvents, nextProfiles] = await Promise.all([getStaffUsers(token), getStaffAccessEvents(token), getStaffCompensationProfiles(token)]);
    setUsers(nextUsers); setEvents(nextEvents); setProfiles(nextProfiles);
  }
  useEffect(() => { void reload().catch((error: Error) => setMessage(error.message)); }, [token]);

  async function create(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setMessage('');
    try {
      await createStaffUser(token, draft);
      setDraft({ email: '', password: '', full_name: '', job_title: '', phone: '', role: 'TECHNICIAN' });
      await reload(); setMessage('Empleado creado. Ya puede iniciar sesión con su correo.');
    } catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo crear el empleado.'); }
    finally { setBusy(false); }
  }

  async function changeRole(user: StaffUser, role: StaffRole) {
    setBusy(true); setMessage('');
    try { await updateStaffUser(token, user.id, { role }); await reload(); setMessage(`Rol actualizado para ${user.full_name}.`); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo actualizar el rol.'); }
    finally { setBusy(false); }
  }

  async function toggle(user: StaffUser) {
    setBusy(true); setMessage('');
    try { await updateStaffUser(token, user.id, { is_active: !user.is_active }); await reload(); setMessage(user.is_active ? 'Acceso suspendido.' : 'Acceso reactivado.'); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo actualizar el acceso.'); }
    finally { setBusy(false); }
  }

  function selectTechnician(id: string) {
    setTechnicianId(id);
    const profile = profiles.find((item) => item.staff_user_id === id);
    setCompensation(profile ? { fixed_monthly_salary: profile.fixed_monthly_salary, productive_hours_monthly: profile.productive_hours_monthly, base_hourly_wage: profile.base_hourly_wage, specialized_hourly_wage: profile.specialized_hourly_wage, employer_burden_percent: profile.employer_burden_percent, standard_sale_rate: profile.standard_sale_rate, specialized_sale_rate: profile.specialized_sale_rate, currency: profile.currency, effective_from: profile.effective_from, source_system: profile.source_system, source_reference: profile.source_reference } : emptyCompensation());
  }

  async function saveCompensation(event: React.FormEvent) {
    event.preventDefault(); if (!technicianId) return; setBusy(true); setMessage('');
    try { await updateStaffCompensation(token, technicianId, compensation); await reload(); setMessage('Costos y tarifas del técnico actualizados.'); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo guardar la configuración salarial.'); }
    finally { setBusy(false); }
  }

  const currentProfile = profiles.find((item) => item.staff_user_id === technicianId);
  const updateComp = (field: keyof CompensationDraft, value: string) => setCompensation((current) => ({ ...current, [field]: value }));

  return <div className="staff-management">
    <header className="content-header"><div><span>RRHH y seguridad</span><h1>Personal, roles y accesos</h1><p>Cada empleado usa su propio correo. Los permisos se aplican en el servidor y cada inicio de sesión queda auditado.</p></div></header>
    {message && <p className="document-message">{message}</p>}
    <div className="staff-layout">
      <form className="role-panel staff-create" onSubmit={create}><header><UserPlus /><div><h2>Nuevo empleado</h2><p>No comparta la contraseña administrativa general.</p></div></header>
        <div className="staff-fields"><label>Nombre completo<input required minLength={3} value={draft.full_name} onChange={(event) => setDraft({ ...draft, full_name: event.target.value })} /></label><label>Código empleado<input disabled value="Se asigna automáticamente" /></label><label>Correo<input required type="email" value={draft.email} onChange={(event) => setDraft({ ...draft, email: event.target.value })} /></label><label>Contraseña inicial<input required type="password" minLength={12} value={draft.password} onChange={(event) => setDraft({ ...draft, password: event.target.value })} /></label><label>Cargo<input value={draft.job_title} onChange={(event) => setDraft({ ...draft, job_title: event.target.value })} /></label><label>Teléfono<input value={draft.phone} onChange={(event) => setDraft({ ...draft, phone: event.target.value })} /></label><label>Rol<select value={draft.role} onChange={(event) => setDraft({ ...draft, role: event.target.value as StaffRole })}>{ROLES.map((role) => <option value={role} key={role}>{ROLE_LABELS[role]}</option>)}</select></label></div>
        <button className="role-primary" disabled={busy}><UserCheck /> Crear acceso individual</button>
      </form>
      <section className="role-panel staff-list"><header><ShieldCheck /><div><h2>Directorio de accesos</h2><p>{users.length} empleados registrados</p></div></header>{users.map((user) => <article key={user.id} className={user.is_active ? '' : 'disabled'}><span className="staff-avatar">{user.full_name.slice(0, 2).toUpperCase()}</span><div><strong>{user.full_name}</strong><small>{user.employee_code} · {user.email}</small><em>{user.job_title || 'Sin cargo definido'} · {user.last_login_at ? `Último acceso ${new Date(user.last_login_at).toLocaleString('es-HN')}` : 'Sin ingresos'}</em></div><select aria-label={`Rol de ${user.full_name}`} disabled={busy} value={user.role} onChange={(event) => void changeRole(user, event.target.value as StaffRole)}>{ROLES.map((role) => <option value={role} key={role}>{ROLE_LABELS[role]}</option>)}</select><button aria-label={`${user.is_active ? 'Suspender' : 'Reactivar'} ${user.full_name}`} disabled={busy} onClick={() => void toggle(user)}>{user.is_active ? <UserX /> : <UserCheck />}</button></article>)}{users.length === 0 && <p>No hay empleados. Cree al propietario y luego asigne los demás roles.</p>}</section>
    </div>
    <section className="role-panel staff-compensation"><header><Calculator /><div><h2>Costos y tarifas de técnicos</h2><p>El salario fijo se distribuye entre horas productivas; luego se suman el pago por hora y las cargas patronales. Estos costos no aparecen en la cotización del cliente.</p></div></header>
      <form onSubmit={saveCompensation}><div className="staff-fields"><label>Técnico<select required value={technicianId} onChange={(event) => selectTechnician(event.target.value)}><option value="">Seleccione</option>{users.filter((user) => user.role === 'TECHNICIAN' && user.is_active).map((user) => <option value={user.id} key={user.id}>{user.employee_code} · {user.full_name}</option>)}</select></label><label>Salario fijo mensual<input required type="number" min="0" step="0.01" value={compensation.fixed_monthly_salary} onChange={(event) => updateComp('fixed_monthly_salary', event.target.value)} /></label><label>Horas productivas al mes<input required type="number" min="1" max="744" step="0.01" value={compensation.productive_hours_monthly} onChange={(event) => updateComp('productive_hours_monthly', event.target.value)} /></label><label>Pago adicional hora normal<input required type="number" min="0" step="0.01" value={compensation.base_hourly_wage} onChange={(event) => updateComp('base_hourly_wage', event.target.value)} /></label><label>Pago hora especializada<input required type="number" min="0" step="0.01" value={compensation.specialized_hourly_wage} onChange={(event) => updateComp('specialized_hourly_wage', event.target.value)} /></label><label>Cargas patronales %<input required type="number" min="0" max="300" step="0.01" value={compensation.employer_burden_percent} onChange={(event) => updateComp('employer_burden_percent', event.target.value)} /></label><label>Venta hora normal<input required type="number" min="0.01" step="0.01" value={compensation.standard_sale_rate} onChange={(event) => updateComp('standard_sale_rate', event.target.value)} /></label><label>Venta hora especializada<input required type="number" min="0.01" step="0.01" value={compensation.specialized_sale_rate} onChange={(event) => updateComp('specialized_sale_rate', event.target.value)} /></label><label>Vigente desde<input required type="date" value={compensation.effective_from} onChange={(event) => updateComp('effective_from', event.target.value)} /></label></div>
        {currentProfile && <div className="compensation-summary"><span>Costo fijo por hora <strong>L {Number(currentProfile.fixed_hourly_allocation).toFixed(2)}</strong></span><span>Costo real normal <strong>L {Number(currentProfile.standard_hourly_cost).toFixed(2)}</strong></span><span>Costo real especializado <strong>L {Number(currentProfile.specialized_hourly_cost).toFixed(2)}</strong></span></div>}
        <button className="role-primary" disabled={busy || !technicianId}><Save /> Guardar política salarial</button>
      </form>
    </section>
    <section className="role-panel staff-audit"><header><Clock3 /><div><h2>Bitácora de accesos</h2><p>Últimos 100 eventos de autenticación.</p></div></header>{events.map((item) => <article key={item.id}><span className={item.result === 'SUCCESS' ? 'ok' : 'failed'}>{item.result}</span><strong>{item.action}</strong><p>{item.detail}</p><time>{new Date(item.created_at).toLocaleString('es-HN')}</time></article>)}{events.length === 0 && <p>La bitácora se llenará con el primer inicio de sesión.</p>}</section>
  </div>;
}
