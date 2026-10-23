from fastapi.testclient import TestClient
from src.main import create_app


def test_health_and_unknown_order(guest):
    with guest as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        assert client.get("/api/orders").json() == []
        assert client.get("/api/orders/unknown").status_code == 404


def test_frontend_deep_links_preserve_api_404(tmp_path):
    (tmp_path / "index.html").write_text("<main>app shell</main>")
    with TestClient(create_app(tmp_path)) as client:
        assert "app shell" in client.get("/orders/example/review").text
        assert client.get("/api/missing").status_code == 404
