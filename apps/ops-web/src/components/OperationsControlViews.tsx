import { useMemo, useState } from "react";
import {
  Building2,
  CheckCircle2,
  ClipboardList,
  PackageCheck,
  RotateCcw,
  Route,
  ShieldCheck,
  Truck,
  Warehouse,
} from "lucide-react";
import {
  addLeadActivity,
  addLeadSurvey,
  createBranch,
  createManagementDocument,
  createQualityCase,
  createStaffLead,
  updateLead,
  updateQualityCase,
} from "../lib/api";
import type { OperationsOverview, SalesLead } from "../types";

const FLOW_RECIPES = [
  [
    "Servicio completo",
    "Cita → recepción → diagnóstico → cotización → aprobación por línea → repuestos → trabajo → QC → caja",
  ],
  [
    "Solo diagnóstico",
    "Recepción → diagnóstico → informe → cobro → historial VIN",
  ],
  [
    "Solo repuestos",
    "Pedido → contacto Caja → confirmación → reserva → preparación → guía → tránsito → entrega",
  ],
  [
    "Devolución web",
    "Solicitud → evidencia → inspección → bodega devoluciones → resolución → historial",
  ],
  [
    "Garantía / reclamo",
    "Caso de calidad → vínculo OT/VIN → inspección → retrabajo o rechazo → cierre",
  ],
  [
    "Importación",
    "Solicitud → compra → recepción → bodega principal → reserva/venta → trazabilidad",
  ],
] as const;

export function LegacyProcessControlView({
  overview,
  token,
  onReload,
}: {
  overview: OperationsOverview;
  token: string;
  onReload: () => Promise<void>;
}) {
  const [description, setDescription] = useState("");
  const [caseType, setCaseType] = useState<
    "RETURN" | "WARRANTY" | "COMPLAINT" | "REWORK"
  >("RETURN");
  async function saveCase() {
    if (description.trim().length < 5) return;
    await createQualityCase(token, { case_type: caseType, description });
    setDescription("");
    await onReload();
  }
  return (
    <div className="control-view">
      <header className="content-header">
        <div>
          <span>Diseño y ejecución</span>
          <h1>Procesos, devoluciones y control de calidad</h1>
          <p>
            Cada combinación tiene estados, responsables y eventos auditables;
            la contabilidad final sigue en ERPNext.
          </p>
        </div>
      </header>
      <section className="flow-recipe-grid">
        {FLOW_RECIPES.map(([title, steps]) => (
          <article key={title}>
            <Route />
            <div>
              <h2>{title}</h2>
              <p>{steps}</p>
            </div>
          </article>
        ))}
      </section>
      <div className="control-columns">
        <section className="control-panel">
          <h2>
            <Warehouse /> Bodegas por estado físico
          </h2>
          {overview.warehouses.map((item) => (
            <article className="record-row" key={item.id}>
              <span>
                <b>{item.name}</b>
                <small>{item.code}</small>
              </span>
              <em>{item.warehouse_type}</em>
            </article>
          ))}
        </section>
        <section className="control-panel">
          <h2>
            <Truck /> Reservas y fletes
          </h2>
          <div className="mini-kpis">
            <b>
              {overview.reservations.length}
              <small>reservas</small>
            </b>
            <b>
              {overview.transfers.length}
              <small>movimientos</small>
            </b>
            <b>
              {overview.shipments.length}
              <small>fletes</small>
            </b>
          </div>
          {overview.shipments.slice(0, 5).map((item) => (
            <article className="record-row" key={item.id}>
              <span>
                <b>{item.number}</b>
                <small>
                  {item.carrier} · {item.tracking_number || "sin guía todavía"}
                </small>
              </span>
              <em>{item.status}</em>
            </article>
          ))}
        </section>
        <section className="control-panel quality-panel">
          <h2>
            <ShieldCheck /> Calidad y reclamos
          </h2>
          <div className="inline-form">
            <select
              aria-label="Tipo de caso de calidad"
              value={caseType}
              onChange={(event) =>
                setCaseType(event.target.value as typeof caseType)
              }
            >
              <option value="RETURN">Devolución</option>
              <option value="WARRANTY">Garantía</option>
              <option value="COMPLAINT">Reclamo</option>
              <option value="REWORK">Retrabajo</option>
            </select>
            <input
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Detalle verificable del caso"
            />
            <button onClick={() => void saveCase()}>Registrar</button>
          </div>
          {overview.quality_cases.map((item) => (
            <article className="record-row" key={item.id}>
              <span>
                <b>
                  {item.number} · {item.case_type}
                </b>
                <small>{item.description}</small>
              </span>
              <em>{item.status}</em>
            </article>
          ))}
        </section>
      </div>
    </div>
  );
}

