# tests/test_calculadora.py
import pytest
from app.calculadora import sumar, restar, multiplicar, dividir, potencia, modulo


def test_sumar():
    assert sumar(2, 3) == 5
    assert sumar(-1, 1) == 0
    assert sumar(0, 0) == 0


def test_restar():
    assert restar(5, 2) == 3
    assert restar(1, -1) == 2
    assert restar(0, 0) == 0


def test_multiplicar():
    assert multiplicar(2, 3) == 6
    assert multiplicar(-1, 5) == -5
    assert multiplicar(0, 10) == 0


def test_dividir():
    assert dividir(10, 2) == 5.0
    assert dividir(5, -1) == -5.0
    with pytest.raises(ZeroDivisionError):
        dividir(1, 0)


def test_restar_decimales():
    assert restar(0.3, 0.1) == pytest.approx(0.2)


def test_restar_dos_negativos():
    assert restar(-5, -2) == -3


@pytest.mark.parametrize(
    "base, exponente, esperado",
    [
        (2, 3, 8),
        (-2, 3, -8),
        (5, 0, 1),
        (2, -2, 0.25),
        (9, 0.5, 3),
    ],
)
def test_potencia(base, exponente, esperado):
    assert potencia(base, exponente) == pytest.approx(esperado)


def test_potencia_cero_exponente_negativo():
    with pytest.raises(ZeroDivisionError):
        potencia(0, -1)


@pytest.mark.parametrize(
    "dividendo, divisor, esperado",
    [
        (10, 3, 1),
        (6, 3, 0),
        (-5, 3, 1),
        (5, -3, -1),
        (5.5, 2, 1.5),
    ],
)
def test_modulo(dividendo, divisor, esperado):
    assert modulo(dividendo, divisor) == pytest.approx(esperado)


def test_modulo_por_cero():
    with pytest.raises(ZeroDivisionError, match="No se puede dividir por cero"):
        modulo(5, 0)
