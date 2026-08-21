def test_authenticated_client_cannot_download_nonexistent_demo_invoice(client, client_account) -> None:
    login = client.post(
        "/api/v1/client-auth/login",
        data={"username": client_account["email"], "password": client_account["password"]},
    )
    assert login.status_code == 204

    response = client.get(
        "/api/v1/client-documents/invoices/FAC-DEMO-0245.pdf",
    )
    assert response.status_code == 404


def test_invoice_pdf_rejects_missing_client_session(client) -> None:
    response = client.get("/api/v1/client-documents/invoices/FAC-DEMO-0245.pdf")
    assert response.status_code == 401
