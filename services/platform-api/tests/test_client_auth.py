def test_client_login_rejects_arbitrary_credentials(client) -> None:
    response = client.post(
        "/api/v1/client-auth/login",
        data={"username": "intruso@example.com", "password": "cualquier-password"},
    )
    assert response.status_code == 400


def test_client_login_uses_http_only_cookie(client, client_account) -> None:
    response = client.post("/api/v1/client-auth/login", data={
        "username": client_account["email"], "password": client_account["password"],
    })
    assert response.status_code == 204
    cookie = response.headers["set-cookie"]
    assert "smartdiag_client_session=" in cookie
    assert "HttpOnly" in cookie
    assert client.get("/api/v1/client-auth/session").status_code == 200
    assert client.post("/api/v1/client-auth/revoke-sessions").status_code == 200
    assert client.get("/api/v1/client-auth/session").status_code == 401
