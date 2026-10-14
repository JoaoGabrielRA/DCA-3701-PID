"""Raízes de polinômios com pares conjugados exatos e zeros na origem separados."""

import math
from functools import cmp_to_key

import numpy as np

from . import polinomio as P


def _resolver_quadratica(a, b, c):
    delta = b * b - 4 * a * c
    if delta >= 0:
        r = math.sqrt(delta)
        q = -0.5 * (b + r) if b >= 0 else -0.5 * (b - r)
        if abs(q) < 1e-300:
            return [0j, 0j]
        return [complex(q / a), complex(c / q)]
    parte_real = -b / (2 * a)
    parte_imaginaria = math.sqrt(-delta) / (2 * a)
    return [complex(parte_real, parte_imaginaria), complex(parte_real, -parte_imaginaria)]


def _refinar_newton(monico, z):
    derivada = P.derivar(monico)
    atual = z
    for _ in range(12):
        valor = P.avaliar(monico, atual)
        inclinacao = P.avaliar(derivada, atual)
        if abs(inclinacao) < 1e-300:
            break
        passo = valor / inclinacao
        if not (math.isfinite(passo.real) and math.isfinite(passo.imag)):
            break
        novo = atual - passo
        # Newton não pode piorar o resíduo (raízes múltiplas, por exemplo).
        if abs(P.avaliar(monico, novo)) > abs(valor):
            break
        atual = novo
        if abs(passo) < 1e-14 * (1 + abs(atual)):
            break
    return atual


def _agrupar_multiplas(lista):
    """Raízes múltiplas saem espalhadas (erro ~ eps^(1/m)); a média do grupo volta à precisão de máquina."""
    restantes = list(lista)
    saida = []
    while restantes:
        semente = restantes.pop(0)
        tolerancia = 1e-5 * max(1.0, abs(semente))
        grupo = [semente] + [z for z in restantes if abs(z - semente) < tolerancia]
        restantes = [z for z in restantes if abs(z - semente) >= tolerancia]
        media = sum(grupo) / len(grupo)
        saida.extend([media] * len(grupo))
    return saida


def _simetrizar(lista, escala):
    tolerancia = 1e-7 * max(1.0, escala)
    saida = [complex(z.real, 0.0) if abs(z.imag) < tolerancia else complex(z) for z in lista]
    usados = set()
    for i in range(len(saida)):
        if i in usados or saida[i].imag <= 0:
            continue
        melhor = -1
        menor = math.inf
        for j in range(len(saida)):
            if j == i or j in usados or saida[j].imag >= 0:
                continue
            distancia = abs(saida[i] - saida[j].conjugate())
            if distancia < menor:
                menor = distancia
                melhor = j
        if melhor >= 0 and menor < 1e-6 * max(1.0, escala):
            re = (saida[i].real + saida[melhor].real) / 2
            im = (saida[i].imag - saida[melhor].imag) / 2
            saida[i] = complex(re, im)
            saida[melhor] = complex(re, -im)
            usados.add(i)
            usados.add(melhor)
    return saida


def raizes(coeficientes, refinar=True):
    p = P.normalizar([float(c) for c in coeficientes])
    if len(p) <= 1:
        return []

    escala_p = max(1.0, P.maior_coeficiente(p))
    corte = len(p)
    while corte > 1 and abs(p[corte - 1]) < 1e-14 * escala_p:
        corte -= 1
    zeros_na_origem = len(p) - corte
    reduzido = p[:corte]

    if len(reduzido) == 2:
        encontradas = [complex(-reduzido[1] / reduzido[0])]
    elif len(reduzido) == 3:
        encontradas = _resolver_quadratica(*reduzido)
    elif len(reduzido) > 3:
        monico = [v / reduzido[0] for v in reduzido]
        encontradas = _agrupar_multiplas([complex(z) for z in np.roots(monico)])
        if refinar:
            encontradas = [_refinar_newton(monico, z) for z in encontradas]
    else:
        encontradas = []

    escala = max([1.0] + [abs(z) for z in encontradas])
    completas = _simetrizar(encontradas, escala)
    completas.extend([0j] * zeros_na_origem)
    return completas


def _comparar(a, b):
    if abs(a.real - b.real) > 1e-9:
        return -1 if b.real < a.real else 1
    if b.imag == a.imag:
        return 0
    return -1 if b.imag < a.imag else 1


def ordenar_para_exibicao(lista):
    return sorted(lista, key=cmp_to_key(_comparar))


def casar_por_proximidade(anteriores, atuais):
    n = len(atuais)
    distancias = np.abs(np.asarray(anteriores)[:, None] - np.asarray(atuais)[None, :])
    saida = [0j] * n
    usados = np.zeros(n, dtype=bool)
    for i in range(n):
        linha = np.where(usados, np.inf, distancias[i])
        melhor = int(np.argmin(linha))
        saida[i] = atuais[melhor]
        usados[melhor] = True
    return saida
