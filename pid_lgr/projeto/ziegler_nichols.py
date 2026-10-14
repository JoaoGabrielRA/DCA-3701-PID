"""Sintonia de Ziegler-Nichols, 1º e 2º métodos, e o ponto crítico do modelo."""

import math

from ..nucleo import polinomio as P
from .criterios import argumento_graus
from .malha import montar_malha_aberta

AMOSTRAS = 6000
PASSOS_DE_BISSECAO = 80


def _completar(linha):
    return {
        **linha,
        "ki": linha["kp"] / linha["ti"] if math.isfinite(linha["ti"]) else 0.0,
        "kd": linha["kp"] * linha["td"],
    }


def primeiro_metodo(atraso, constante):
    razao = constante / atraso
    return [_completar(linha) for linha in (
        {"tipo": "P", "kp": razao, "ti": math.inf, "td": 0.0},
        {"tipo": "PI", "kp": 0.9 * razao, "ti": atraso / 0.3, "td": 0.0},
        {"tipo": "PID", "kp": 1.2 * razao, "ti": 2 * atraso, "td": 0.5 * atraso},
    )]


def segundo_metodo(ganho_critico, periodo_critico):
    return [_completar(linha) for linha in (
        {"tipo": "P", "kp": 0.5 * ganho_critico, "ti": math.inf, "td": 0.0},
        {"tipo": "PI", "kp": 0.45 * ganho_critico, "ti": periodo_critico / 1.2, "td": 0.0},
        {"tipo": "PID", "kp": 0.6 * ganho_critico, "ti": 0.5 * periodo_critico, "td": 0.125 * periodo_critico},
    )]


def _sinal(valor):
    return (valor > 0) - (valor < 0)


def _fase_relativa(numerador, denominador, omega, alvo):
    s = complex(0, omega)
    valor = P.avaliar(numerador, s) / P.avaliar(denominador, s)
    fase = argumento_graus(valor) - alvo
    return math.fmod(math.fmod(fase, 360) + 540, 360) - 180


def ponto_critico(numerador, denominador):
    malha = montar_malha_aberta(numerador, [1.0], [1.0], denominador)
    alvo = 0 if malha["ganho"] < 0 else 180
    raio = max([1.0] + [abs(p) for p in malha["polos"] + malha["zeros"]])
    minimo = raio * 1e-4
    maximo = raio * 1e3

    def erro(w):
        return _fase_relativa(malha["numerador"], malha["denominador"], w, alvo)

    anterior = minimo
    erro_anterior = erro(anterior)
    for i in range(1, AMOSTRAS + 1):
        atual = minimo * (maximo / minimo) ** (i / AMOSTRAS)
        erro_atual = erro(atual)
        if _sinal(erro_atual) != _sinal(erro_anterior) and abs(erro_atual) < 90 and abs(erro_anterior) < 90:
            baixo, alto = anterior, atual
            for _ in range(PASSOS_DE_BISSECAO):
                meio = (baixo + alto) / 2
                if _sinal(erro(meio)) == _sinal(erro(baixo)):
                    baixo = meio
                else:
                    alto = meio
            omega = (baixo + alto) / 2
            s = complex(0, omega)
            modulo = abs(P.avaliar(malha["numerador"], s) / P.avaliar(malha["denominador"], s))
            return {"omega": omega, "ganhoCritico": 1 / modulo, "periodoCritico": 2 * math.pi / omega}
        anterior = atual
        erro_anterior = erro_atual
    return None
