# Beveren FSM compatibility status

- Upstream repository: `Beveren-Software-Inc/Field_Service_Management`
- Upstream commit: `ab6d56d1069882326475f256d09cc63236eddec1`
- Patch SHA256: `828350ae82cea4ea182678b84965a78df6343d3929c67ec185791fe055299a58`
- Target: Frappe/ERPNext `version-16`

The patch declares ERPNext as a required application, fixes Address/Contact link queries,
registers a valid app tile and makes `Service Order` and `Service Quotation` inherit
ERPNext's `SellingController`. That inheritance supplies `process_item_selection`, which
is the compatibility repair tracked by upstream Issue #24.

The Docker build checks out the pinned commit in detached mode and applies this patch. A
fresh-site installation plus creation of a Service Order with parts remains a mandatory
integration gate before any production rollout.
