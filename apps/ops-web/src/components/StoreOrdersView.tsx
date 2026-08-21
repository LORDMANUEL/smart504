import { useEffect, useMemo, useState } from "react";
import {
  CircleDollarSign,
  ClipboardCheck,
  PackageCheck,
  Phone,
  RefreshCw,
  ShoppingCart,
  UserRound,
  X,
} from "lucide-react";
import type { StoreOrder, StoreOrderStatus } from "../types";
import { uploadStorePaymentProof } from "../lib/api";

const STATUS_LABELS: Record<StoreOrderStatus, string> = {
  PENDING_CONFIRMATION: "Pendiente de confirmación",
  CONTACTED: "Cliente contactado",
  CONFIRMED: "Pedido confirmado",
  PAID: "Pagado",
  RESERVED: "Repuesto reservado",
  PREPARING: "Preparando en bodega",
  SHIPPED: "Enviado con guía",
  DELIVERED: "Entregado",
  RETURN_REQUESTED: "Devolución solicitada",
  RETURNED: "Devuelto",
  SYNCED: "Sincronizado con ERPNext",
  NO_RESPONSE: "No respondió",
  LOST: "Venta perdida",
  CANCELLED: "Cancelado",
};
const STATUS_OPTIONS = Object.entries(STATUS_LABELS) as Array<
  [StoreOrderStatus, string]
>;
const COLUMNS: Array<{
  id: string;
  label: string;
  statuses: StoreOrderStatus[];
}> = [
  { id: "entered", label: "Entrado", statuses: ["PENDING_CONFIRMATION"] },
  { id: "answered", label: "Contestado", statuses: ["CONTACTED", "CONFIRMED"] },
  { id: "paid", label: "Pagado", statuses: ["PAID", "RESERVED", "PREPARING"] },
  { id: "shipped", label: "Enviado", statuses: ["SHIPPED"] },
  {
    id: "returned",
    label: "Devuelto",
    statuses: ["RETURN_REQUESTED", "RETURNED"],
  },
  { id: "no-response", label: "No contestó", statuses: ["NO_RESPONSE"] },
  { id: "won", label: "Venta hecha", statuses: ["DELIVERED", "SYNCED"] },
  { id: "lost", label: "Venta perdida", statuses: ["LOST", "CANCELLED"] },
];
type Draft = {
  status: StoreOrderStatus;
  erpnextReference: string;
  error: string;
};
type Props = {
  token?: string;
  orders: StoreOrder[];
  busy: boolean;
  onStatusChange: (
    order: StoreOrder,
    status: StoreOrderStatus,
    erpnextReference?: string,
  ) => Promise<void> | void;
  onReload?: () => Promise<void> | void;
};
const money = (value: string, currency: string) =>
  new Intl.NumberFormat("es-HN", { style: "currency", currency }).format(
    Number(value),
  );
const makeDraft = (order: StoreOrder): Draft => ({
  status: order.status,
  erpnextReference: order.erpnext_sales_order_id ?? "",
  error: "",
});

