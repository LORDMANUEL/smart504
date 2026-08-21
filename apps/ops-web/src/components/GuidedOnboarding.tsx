import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, ArrowRight, BookOpenCheck, X } from 'lucide-react';
import type { StaffRole } from '../types';

type Step = { title: string; detail: string; target: string };
const shared: Step[] = [
  { title: 'Menú de trabajo', detail: 'Aquí aparecen únicamente los módulos permitidos para su usuario.', target: '[data-tour="navigation"]' },
  { title: 'Búsqueda operativa', detail: 'Busque órdenes, VIN, placas o clientes sin recorrer cada módulo.', target: '[data-tour="global-search"]' },
  { title: 'Ayuda disponible', detail: 'Puede volver a abrir este recorrido desde el botón Guía.', target: '[data-tour="tour-button"]' },
];
const roleSteps: Partial<Record<StaffRole, Step[]>> = {
  CASHIER: [{ title: 'Mostrador y caja', detail: 'Seleccione inventario existente, cotice o cobre. Si falta una pieza, envíe una solicitud a Compras.', target: '[data-tour="COUNTER"]' }],
  TECHNICIAN: [{ title: 'Mi trabajo técnico', detail: 'Abra sus OTs, documente diagnóstico y agregue fotografías antes de entregar.', target: '[data-tour="TECHNICIAN"]' }],
  WAREHOUSE: [{ title: 'Bodega', detail: 'Atienda solicitudes por OT y registre cada entrega o devolución.', target: '[data-tour="WAREHOUSE"]' }],
  RECEPTION: [{ title: 'Recepción y citas', detail: 'Confirme citas, identifique al cliente y convierta el ingreso en una sola OT.', target: '[data-tour="BOOKINGS"]' }],
  ACCOUNTANT: [{ title: 'Contador', detail: 'Revise configuración fiscal, conciliación y reportes sin duplicar la contabilidad del ERP.', target: '[data-tour="ACCOUNTING"]' }],
  MARKETING: [{ title: 'Publicidad', detail: 'Cree campañas y publíquelas para landing, enlaces y pantallas del taller.', target: '[data-tour="MARKETING"]' }],
};

const counterSteps: Step[] = [
  { title: 'Buscar por VIN o pieza', detail: 'Use el VIN para filtrar repuestos compatibles o busque por código y nombre.', target: '[data-tour="counter-search"]' },
  { title: 'Inventario real de bodega', detail: 'Sólo puede seleccionar artículos activos, con precio y existencia disponible.', target: '[data-tour="counter-products"]' },
  { title: 'Cotizar o cobrar', detail: 'Puede enviar la selección al seguimiento de cotizaciones o completar la venta en caja.', target: '[data-tour="counter-checkout"]' },
];

export function GuidedOnboarding({ role, module, open, onClose }: { role: StaffRole; module?: string; open: boolean; onClose: () => void }) {
  const steps = useMemo(() => module === 'COUNTER' ? counterSteps : [...(roleSteps[role] || []), ...shared], [module, role]);
  const [index, setIndex] = useState(0);
  useEffect(() => { if (open) setIndex(0); }, [open]);
  useEffect(() => {
    document.querySelectorAll('.tour-highlight').forEach((node) => node.classList.remove('tour-highlight'));
    if (!open) return undefined;
    const node = document.querySelector(steps[index]?.target || '');
    node?.classList.add('tour-highlight');
    return () => node?.classList.remove('tour-highlight');
  }, [index, open, steps]);
  if (!open) return null;
  const step = steps[index]; const finish = index === steps.length - 1;
  return <div className="tour-backdrop" role="dialog" aria-modal="true" aria-labelledby="tour-title"><section className="tour-popup"><header><span><BookOpenCheck /> Recorrido guiado</span><button aria-label="Omitir recorrido" onClick={onClose}><X /></button></header><div className="tour-progress" aria-label={`Paso ${index + 1} de ${steps.length}`}><span style={{ width: `${((index + 1) / steps.length) * 100}%` }} /></div><small>Paso {index + 1} de {steps.length}</small><h2 id="tour-title">{step.title}</h2><p>{step.detail}</p><footer><button disabled={index === 0} onClick={() => setIndex((value) => value - 1)}><ArrowLeft /> Anterior</button><button className="role-primary" onClick={() => finish ? onClose() : setIndex((value) => value + 1)}>{finish ? 'Empezar a trabajar' : 'Siguiente'} {!finish && <ArrowRight />}</button></footer></section></div>;
}
