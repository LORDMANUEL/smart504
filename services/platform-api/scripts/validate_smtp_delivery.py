from __future__ import annotations

import os
from types import SimpleNamespace

from app.config import get_settings
from app.services.notifications import _send_email


def main() -> None:
    """Send a bounded message to a local mailbox; never target a customer by default."""
    recipient = os.getenv("SMTP_VALIDATION_RECIPIENT", "root@localhost")
    if recipient != "root@localhost" and not os.getenv("ALLOW_EXTERNAL_SMTP_VALIDATION"):
        raise SystemExit("External SMTP validation requires explicit ALLOW_EXTERNAL_SMTP_VALIDATION")
    reference = _send_email(
        SimpleNamespace(
            id="smtp-validation",
            recipient=recipient,
            subject="Validacion SMTP SmartDiag504",
            body_text="Entrega local de prueba desde el worker SmartDiag504.",
        ),
        get_settings(),
    )
    print({"status": "PASS", "recipient": recipient, "reference": reference})


if __name__ == "__main__":
    main()
