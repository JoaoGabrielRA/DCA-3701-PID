"""Varredura do lugar geométrico das raízes e ganhos de descolamento."""

import math

import numpy as np

from ..nucleo import polinomio as P
from ..nucleo.raizes import raizes, casar_por_proximidade

AMOSTRAS_INICIAIS = 200
AMOSTRAS_LOGARITMICAS = 2400
FOLGA_ALEM_DA_JANELA = 1.6
GANHO_MAXIMO_ABSOLUTO = 1e9
FRACAO_DA_TOLERANCIA_NO_ZERO = 0.005
FATOR_DA_BUSCA = 10
PASSOS_DO_REFINO = 8
DESVIOS_AO_REDOR_DO_NOTAVEL = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 5e-2]
TOLERANCIA_IMAGINARIA = 1e-6


def _grau_efetivo(coeficientes):
    escala = max((abs(v) for v in coeficientes), default=0.0)
    desprezivel = 1e-14 * max(1.0, escala)
    inicio = 0
    while inicio < len(coeficientes) - 1 and abs(coeficientes[inicio]) <= desprezivel:
        inicio += 1
    return len(coeficientes) - 1 - inicio


def _combinar(denominador, numerador, ganho):
    return [d + ganho * n for d, n in zip(denominador, numerador)]


def _raizes_rapidas(coeficientes):
    return raizes(coeficientes, refinar=False)


def _maior_modulo(numerador, denominador, ganho):
    return max([0.0] + [abs(z) for z in _raizes_rapidas(_combinar(denominador, numerador, ganho))])


def _maior_folga_ate_os_zeros(numerador, denominador, zeros, ganho):
    encontradas = _raizes_rapidas(_combinar(denominador, numerador, ganho))
    if not encontradas:
        return math.inf
    return max(min(abs(s - zero) for s in encontradas) for zero in zeros)


def estimar_ganho_maximo(numerador, denominador, raio=10):
    alvo = max(raio, 1) * FOLGA_ALEM_DA_JANELA
    inferior = 0.0
    superior = 0.0
    anterior = -math.inf
    for expoente in range(10):
        ganho = 10.0 ** expoente
        modulo = _maior_modulo(numerador, denominador, ganho)
        if modulo >= alvo:
            superior = ganho
            break
        if modulo <= anterior * 1.0001 and expoente > 2:
            return ganho
        anterior = modulo
        inferior = ganho

    if superior == 0:
        return GANHO_MAXIMO_ABSOLUTO

    for _ in range(24):
        meio = (inferior + superior) / 2
        if _maior_modulo(numerador, denominador, meio) >= alvo:
            superior = meio
        else:
            inferior = meio
    return max(superior, 1e-3)


def estimar_ganho_para_fechar_nos_zeros(numerador, denominador, zeros=None, raio=0):
    raio = max(raio or 0, 1)
    alvo = raio * FOLGA_ALEM_DA_JANELA
    finitos = zeros if zeros is not None else raizes(numerador)
    zeros = [z for z in finitos if abs(z) <= alvo]
    if not zeros:
        return 0.0

    tolerancia = raio * FRACAO_DA_TOLERANCIA_NO_ZERO

    def folga(ganho):
        return _maior_folga_ate_os_zeros(numerador, denominador, zeros, ganho)

    superior = 1.0
    while folga(superior) > tolerancia:
        if superior >= GANHO_MAXIMO_ABSOLUTO:
            return GANHO_MAXIMO_ABSOLUTO
        superior = min(superior * FATOR_DA_BUSCA, GANHO_MAXIMO_ABSOLUTO)

    inferior = superior / FATOR_DA_BUSCA
    for _ in range(PASSOS_DO_REFINO):
        meio = math.sqrt(inferior * superior)
        if folga(meio) <= tolerancia:
            superior = meio
        else:
            inferior = meio
    return superior


