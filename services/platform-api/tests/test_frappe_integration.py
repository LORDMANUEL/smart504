from __future__ import annotations

import httpx
import pytest
from fastapi import HTTPException
from pydantic import SecretStr

from app.config import Settings
from app.services.frappe import FrappeReadClient


class FakeClient:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url, params=None):
        request = httpx.Request("GET", url)
        return httpx.Response(404, request=request, json={"exc_type": "DoesNotExistError"})


def test_missing_erpnext_invoice_is_a_business_conflict(monkeypatch) -> None:
    monkeypatch.setattr(httpx, "Client", FakeClient)
    client = FrappeReadClient(
        Settings(
            frappe_base_url="http://erp.local",
            frappe_api_key=SecretStr("key"),
            frappe_api_secret=SecretStr("secret"),
        )
    )
    with pytest.raises(HTTPException) as error:
        client.verify_submitted_sales_invoice("ACC-SINV-MISSING")
    assert error.value.status_code == 409
    assert "does not exist" in error.value.detail
