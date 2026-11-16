# app/calculadora.py

# IMPORTANTE: reemplaza ??? con los nombres completos de los 3 integrantes,
# separados por " | " y en el mismo orden de la sección Integrantes del README.
# Ejemplo: "Ana María Pérez | Luis Andrés Gómez | Sara Restrepo Ríos"
AUTOR = "Lina Sofia Ballesteros Merchan | Alejandro Rios Muñoz | Quinnie Villarreal"


def sumar(a, b):
    return a + b


def restar(a, b):
    return a - b


def multiplicar(a, b):
    return a * b


def dividir(a, b):
    if b == 0:
        raise ZeroDivisionError("No se puede dividir por cero")
    return a / b


def potencia(a, b):
    """Eleva la base a al exponente b."""
    return a**b


def modulo(a, b):
    """Devuelve el residuo de a entre b; el divisor no puede ser cero."""
    if b == 0:
        raise ZeroDivisionError("No se puede dividir por cero")
    return a % b
