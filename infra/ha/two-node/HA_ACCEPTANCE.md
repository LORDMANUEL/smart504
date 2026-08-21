# Acta de aceptación de alta disponibilidad

- [ ] Las tres instancias etcd tienen quorum 2/3.
- [ ] Patroni identifica exactamente un primario PostgreSQL.
- [ ] Galera reporta `wsrep_cluster_size=2` y `Primary`, con `garbd` conectado.
- [ ] Las escrituras de prueba aparecen en el nodo réplica PostgreSQL.
- [ ] Las escrituras de prueba aparecen en ambos nodos Galera.
- [ ] La pérdida de VPS A mueve el VIP a B sin intervención manual.
- [ ] La pérdida de VPS B conserva servicio en A.
- [ ] Una partición A↔B no genera dos primarios.
- [ ] El testigo caído no produce split-brain; se documenta la degradación.
- [ ] Solo el MASTER ejecuta scheduler y workers Frappe.
- [ ] El worker de alertas activo posee un fencing token vigente.
- [ ] Las fotografías subidas desde A se leen desde B.
- [ ] Se restaura un backup en un entorno vacío y se valida una OT y una factura.
- [ ] Se mide RTO y RPO reales y se firman por el responsable técnico.
