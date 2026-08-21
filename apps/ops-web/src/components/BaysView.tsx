import { CarFront, Construction, Wrench } from 'lucide-react';
import type { BoardResponse } from '../types';

export function BaysView({ board, enabled }: { board: BoardResponse; enabled: boolean }) {
  if (!enabled) {
    return <div className="disabled-feature"><Construction size={34} /><h2>La vista de bahías está desactivada</h2><p>Actívela en Configuración cuando el taller quiera asignar físicamente vehículos a espacios de trabajo. Kanban continúa siendo la vista predeterminada.</p></div>;
  }
  const cards = board.columns.flatMap((column) => column.cards);
  const bays = Array.from({ length: 8 }, (_, index) => `B-${String(index + 1).padStart(2, '0')}`);
  return (
    <div className="bays-layout">
      <div className="bays-grid">
        {bays.map((bay) => {
          const card = cards.find((item) => item.bay_code === bay);
          return <article className={card ? 'bay bay--occupied' : 'bay'} key={bay}>
            <header><strong>{bay}</strong><span>{card ? 'Ocupada' : 'Disponible'}</span></header>
            {card ? <><CarFront size={42} /><h3>{card.vehicle_label}</h3><p>{card.external_reference} · {card.title}</p><small><Wrench size={13} />{card.technician_name ?? 'Sin técnico'}</small></> : <><span className="bay__lane" /><p>Lista para asignación</p></>}
          </article>;
        })}
      </div>
      <aside className="unassigned"><h2>Sin bahía</h2>{cards.filter((card) => !card.bay_code && card.status !== 'INVOICED').map((card) => <div key={card.id}><strong>{card.external_reference}</strong><span>{card.vehicle_label}</span></div>)}</aside>
    </div>
  );
}
