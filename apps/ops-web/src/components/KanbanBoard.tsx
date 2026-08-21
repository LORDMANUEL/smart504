import { AlertTriangle, ArrowRight, CarFront, Clock3, UserRound } from 'lucide-react';
import type { BoardResponse, WorkOrderCard, WorkOrderStatus } from '../types';

const nextStatus: Partial<Record<WorkOrderStatus, WorkOrderStatus>> = {
  CREATED: 'QUOTED_BY_TECHNICIAN',
  QUOTED_BY_TECHNICIAN: 'PENDING_CUSTOMER_APPROVAL',
  PENDING_CUSTOMER_APPROVAL: 'PENDING_PARTS',
  PENDING_PARTS: 'READY_TO_INVOICE',
  READY_TO_INVOICE: 'INVOICED',
};

export function KanbanBoard({ board, onAdvance, onOpen }: { board: BoardResponse; onAdvance: (card: WorkOrderCard, target: WorkOrderStatus) => void; onOpen: (card: WorkOrderCard) => void }) {
  return (
    <div className="kanban" role="region" tabIndex={0} aria-label="Flujo de órdenes de trabajo">
      {board.columns.map((column) => (
        <section className={`kanban-column kanban-column--${column.status.toLowerCase()}`} key={column.status}>
          <header><div><span className="kanban-column__dot" /><h2>{column.label}</h2></div><b>{column.cards.length}</b></header>
          <div className="kanban-column__body">
            {column.cards.map((card) => (
              <article className="ot-card" key={card.id}>
                <button className="ot-card__open" type="button" aria-label={`Abrir OT ${card.external_reference}`} onClick={() => onOpen(card)}>
                <div className="ot-card__top"><code>{card.external_reference}</code>{card.promised_at && <span><Clock3 size={13} /> Promesa</span>}</div>
                <h3>{card.vehicle_label}</h3>
                <p>{card.title}</p>
                <div className="ot-card__info"><span><UserRound size={14} />{card.customer_name}</span><span><CarFront size={14} />{card.bay_code ?? 'Sin bahía'}</span></div>
                {card.technician_name && <div className="ot-card__technician">Técnico <strong>{card.technician_name}</strong></div>}
                </button>
                {nextStatus[card.status] && (
                  <button type="button" onClick={() => onAdvance(card, nextStatus[card.status]!)}>
                    Avanzar <ArrowRight size={15} />
                  </button>
                )}
              </article>
            ))}
            {column.cards.length === 0 && <div className="kanban-empty"><AlertTriangle size={18} /><span>Sin OT en esta etapa</span></div>}
          </div>
        </section>
      ))}
    </div>
  );
}
