app_name = "smartdiag_workshop"
app_title = "SmartDiag504 Workshop"
app_publisher = "SmartDiag504"
app_description = "Automotive workshop domain for ERPNext and Beveren FSM"
app_email = "tecnologia@smartdiag504.com"
app_license = "GPL-3.0-or-later"

required_apps = ["erpnext", "beveren_fsm"]

after_install = "smartdiag_workshop.setup.install.after_install"
after_migrate = "smartdiag_workshop.setup.install.after_migrate"

add_to_apps_screen = [
    {
        "name": "smartdiag_workshop",
        "logo": "/assets/smartdiag_workshop/smartdiag-mark.svg",
        "title": "SmartDiag504",
        "route": "/app/smartdiag-workshop",
    }
]

app_include_css = ["/assets/smartdiag_workshop/css/smartdiag.css?v=0.4.0-erp6"]
app_include_js = ["/assets/smartdiag_workshop/js/smartdiag.js?v=0.4.0-erp6"]

scheduler_events = {
    "cron": {
        "*/5 * * * *": ["smartdiag_workshop.events.outbox.publish_pending_events"],
        "0 5 * * *": ["smartdiag_workshop.events.maintenance.create_due_notifications"],
    }
}

doc_events = {
    "Service Order": {
        "validate": "smartdiag_workshop.events.service_order.validate_service_order",
        "after_insert": "smartdiag_workshop.events.service_order.after_insert",
        "on_update": "smartdiag_workshop.events.service_order.on_update",
        "on_submit": "smartdiag_workshop.events.service_order.on_submit",
        "on_cancel": "smartdiag_workshop.events.service_order.on_cancel",
    },
    "Service Quotation": {
        "on_update": "smartdiag_workshop.events.service_order.on_quotation_update",
        "on_submit": "smartdiag_workshop.events.service_order.on_quotation_submit",
    },
    "Sales Invoice": {
        "on_submit": "smartdiag_workshop.events.erp_documents.on_sales_invoice_submit",
        "on_cancel": "smartdiag_workshop.events.erp_documents.on_sales_invoice_cancel",
    },
    "Stock Entry": {
        "on_submit": "smartdiag_workshop.events.erp_documents.on_stock_entry_submit",
    },
}

website_route_rules = [
    {"from_route": "/smartdiag/api/catalog/<path:app_path>", "to_route": "smartdiag/api/catalog"},
]