export function ProcessControlView({
  overview,
  token,
  onReload,
}: {
  overview: OperationsOverview;
  token: string;
  onReload: () => Promise<void>;
}) {
  const [description, setDescription] = useState("");
  const [caseType, setCaseType] = useState<
    "RETURN" | "WARRANTY" | "COMPLAINT" | "REWORK"
  >("RETURN");
  const next: Record<string, string> = {
    OPEN: "INSPECTING",
    INSPECTING: "APPROVED",
    APPROVED: "RESOLVED",
    REJECTED: "CLOSED",
    RESOLVED: "CLOSED",
  };
  async function saveCase() {
    if (description.trim().length < 5) return;
    await createQualityCase(token, { case_type: caseType, description });
    setDescription("");
    await onReload();
  }
  async function advance(item: OperationsOverview["quality_cases"][number]) {
    const target = next[item.status];
    if (!target) return;
    const resolution = ["RESOLVED", "CLOSED"].includes(target)
      ? window.prompt("Resolucion verificable:", item.resolution || "") || ""
      : undefined;
    if (["RESOLVED", "CLOSED"].includes(target) && !resolution) return;
    await updateQualityCase(token, item.id, target, resolution);
    await onReload();
  }
  return (
    <div className="control-view">
      <header className="content-header">
        <div>
          <span>Ejecucion y calidad</span>
          <h1>Procesos, devoluciones y control de calidad</h1>
          <p>
            Los mapas describen el flujo y los casos avanzan con estados,
            responsable y resolucion.
          </p>
        </div>
      </header>
      <section className="flow-recipe-grid">
        {FLOW_RECIPES.map(([title, steps]) => (
          <article key={title}>
            <Route />
            <div>
              <h2>{title}</h2>
              <p>{steps}</p>
            </div>
          </article>
        ))}
      </section>
      <section className="control-panel">
        <h2>
          <ShieldCheck /> Nuevo caso
        </h2>
        <div className="inline-form">
          <select
            aria-label="Tipo de caso de calidad"
            value={caseType}
            onChange={(e) => setCaseType(e.target.value as typeof caseType)}
          >
            <option value="RETURN">Devolucion</option>
            <option value="WARRANTY">Garantia</option>
            <option value="COMPLAINT">Reclamo</option>
            <option value="REWORK">Retrabajo</option>
          </select>
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Descripcion verificable"
          />
          <button onClick={() => void saveCase()}>Registrar</button>
        </div>
      </section>
      <div className="quality-kanban">
        {[
          "OPEN",
          "INSPECTING",
          "APPROVED",
          "REJECTED",
          "RESOLVED",
          "CLOSED",
        ].map((status) => (
          <section key={status}>
            <header>
              <h2>{status}</h2>
              <b>
                {
                  overview.quality_cases.filter(
                    (item) => item.status === status,
                  ).length
                }
              </b>
            </header>
            {overview.quality_cases
              .filter((item) => item.status === status)
              .map((item) => (
                <article key={item.id}>
                  <small>
                    {item.number} · {item.case_type}
                  </small>
                  <p>{item.description}</p>
                  {item.resolution && <em>{item.resolution}</em>}
                  {next[item.status] && (
                    <button onClick={() => void advance(item)}>
                      Pasar a {next[item.status]}
                    </button>
                  )}
                </article>
              ))}
          </section>
        ))}
      </div>
    </div>
  );
}

const LEAD_COLUMNS: Array<{ status: SalesLead["status"]; label: string }> = [
  { status: "NEW", label: "Nuevos" },
  { status: "QUALIFYING", label: "Calificando" },
  { status: "ADVISOR", label: "Con asesor" },
  { status: "QUOTED", label: "Cotizados" },
  { status: "WON", label: "Ganados" },
  { status: "LOST", label: "No concretados" },
];

