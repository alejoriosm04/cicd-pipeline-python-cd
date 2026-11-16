# tests/test_app.py
import pytest
from app.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_index_get(client):
    response = client.get("/")
    assert response.status_code == 200
    assert (
        b"<!DOCTYPE html>" in response.data
    )  # Assuming the HTML template starts with <!DOCTYPE html>


def test_index_post_sumar(client):
    response = client.post("/", data={"num1": "2", "num2": "3", "operacion": "sumar"})
    assert response.status_code == 200
    assert b"Resultado: 5.0" in response.data


def test_index_post_restar(client):
    response = client.post("/", data={"num1": "5", "num2": "3", "operacion": "restar"})
    assert response.status_code == 200
    assert b"Resultado: 2.0" in response.data


def test_index_post_multiplicar(client):
    response = client.post(
        "/", data={"num1": "2", "num2": "3", "operacion": "multiplicar"}
    )
    assert response.status_code == 200
    assert b"Resultado: 6.0" in response.data


def test_index_post_dividir(client):
    response = client.post("/", data={"num1": "6", "num2": "3", "operacion": "dividir"})
    assert response.status_code == 200
    assert b"Resultado: 2.0" in response.data


def test_index_post_dividir_by_zero(client):
    response = client.post("/", data={"num1": "6", "num2": "0", "operacion": "dividir"})
    assert response.status_code == 200
    assert b"Error: No se puede dividir por cero" in response.data


def test_index_post_invalid_operation(client):
    response = client.post("/", data={"num1": "6", "num2": "3", "operacion": "invalid"})
    assert response.status_code == 200
    assert b"Operaci\xc3\xb3n no v\xc3\xa1lida" in response.data


def test_index_post_invalid_numbers(client):
    response = client.post("/", data={"num1": "a", "num2": "b", "operacion": "sumar"})
    assert response.status_code == 200
    assert b"Error: Introduce n\xc3\xbameros v\xc3\xa1lidos" in response.data


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "version": "local"}


@pytest.mark.parametrize(
    "operacion, num1, num2, esperado",
    [
        ("potencia", "2", "3", "8.0"),
        ("potencia", "2", "-2", "0.25"),
        ("potencia", "5", "0", "1.0"),
        ("modulo", "10", "3", "1.0"),
        ("modulo", "5.5", "2", "1.5"),
        ("modulo", "-5", "3", "1.0"),
        ("modulo", "5", "0", "Error: No se puede dividir por cero"),
        ("potencia", "0", "-1", "Error: No se puede dividir por cero"),
        ("potencia", "abc", "3", "Error: Introduce números válidos"),
        ("modulo", "5", "abc", "Error: Introduce números válidos"),
    ],
)
def test_operaciones_nuevas(client, operacion, num1, num2, esperado):
    response = client.post(
        "/", data={"num1": num1, "num2": num2, "operacion": operacion}
    )
    assert response.status_code == 200
    assert f"<h2>Resultado: {esperado}</h2>" in response.get_data(as_text=True)


def test_opciones_nuevas_en_formulario(client):
    html = client.get("/").get_data(as_text=True)
    assert '<option value="potencia">Potencia</option>' in html
    assert '<option value="modulo">Módulo</option>' in html
