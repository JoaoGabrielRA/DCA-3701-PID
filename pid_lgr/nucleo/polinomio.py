"""Polinômios como listas de coeficientes em ordem decrescente de potência."""

EPS = 1e-14


def normalizar(p):
    i = 0
    while i < len(p) - 1 and abs(p[i]) < EPS:
        i += 1
    return list(p[i:])


def preencher(p, tamanho):
    if len(p) >= tamanho:
        return list(p)
    return [0.0] * (tamanho - len(p)) + list(p)


def somar(a, b):
    n = max(len(a), len(b))
    x = preencher(a, n)
    y = preencher(b, n)
    return [u + v for u, v in zip(x, y)]


def multiplicar(a, b):
    if len(a) == 0 or len(b) == 0:
        return [0.0]
    saida = [0.0] * (len(a) + len(b) - 1)
    for i, u in enumerate(a):
        for j, v in enumerate(b):
            saida[i + j] += u * v
    return saida


def escalar(p, k):
    return [v * k for v in p]


def derivar(p):
    g = len(p) - 1
    if g <= 0:
        return [0.0]
    return [p[i] * (g - i) for i in range(g)]


def avaliar(p, x):
    """Horner; funciona com x real ou complexo."""
    acumulado = 0
    for c in p:
        acumulado = acumulado * x + c
    return acumulado


def grau(p):
    return len(normalizar(p)) - 1


def maior_coeficiente(p):
    return max((abs(v) for v in p), default=0.0)