export function LegacyLeadsKanbanView({
  overview,
  token,
  onReload,
}: {
  overview: OperationsOverview;
  token: string;
  onReload: () => Promise<void>;
}) {
  async function move(lead: SalesLead, status: SalesLead["status"]) {
    await updateLead(
      token,
      lead.id,
      status,
      status === "ADVISOR" ? "María - asesora" : lead.assigned_to || undefined,
    );
    await onReload();
  }
  return (
    <div className="control-view">
      <header className="content-header">
        <div>
          <span>CRM y asistente</span>
          <h1>Seguimiento de interesados</h1>
          <p>
            La IA captura nombre, teléfono, interés y vehículo; el equipo
            continúa la conversación y mide la conversión.
          </p>
        </div>
      </header>
      <div className="lead-board">
        {LEAD_COLUMNS.map((column, index) => (
          <section key={column.status}>
            <header>
              <h2>{column.label}</h2>
              <b>
                {
                  overview.leads.filter((lead) => lead.status === column.status)
                    .length
                }
              </b>
            </header>
            {overview.leads
              .filter((lead) => lead.status === column.status)
              .map((lead) => (
                <article key={lead.id}>
                  <small>
                    {lead.number} · {lead.source}
                  </small>
                  <h3>{lead.full_name}</h3>
                  <a
                    href={`https://wa.me/${lead.phone.replace(/\D/g, "")}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {lead.phone}
                  </a>
                  <p>{lead.interest}</p>
                  {lead.vehicle_summary && <span>{lead.vehicle_summary}</span>}
                  <footer>
                    {index > 0 && (
                      <button
                        onClick={() =>
                          void move(lead, LEAD_COLUMNS[index - 1].status)
                        }
                      >
                        ←
                      </button>
                    )}
                    {index < LEAD_COLUMNS.length - 1 && (
                      <button
                        onClick={() =>
                          void move(lead, LEAD_COLUMNS[index + 1].status)
                        }
                      >
                        Avanzar →
                      </button>
                    )}
                  </footer>
                </article>
              ))}
          </section>
        ))}
      </div>
    </div>
  );
}

export function LeadsKanbanView({
  overview,
  token,
  onReload,
}: {
  overview: OperationsOverview;
  token: string;
  onReload: () => Promise<void>;
}) {
  const [selected, setSelected] = useState<SalesLead | null>(null);
  const [draft, setDraft] = useState({
    full_name: "",
    phone: "",
    email: "",
    interest: "",
    vehicle_summary: "",
    source: "WALK_IN",
  });
  const [activity, setActivity] = useState("");
  const [survey, setSurvey] = useState("");
  async function createLead(event: React.FormEvent) {
    event.preventDefault();
    await createStaffLead(token, {
      ...draft,
      email: draft.email || undefined,
      vehicle_summary: draft.vehicle_summary || undefined,
    });
    setDraft({
      full_name: "",
      phone: "",
      email: "",
      interest: "",
      vehicle_summary: "",
      source: "WALK_IN",
    });
    await onReload();
  }
  async function move(lead: SalesLead, status: SalesLead["status"]) {
    await updateLead(
      token,
      lead.id,
      status,
      status === "ADVISOR" ? "Maria - asesora" : lead.assigned_to || undefined,
    );
    await onReload();
  }
  async function saveActivity() {
    if (!selected || activity.trim().length < 3) return;
    await addLeadActivity(token, selected.id, {
      activity_type: "FOLLOW_UP",
      content: activity,
    });
    setActivity("");
  }
  async function saveSurvey() {
    if (!selected || survey.trim().length < 3) return;
    await addLeadSurvey(token, selected.id, "Encuesta de interes", {
      respuesta: survey,
    });
    setSurvey("");
  }
  return (
    <div className="control-view">
      <header className="content-header">
        <div>
          <span>CRM operativo</span>
          <h1>Prospeccion, seguimiento y encuestas</h1>
          <p>
            Capture interesados, registre cada contacto y mueva la oportunidad
            hasta venta ganada o perdida.
          </p>
        </div>
      </header>
      <form className="control-panel lead-entry" onSubmit={createLead}>
        <h2>Ingresar lead</h2>
        <input
          required
          placeholder="Nombre"
          value={draft.full_name}
          onChange={(e) => setDraft({ ...draft, full_name: e.target.value })}
        />
        <input
          required
          placeholder="Telefono"
          value={draft.phone}
          onChange={(e) => setDraft({ ...draft, phone: e.target.value })}
        />
        <input
          type="email"
          placeholder="Correo"
          value={draft.email}
          onChange={(e) => setDraft({ ...draft, email: e.target.value })}
        />
        <input
          required
          placeholder="Que le interesa"
          value={draft.interest}
          onChange={(e) => setDraft({ ...draft, interest: e.target.value })}
        />
        <input
          placeholder="Vehiculo"
          value={draft.vehicle_summary}
          onChange={(e) =>
            setDraft({ ...draft, vehicle_summary: e.target.value })
          }
        />
        <select
          aria-label="Origen del lead"
          value={draft.source}
          onChange={(e) => setDraft({ ...draft, source: e.target.value })}
        >
          <option value="WALK_IN">Visita</option>
          <option value="PHONE">Telefono</option>
          <option value="WHATSAPP">WhatsApp</option>
          <option value="LANDING">Landing</option>
          <option value="AI_CHAT">IA</option>
        </select>
        <button className="role-primary">Guardar lead</button>
      </form>
      <div className="lead-board">
        {LEAD_COLUMNS.map((column, index) => (
          <section key={column.status}>
            <header>
              <h2>{column.label}</h2>
              <b>
                {
                  overview.leads.filter((lead) => lead.status === column.status)
                    .length
                }
              </b>
            </header>
            {overview.leads
              .filter((lead) => lead.status === column.status)
              .map((lead) => (
                <article
                  className={selected?.id === lead.id ? "active" : ""}
                  key={lead.id}
                  onClick={() => setSelected(lead)}
                >
                  <small>
                    {lead.number} · {lead.source}
                  </small>
                  <h3>{lead.full_name}</h3>
                  <a
                    href={`https://wa.me/${lead.phone.replace(/\D/g, "")}`}
                    target="_blank"
                    rel="noreferrer"
                    onClick={(event) => event.stopPropagation()}
                  >
                    {lead.phone}
                  </a>
                  <p>{lead.interest}</p>
                  <footer>
                    {index > 0 && (
                      <button
                        onClick={(event) => {
                          event.stopPropagation();
                          void move(lead, LEAD_COLUMNS[index - 1].status);
                        }}
                      >
                        ←
                      </button>
                    )}
                    {index < LEAD_COLUMNS.length - 1 && (
                      <button
                        onClick={(event) => {
                          event.stopPropagation();
                          void move(lead, LEAD_COLUMNS[index + 1].status);
                        }}
                      >
                        Avanzar →
                      </button>
                    )}
                  </footer>
                </article>
              ))}
          </section>
        ))}
      </div>
      {selected && (
        <section className="control-panel lead-workspace">
          <h2>Seguimiento de {selected.full_name}</h2>
          <div>
            <input
              value={activity}
              onChange={(e) => setActivity(e.target.value)}
              placeholder="Llamada, mensaje, propuesta o proximo paso"
            />
            <button onClick={() => void saveActivity()}>
              Registrar contacto
            </button>
          </div>
          <div>
            <input
              value={survey}
              onChange={(e) => setSurvey(e.target.value)}
              placeholder="Respuesta de encuesta o satisfaccion"
            />
            <button onClick={() => void saveSurvey()}>Guardar encuesta</button>
          </div>
          <a
            href={`https://wa.me/${selected.phone.replace(/\D/g, "")}`}
            target="_blank"
            rel="noreferrer"
          >
            Enviar mensaje por WhatsApp
          </a>
        </section>
      )}
    </div>
  );
}

export function ManagementView({
  overview,
  token,
  onReload,
}: {
  overview: OperationsOverview;
  token: string;
  onReload: () => Promise<void>;
}) {
  const branch = overview.branches[0];
  const [branchName, setBranchName] = useState("");
  const [branchCode, setBranchCode] = useState("");
  const [docType, setDocType] = useState("CAI");
  const [docNumber, setDocNumber] = useState("");
  const activeCai = useMemo(
    () =>
      overview.management_documents.filter(
        (item) => item.document_type === "CAI" && item.status === "ACTIVE",
      ).length,
    [overview],
  );
  async function addBranch() {
    if (!branchName || !branchCode) return;
    await createBranch(token, {
      code: branchCode.toUpperCase(),
      name: branchName,
    });
    setBranchName("");
    setBranchCode("");
    await onReload();
  }
  async function addDocument() {
    if (!branch || !docNumber) return;
    await createManagementDocument(token, {
      branch_id: branch.id,
      document_type: docType,
      number: docNumber,
      status: "ACTIVE",
    });
    setDocNumber("");
    await onReload();
  }
  return (
    <div className="control-view">
      <header className="content-header">
        <div>
          <span>Gerencia y configuración</span>
          <h1>Empresa, sucursales y documentos</h1>
          <p>
            Configuración visual preparada para CAI, formatos, correo
            corporativo y documentos gerenciales.
          </p>
        </div>
      </header>
      <div className="management-kpis">
        <article>
          <Building2 />
          <b>
            {overview.branches.length}
            <small>sucursales</small>
          </b>
        </article>
        <article>
          <ClipboardList />
          <b>
            {overview.management_documents.length}
            <small>formatos</small>
          </b>
        </article>
        <article>
          <CheckCircle2 />
          <b>
            {activeCai}
            <small>CAI activo</small>
          </b>
        </article>
        <article>
          <PackageCheck />
          <b>
            4<small>tipos de bodega</small>
          </b>
        </article>
      </div>
      <div className="control-columns">
        <section className="control-panel">
          <h2>Sucursales</h2>
          {overview.branches.map((item) => (
            <article className="record-row" key={item.id}>
              <span>
                <b>{item.name}</b>
                <small>
                  {item.code} · {item.email_domain || "sin dominio"}
                </small>
              </span>
              <em>{item.active ? "ACTIVA" : "INACTIVA"}</em>
            </article>
          ))}
          <div className="inline-form">
            <input
              value={branchCode}
              onChange={(event) => setBranchCode(event.target.value)}
              placeholder="Código"
            />
            <input
              value={branchName}
              onChange={(event) => setBranchName(event.target.value)}
              placeholder="Nombre sucursal"
            />
            <button onClick={() => void addBranch()}>Agregar</button>
          </div>
        </section>
        <section className="control-panel">
          <h2>CAI, facturas y plantillas</h2>
          {overview.management_documents.map((item) => (
            <article className="record-row" key={item.id}>
              <span>
                <b>{item.document_type}</b>
                <small>{item.number}</small>
              </span>
              <em>{item.status}</em>
            </article>
          ))}
          <div className="inline-form">
            <select
              aria-label="Tipo de documento administrativo"
              value={docType}
              onChange={(event) => setDocType(event.target.value)}
            >
              <option>CAI</option>
              <option>INVOICE_TEMPLATE</option>
              <option>QUOTE_TEMPLATE</option>
              <option>PROFORMA</option>
              <option>LETTER</option>
              <option>EMAIL_TEMPLATE</option>
            </select>
            <input
              value={docNumber}
              onChange={(event) => setDocNumber(event.target.value)}
              placeholder="Número o nombre"
            />
            <button onClick={() => void addDocument()}>Guardar</button>
          </div>
        </section>
        <section className="control-panel">
          <h2>Servicios corporativos</h2>
          {[
            ["Correo SmartDiag504", "Dominio y buzones por usuario"],
            ["Mensajes y cartas", "Plantillas con identidad de marca"],
            ["Facturación", "CAI, rangos y vencimientos"],
            ["Alta disponibilidad", "Diseño de dos nodos y failover probado"],
          ].map(([name, note]) => (
            <article className="record-row" key={name}>
              <span>
                <b>{name}</b>
                <small>{note}</small>
              </span>
              <em>FEATURE</em>
            </article>
          ))}
        </section>
      </div>
    </div>
  );
}
