frappe.provide("smartdiag504");
smartdiag504.version = "0.4.0";

document.documentElement.dataset.smartdiag = "504";

smartdiag504.renderHomeButton = function () {
  const route = frappe.get_route?.() || [];
  const isSmartDiagHome = route[0] === "smartdiag-workshop";
  let button = document.querySelector(".smartdiag-global-home");
  if (isSmartDiagHome) {
    button?.remove();
    return;
  }
  if (!button) {
    button = document.createElement("button");
    button.type = "button";
    button.className = "smartdiag-global-home";
    button.setAttribute("aria-label", __("Volver al centro SmartDiag504"));
    button.innerHTML = `<span aria-hidden="true">←</span><b>${__("Volver a SmartDiag504")}</b>`;
    button.addEventListener("click", () => frappe.set_route("smartdiag-workshop"));
    document.body.appendChild(button);
  }
};

smartdiag504.installHomeButton = function () {
  if (smartdiag504.homeButtonInstalled) return;
  smartdiag504.homeButtonInstalled = true;
  const refreshHomeButton = () => window.requestAnimationFrame(() => smartdiag504.renderHomeButton());
  refreshHomeButton();
  frappe.router?.on?.("change", refreshHomeButton);
  $(document).on("page-change", refreshHomeButton);
  window.addEventListener("hashchange", refreshHomeButton);
  window.addEventListener("popstate", refreshHomeButton);
};

smartdiag504.installHomeButton();
