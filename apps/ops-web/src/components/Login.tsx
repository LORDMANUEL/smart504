import { FormEvent, useState } from 'react';
import { ArrowRight, KeyRound, LockKeyhole, Mail } from 'lucide-react';
import { Brand } from './Brand';
import { requestStaffPasswordReset, resetStaffPassword } from '../lib/api';

export function Login({ onLogin, onRecoveryLogin }: { onLogin: (email: string, password: string, mfaCode: string) => Promise<void>; onRecoveryLogin: (token: string) => void }) {
  const resetToken = new URLSearchParams(window.location.search).get('reset_token') ?? '';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirmation, setPasswordConfirmation] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [token, setToken] = useState('');
  const [recovery, setRecovery] = useState(false);
  const [forgotPassword, setForgotPassword] = useState(false);
  const [resetComplete, setResetComplete] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(''); setNotice('');
    if (resetToken && !resetComplete) {
      if (password.length < 12) { setError('La contraseña debe tener al menos 12 caracteres.'); return; }
      if (password !== passwordConfirmation) { setError('Las contraseñas no coinciden.'); return; }
      setBusy(true);
      try {
        await resetStaffPassword(resetToken, password);
        setResetComplete(true);
        window.history.replaceState({}, '', '/tallerv1/login');
      } catch (cause) { setError(cause instanceof Error ? cause.message : 'No se pudo restablecer la contraseña.'); }
      finally { setBusy(false); }
      return;
    }
    if (forgotPassword) {
      setBusy(true);
      try { await requestStaffPasswordReset(email); setNotice('Si el correo existe, recibirá un enlace temporal.'); }
      catch (cause) { setError(cause instanceof Error ? cause.message : 'No se pudo registrar la solicitud.'); }
      finally { setBusy(false); }
      return;
    }
    if (recovery) { if (token.trim()) onRecoveryLogin(token.trim()); return; }
    setBusy(true);
    try { await onLogin(email, password, mfaCode); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'No se pudo iniciar sesión.'); }
    finally { setBusy(false); }
  }

  const title = resetToken && !resetComplete ? 'Crear nueva contraseña' : forgotPassword ? 'Recuperar acceso' : 'Acceso del personal';
  const description = resetToken && !resetComplete ? 'Defina una contraseña nueva para su cuenta individual.' : forgotPassword ? 'Le enviaremos un enlace temporal si el correo está registrado.' : recovery ? 'Acceso temporal para el propietario durante la migración.' : 'Ingrese con el correo individual asignado por la empresa.';

  return <main className="login-screen">
    <div className="login-screen__image"><img src="/images/stock/workshop-hero.jpg" alt="Taller SmartDiag504" /><div><Brand /><h1>Operación del taller en una sola línea de tiempo.</h1><p>OT, técnicos, repuestos, bahías, factura y catálogo.</p></div></div>
    <form onSubmit={submit} className="login-card"><span><LockKeyhole /></span><h2>{title}</h2><p>{description}</p>{error && <p className="login-error">{error}</p>}{notice && <p className="login-success">{notice}</p>}
      {resetToken && !resetComplete ? <><label><KeyRound /> Nueva contraseña<input aria-label="Nueva contraseña" type="password" autoComplete="new-password" required minLength={12} value={password} onChange={(event) => setPassword(event.target.value)} autoFocus /></label><label><KeyRound /> Confirmar contraseña<input aria-label="Confirmar contraseña" type="password" autoComplete="new-password" required minLength={12} value={passwordConfirmation} onChange={(event) => setPasswordConfirmation(event.target.value)} /></label></> : forgotPassword ? <label><Mail /> Correo del empleado<input aria-label="Correo para recuperar acceso" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} autoFocus /></label> : recovery ? <label>Clave de recuperación<input aria-label="Clave de acceso del taller" type="password" value={token} onChange={(event) => setToken(event.target.value)} autoFocus /></label> : <><label><Mail /> Correo del empleado<input aria-label="Correo del empleado" type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} autoFocus /></label><label><KeyRound /> Contraseña<input aria-label="Contraseña" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} /></label><label><KeyRound /> Código MFA <small>(si está activo)</small><input aria-label="Código MFA" inputMode="numeric" pattern="[0-9]{6}" maxLength={6} autoComplete="one-time-code" value={mfaCode} onChange={(event) => setMfaCode(event.target.value.replace(/\D/g, ''))} /></label></>}
      <button className="primary-action" disabled={busy || resetComplete}>{busy ? 'Procesando...' : resetToken && !resetComplete ? 'Guardar contraseña' : forgotPassword ? 'Enviar enlace' : 'Entrar'} <ArrowRight /></button>
      {resetComplete ? <button type="button" className="login-recovery" onClick={() => window.location.assign('/tallerv1/login')}>Volver al inicio de sesión</button> : !resetToken && <><button type="button" className="login-recovery" onClick={() => { setForgotPassword(!forgotPassword); setRecovery(false); setError(''); setNotice(''); }}>{forgotPassword ? 'Volver al inicio de sesión' : '¿Olvidó su contraseña?'}</button>{!forgotPassword && <button type="button" className="login-recovery" onClick={() => { setRecovery(!recovery); setError(''); }}>{recovery ? 'Volver al acceso por empleado' : 'Acceso de recuperación del propietario'}</button>}</>}
    </form>
  </main>;
}
