from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health_devuelve_ok():
    """El endpoint /health debe confirmar que el servicio está activo."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_hello_devuelve_mensaje_esperado():
    """El endpoint /hello debe devolver el mensaje de saludo."""
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from Kubernetes!"}


def test_ruta_inexistente_devuelve_404():
    """Cualquier ruta no definida debe responder 404."""
    response = client.get("/ruta-que-no-existe")
    assert response.status_code == 404