def limites_de_ganho(numerador, denominador, zeros=None, raio=None):
    ganho_da_janela = estimar_ganho_maximo(numerador, denominador, raio if raio is not None else 10)
    ganho_dos_zeros = estimar_ganho_para_fechar_nos_zeros(numerador, denominador, zeros, raio)
    ramos_que_fogem = _grau_efetivo(denominador) - _grau_efetivo(numerador)
    limite = max(ganho_da_janela, ganho_dos_zeros)
    if ramos_que_fogem == 0 and ganho_dos_zeros > 0:
        limite = ganho_dos_zeros
    return {"limite": limite, "ganhoDaJanela": ganho_da_janela, "ganhoDosZeros": ganho_dos_zeros}


def _acrescentar_notaveis(lista, notaveis, limite):
    for notavel in notaveis:
        if not math.isfinite(notavel) or notavel <= 0 or notavel > limite:
            continue
        lista.append(notavel)
        for desvio in DESVIOS_AO_REDOR_DO_NOTAVEL:
            lista.append(notavel * (1 - desvio))
            acima = notavel * (1 + desvio)
            if acima <= limite:
                lista.append(acima)


def _montar_ganhos(ganho_maximo, amostras, notaveis):
    limite = max(ganho_maximo, 1e-3)
    iniciais = max(20, round(amostras * 0.08))
    logaritmicas = max(40, amostras - iniciais)
    inicio_linear = min(0.1, limite / 20)

    lista = [(inicio_linear * i) / (iniciais - 1) for i in range(iniciais)]
    expoente_inicial = math.log10(max(inicio_linear, 1e-6))
    expoente_final = math.log10(limite)
    for i in range(logaritmicas):
        t = i / (logaritmicas - 1)
        lista.append(10 ** (expoente_inicial + t * (expoente_final - expoente_inicial)))

    _acrescentar_notaveis(lista, notaveis, limite)
    lista.sort()
    saida = []
    for valor in lista:
        if not saida or valor - saida[-1] > 1e-12:
            saida.append(valor)
    return saida


def calcular_lugar_raizes(numerador, denominador, zeros=None, ganhos_notaveis=(), raio=None):
    ramos = len(denominador) - 1
    estimativa = limites_de_ganho(numerador, denominador, zeros, raio)
    ganhos = _montar_ganhos(estimativa["limite"], AMOSTRAS_INICIAIS + AMOSTRAS_LOGARITMICAS, list(ganhos_notaveis))

    pontos = np.zeros((len(ganhos), ramos), dtype=complex)
    anteriores = None
    for i, ganho in enumerate(ganhos):
        atuais = _raizes_rapidas(_combinar(denominador, numerador, ganho))
        if len(atuais) < ramos and anteriores is not None:
            atuais = atuais + [z * 10 for z in anteriores[len(atuais):]]
        while len(atuais) < ramos:
            atuais.append(0j)
        atuais = atuais[:ramos]
        if anteriores is not None:
            atuais = casar_por_proximidade(anteriores, atuais)
        pontos[i, :] = atuais
        anteriores = atuais

    return {
        "ganhos": np.array(ganhos),
        "pontos": pontos,
        "ramos": ramos,
        "ganhoMaximo": estimativa["limite"],
        "ganhoDaJanela": estimativa["ganhoDaJanela"],
        "ganhoDosZeros": estimativa["ganhoDosZeros"],
    }


def ganhos_de_descolamento(numerador, denominador):
    equacao = P.somar(
        P.multiplicar(numerador, P.derivar(denominador)),
        P.escalar(P.multiplicar(denominador, P.derivar(numerador)), -1),
    )
    saida = []
    for raiz in raizes(equacao):
        if abs(raiz.imag) >= TOLERANCIA_IMAGINARIA:
            continue
        valor_num = P.avaliar(numerador, raiz.real)
        if valor_num == 0:
            continue
        ganho = -P.avaliar(denominador, raiz.real) / valor_num
        if math.isfinite(ganho) and ganho > 0:
            saida.append(ganho)
    return saida
