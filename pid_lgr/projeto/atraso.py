"""Compensador em atraso de fase pelo erro (roteiro da seção 4.6 da apostila)."""

import math

from ..nucleo import polinomio as P
from ..nucleo.raizes import raizes, ordenar_para_exibicao
from .criterios import argumento_graus
from .erro_estatico import constantes_de_erro
from .malha import montar_malha_aberta
from .resposta_degrau import simular_degrau, medir_resposta, valor_final

AMOSTRAS_NA_RETA = 4000
PASSOS_DE_BISSECAO = 80
JANELA_EM_CONSTANTES = 12

SIMBOLOS_DE_CONSTANTE = ["K_p", "K_v", "K_a"]


def _sinal(valor):
    return (valor > 0) - (valor < 0)


def _erro_de_fase(numerador, denominador, ponto, alvo):
    valor = P.avaliar(numerador, ponto) / P.avaliar(denominador, ponto)
    fase = argumento_graus(valor) - alvo
    return math.fmod(math.fmod(fase, 360) + 540, 360) - 180


def ganho_na_reta_de_amortecimento(numerador, denominador, zeta):
    malha = montar_malha_aberta(numerador, [1.0], [1.0], denominador)
    alvo = 0 if malha["ganho"] < 0 else 180
    direcao = complex(-zeta, math.sqrt(1 - zeta ** 2))
    raio = max([1.0] + [abs(p) for p in malha["polos"] + malha["zeros"]])
    minimo = raio * 1e-4
    maximo = raio * 50

    def ponto(r):
        return direcao * r

    def erro(r):
        return _erro_de_fase(malha["numerador"], malha["denominador"], ponto(r), alvo)

    anterior = minimo
    erro_anterior = erro(anterior)
    for i in range(1, AMOSTRAS_NA_RETA + 1):
        atual = minimo * (maximo / minimo) ** (i / AMOSTRAS_NA_RETA)
        erro_atual = erro(atual)
        if _sinal(erro_atual) != _sinal(erro_anterior) and abs(erro_atual) < 90 and abs(erro_anterior) < 90:
            baixo, alto = anterior, atual
            for _ in range(PASSOS_DE_BISSECAO):
                meio = (baixo + alto) / 2
                if _sinal(erro(meio)) == _sinal(erro(baixo)):
                    baixo = meio
                else:
                    alto = meio
            s1 = ponto((baixo + alto) / 2)
            modulo = abs(P.avaliar(malha["numerador"], s1) / P.avaliar(malha["denominador"], s1))
            return {"ponto": s1, "ganho": 1 / modulo, "omegaN": (baixo + alto) / 2}
        anterior = atual
        erro_anterior = erro_atual
    return None


def malha_fechada_com(numerador_controlador, denominador_controlador, entrada):
    nG, dG, nH, dH = entrada["nG"], entrada["dG"], entrada["nH"], entrada["dH"]
    numerador_direto = P.multiplicar(numerador_controlador, nG)
    numerador_aberto = P.multiplicar(numerador_direto, nH)
    denominador_aberto = P.multiplicar(P.multiplicar(denominador_controlador, dG), dH)
    caracteristica = P.normalizar(P.somar(denominador_aberto, numerador_aberto))
    numerador = P.normalizar(P.multiplicar(numerador_direto, dH))
    return {
        "numeradorControlador": numerador_controlador,
        "denominadorControlador": denominador_controlador,
        "numeradorAberto": P.normalizar(numerador_aberto),
        "denominadorAberto": P.normalizar(denominador_aberto),
        "numerador": numerador,
        "caracteristica": caracteristica,
        "polos": ordenar_para_exibicao(raizes(caracteristica)),
        "zeros": ordenar_para_exibicao(raizes(numerador)),
    }


def polo_dominante(polos):
    complexos = [p for p in polos if p.imag > 1e-9]
    candidatos = complexos or polos
    melhor = candidatos[0]
    for p in candidatos:
        if abs(p.real) < abs(melhor.real):
            melhor = p
    return melhor


def constante_do_tipo(erro):
    return [erro["kp"], erro["kv"], erro["ka"]][erro["tipo"]]


def parte_em_atraso(numerador_base, denominador_base, constante_desejada, zero, ponto):
    erro = constantes_de_erro(numerador_base, denominador_base)
    if erro["tipo"] > 2:
        raise ValueError("o sistema é de tipo maior que 2; as constantes K_p, K_v e K_a não se aplicam.")
    atual = constante_do_tipo(erro)
    beta = constante_desejada / atual
    polo = zero / beta
    fator_no_ponto = (ponto + zero) / (ponto + polo)
    return {
        "tipo": erro["tipo"],
        "simbolo": SIMBOLOS_DE_CONSTANTE[erro["tipo"]],
        "atual": atual,
        "desejada": constante_desejada,
        "beta": beta,
        "zero": zero,
        "polo": polo,
        "angulo": argumento_graus(fator_no_ponto),
        "modulo": abs(fator_no_ponto),
        "necessario": beta > 1,
    }


def _responder(malha, duracao):
    if not all(p.real < -1e-9 for p in malha["polos"]):
        return None
    simulacao = simular_degrau(malha["numerador"], malha["caracteristica"], duracao)
    return {
        "simulacao": simulacao,
        "metricas": medir_resposta(simulacao, valor_final(malha["numerador"], malha["caracteristica"])),
    }


def projetar_atraso(entrada):
    nG, dG, nH, dH, atraso = entrada["nG"], entrada["dG"], entrada["nH"], entrada["dH"], entrada["atraso"]
    numerador_gh = P.multiplicar(nG, nH)
    denominador_gh = P.multiplicar(dG, dH)

    ganho = 1.0
    ajuste = None
    if atraso.get("zeta") is not None:
        ajuste = ganho_na_reta_de_amortecimento(numerador_gh, denominador_gh, atraso["zeta"])
        if not ajuste:
            raise ValueError(f"o LGR de G(s)H(s) não cruza a reta de ζ = {atraso['zeta']}.")
        ganho = ajuste["ganho"]

    original = malha_fechada_com([ganho], [1.0], entrada)
    dominante = ajuste["ponto"] if ajuste else polo_dominante(original["polos"])
    parte = parte_em_atraso(P.escalar(numerador_gh, ganho), denominador_gh, atraso["constante"], atraso["zero"], dominante)
    compensada = malha_fechada_com(P.escalar([1.0, parte["zero"]], ganho), [1.0, parte["polo"]], entrada)
    duracao = min(JANELA_EM_CONSTANTES / max(abs(dominante.real), 1e-6), 400)

    restantes = [
        p for p in compensada["polos"]
        if abs(p - complex(-parte["polo"], 0)) > 1e-6 * max(1, parte["zero"])
    ]
    return {
        "tipo": "atraso",
        "entrada": entrada,
        "malhaAberta": montar_malha_aberta(nG, dG, nH, dH),
        "ganho": ganho,
        "ajuste": ajuste,
        "dominante": dominante,
        "parte": parte,
        "original": {**original, "resposta": _responder(original, duracao)},
        "compensada": {**compensada, "resposta": _responder(compensada, duracao)},
        "novoDominante": polo_dominante(restantes),
        "constanteFinal": constante_do_tipo(
            constantes_de_erro(compensada["numeradorAberto"], compensada["denominadorAberto"])
        ),
        "viavel": True,
    }
