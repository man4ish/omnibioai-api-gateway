def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_no_auth_required(client):
    # /health is in the middleware skip-list; no Authorization header needed.
    resp = client.get("/health")
    assert resp.status_code == 200