export function StoreOrdersView({
  token = "",
  orders,
  busy,
  onStatusChange,
  onReload,
}: Props) {
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [proofMessage, setProofMessage] = useState("");
  const selected = orders.find((item) => item.id === selectedId) ?? null;
  useEffect(
    () =>
      setDrafts((current) =>
        Object.fromEntries(
          orders.map((order) => [
            order.id,
            current[order.id] ?? makeDraft(order),
          ]),
        ),
      ),
    [orders],
  );
  const summary = useMemo(
    () => ({
      pending: orders.filter((order) => order.status === "PENDING_CONFIRMATION")
        .length,
      won: orders.filter((order) =>
        ["DELIVERED", "SYNCED"].includes(order.status),
      ).length,
      value: orders
        .filter((order) => !["LOST", "CANCELLED"].includes(order.status))
        .reduce((sum, order) => sum + Number(order.subtotal), 0),
    }),
    [orders],
  );
  function updateDraft(orderId: string, patch: Partial<Draft>) {
    setDrafts((current) => ({
      ...current,
      [orderId]: {
        ...(current[orderId] ?? {
          status: "PENDING_CONFIRMATION",
          erpnextReference: "",
          error: "",
        }),
        ...patch,
      },
    }));
  }
  async function save(order: StoreOrder) {
    const draft = drafts[order.id] ?? makeDraft(order);
    if (draft.status === "SYNCED" && !draft.erpnextReference.trim()) {
      updateDraft(order.id, {
        error:
          "Ingrese la orden de venta de ERPNext antes de marcar el pedido como sincronizado.",
      });
      return;
    }
    updateDraft(order.id, { error: "" });
    await onStatusChange(
      order,
      draft.status,
      draft.erpnextReference.trim() || undefined,
    );
  }
  async function saveProof(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = new FormData(event.currentTarget);
    const file = form.get("proof");
    if (!(file instanceof File) || !file.size) {
      setProofMessage("Seleccione un PDF, JPG o PNG.");
      return;
    }
    try {
      const proof = await uploadStorePaymentProof(
        token,
        selected.id,
        file,
        String(form.get("reference")),
        String(form.get("amount")),
      );
      setProofMessage(`Comprobante ${proof.reference} guardado.`);
      event.currentTarget.reset();
    } catch (error) {
      setProofMessage(
        error instanceof Error ? error.message : "No se pudo guardar.",
      );
    }
  }
  return (
    <div className="store-orders">
      <header className="content-header">
        <div>
          <span>Venta digital</span>
          <h1>Kanban de pedidos</h1>
          <p>
            Seguimiento desde la solicitud hasta la venta, envío, devolución o
            pérdida.
          </p>
        </div>
        {onReload && (
          <button
            className="secondary-action"
            onClick={() => void onReload()}
            disabled={busy}
          >
            <RefreshCw size={17} /> Actualizar
          </button>
        )}
      </header>
      <div className="store-order-summary">
        <div>
          <ShoppingCart />
          <p>
            <small>Entrados</small>
            <strong>{summary.pending}</strong>
          </p>
        </div>
        <div>
          <PackageCheck />
          <p>
            <small>Ventas hechas</small>
            <strong>{summary.won}</strong>
          </p>
        </div>
        <div>
          <CircleDollarSign />
          <p>
            <small>Valor en flujo</small>
            <strong>{money(String(summary.value), "HNL")}</strong>
          </p>
        </div>
      </div>
      {!orders.length && (
        <div className="disabled-feature">
          <ShoppingCart />
          <h2>Sin pedidos web</h2>
          <p>
            Los pedidos aparecerán después de que un cliente envíe su carrito.
          </p>
        </div>
      )}
      <div className="orders-kanban">
        {COLUMNS.map((column) => {
          const items = orders.filter((order) =>
            column.statuses.includes(order.status),
          );
          return (
            <section className="orders-column" key={column.id}>
              <header>
                <h2>{column.label}</h2>
                <b>{items.length}</b>
              </header>
              <div>
                {items.map((order) => (
                  <button
                    className="order-kanban-card"
                    onClick={() => setSelectedId(order.id)}
                    key={order.id}
                  >
                    <small>
                      {new Date(order.created_at).toLocaleDateString("es-HN")}
                    </small>
                    <strong>{order.order_number}</strong>
                    <span>{order.customer_name}</span>
                    <p>
                      {order.items
                        .slice(0, 2)
                        .map((item) => `${item.quantity} × ${item.name}`)
                        .join(", ")}
                    </p>
                    <footer>
                      <em>{STATUS_LABELS[order.status]}</em>
                      <b>{money(order.subtotal, order.currency)}</b>
                    </footer>
                  </button>
                ))}
              </div>
            </section>
          );
        })}
      </div>
      {selected && (
        <div
          className="order-detail-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setSelectedId(null);
          }}
        >
          <aside
            className="order-detail"
            role="dialog"
            aria-modal="true"
            aria-label={`Pedido ${selected.order_number}`}
          >
            <header>
              <div>
                <small>Pedido web</small>
                <h2>{selected.order_number}</h2>
              </div>
              <button
                aria-label="Cerrar detalle"
                onClick={() => setSelectedId(null)}
              >
                <X />
              </button>
            </header>
            <div className="order-detail-body">
              <section className="store-order-customer">
                <div>
                  <UserRound />
                  <p>
                    <small>Cliente</small>
                    <strong>{selected.customer_name}</strong>
                  </p>
                </div>
                <div>
                  <Phone />
                  <p>
                    <small>Contacto</small>
                    <strong>{selected.phone}</strong>
                    {selected.email && <span>{selected.email}</span>}
                  </p>
                </div>
                <div>
                  <ClipboardCheck />
                  <p>
                    <small>Caja responsable</small>
                    <strong>
                      {selected.assigned_cashier || "Caja principal"}
                    </strong>
                    <span>
                      WhatsApp: {selected.whatsapp_status || "PENDING"}
                    </span>
                  </p>
                </div>
              </section>
              <section className="store-order-lines">
                <h3>Repuestos solicitados</h3>
                {selected.items.map((item) => (
                  <div key={item.id}>
                    <p>
                      <strong>
                        {item.quantity} × {item.name}
                      </strong>
                      <small>
                        {item.sku} · {money(item.unit_price, selected.currency)}{" "}
                        c/u
                      </small>
                    </p>
                    <b>{money(item.line_total, selected.currency)}</b>
                  </div>
                ))}
                <footer>
                  <span>Subtotal web</span>
                  <strong>{money(selected.subtotal, selected.currency)}</strong>
                </footer>
              </section>
              {selected.notes && (
                <p className="store-order-note">
                  <strong>Nota:</strong> {selected.notes}
                </p>
              )}
              <form
                className="store-payment-proof"
                onSubmit={(event) => void saveProof(event)}
              >
                <h3>Comprobante de pago</h3>
                <p>
                  Si no hay pasarela, registre el pago con evidencia privada y
                  auditable.
                </p>
                <label>
                  Referencia
                  <input
                    name="reference"
                    required
                    placeholder="Transferencia, depósito o recibo"
                  />
                </label>
                <label>
                  Monto
                  <input
                    name="amount"
                    required
                    type="number"
                    min="0.01"
                    step="0.01"
                    defaultValue={selected.subtotal}
                  />
                </label>
                <label>
                  Archivo PDF, JPG o PNG
                  <input
                    name="proof"
                    required
                    type="file"
                    accept="application/pdf,image/jpeg,image/png"
                  />
                </label>
                <button className="secondary-action" type="submit">
                  Guardar comprobante
                </button>
                {proofMessage && <p role="status">{proofMessage}</p>}
              </form>
              <footer className="store-order-actions">
                <label>
                  Estado de {selected.order_number}
                  <select
                    aria-label={`Estado de ${selected.order_number}`}
                    value={(drafts[selected.id] ?? makeDraft(selected)).status}
                    onChange={(event) =>
                      updateDraft(selected.id, {
                        status: event.target.value as StoreOrderStatus,
                        error: "",
                      })
                    }
                  >
                    {STATUS_OPTIONS.map(([value, label]) => (
                      <option value={value} key={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                {(drafts[selected.id] ?? makeDraft(selected)).status ===
                  "SYNCED" && (
                  <label>
                    Orden de venta ERPNext
                    <input
                      value={
                        (drafts[selected.id] ?? makeDraft(selected))
                          .erpnextReference
                      }
                      onChange={(event) =>
                        updateDraft(selected.id, {
                          erpnextReference: event.target.value,
                          error: "",
                        })
                      }
                    />
                  </label>
                )}
                <button
                  className="primary-action"
                  disabled={busy}
                  onClick={() => void save(selected)}
                >
                  Guardar estado
                </button>
                {(drafts[selected.id] ?? makeDraft(selected)).error && (
                  <p role="alert">
                    {(drafts[selected.id] ?? makeDraft(selected)).error}
                  </p>
                )}
              </footer>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
