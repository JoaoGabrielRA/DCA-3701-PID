"""Orquestra o projeto completo: especificação, critérios, malha fechada, degrau, LGR e discretização."""

from ..nucleo import polinomio as P
from .especificacoes import interpretar_especificacao
from .controladores import (
    obter_controlador,
    ganhos_do_controlador,
    numerador_do_controlador,
    denominador_do_controlador,
    excesso_de_zeros,
    zeros_fixos_como_pontos,
)
from .malha import montar_malha_aberta, analisar_malha_fechada, pontos_notaveis, raio_de_interesse
from .criterios import criterio_de_angulo, localizar_zero, criterio_de_modulo
from .resposta_degrau import horizonte_de_simulacao, simular_degrau, valor_final, medir_resposta
from .lugar_raizes import calcular_lugar_raizes, ganhos_de_descolamento
from .discretizacao import discretizar_projeto
from .atraso import parte_em_atraso, projetar_atraso


def _validar_proprio(entrada, controlador):
    folga_direta = P.grau(entrada["dG"]) - P.grau(entrada["nG"])
    folga_aberta = folga_direta + P.grau(entrada["dH"]) - P.grau(entrada["nH"])
    if excesso_de_zeros(controlador) > min(folga_direta, folga_aberta):
        raise ValueError(
            f"com o {controlador['nome']}, $G_c(s)G(s)H(s)$ teria mais zeros que polos e a malha seria imprópria."
        )


def _responder(malha_fechada, desempenho):
    numerador, caracteristica = malha_fechada["numerador"], malha_fechada["caracteristica"]
    simulacao = simular_degrau(
        numerador, caracteristica, horizonte_de_simulacao(malha_fechada["polos"], desempenho["sigma"])
    )
    return {"simulacao": simulacao, "metricas": medir_resposta(simulacao, valor_final(numerador, caracteristica))}


def _tentar_discretizar(malha_fechada, entrada, pedido):
    try:
        return discretizar_projeto(malha_fechada, entrada, pedido)
    except (ValueError, ZeroDivisionError, IndexError) as falha:
        return {"alvo": pedido["alvo"], "erro": str(falha)}


def _varrer(projeto):
    zero, malha_aberta, modulo = projeto["zero"], projeto["malhaAberta"], projeto["modulo"]
    controlador = projeto["controladorFinal"]
    numerador_bruto = P.multiplicar(numerador_do_controlador(controlador, zero["valor"]), malha_aberta["numerador"])
    denominador_bruto = P.multiplicar(
        denominador_do_controlador(controlador, zero["valor"]), malha_aberta["denominador"]
    )
    tamanho = max(len(numerador_bruto), len(denominador_bruto))
    return calcular_lugar_raizes(
        P.preencher(numerador_bruto, tamanho),
        P.preencher(denominador_bruto, tamanho),
        zeros=(
            list(malha_aberta["zeros"])
            + [zero["ponto"]] * controlador["zeros"]
            + zeros_fixos_como_pontos(controlador)
        ),
        ganhos_notaveis=[modulo["kc"]] + ganhos_de_descolamento(numerador_bruto, denominador_bruto),
        raio=raio_de_interesse(pontos_notaveis(projeto, malha_fechada=True)),
    )


def esbocar_projeto(nG, dG, nH, dH, especificacao, id_do_controlador, fixo=None):
    """Versão leve usada na prévia do plano s: só malha aberta, polos desejados e o zero."""
    malha_aberta = montar_malha_aberta(nG, dG, nH, dH)
    desempenho = interpretar_especificacao(especificacao) if especificacao else None
    controlador = obter_controlador(id_do_controlador, fixo) if id_do_controlador else None
    esboco = {"malhaAberta": malha_aberta, "desempenho": desempenho, "controlador": controlador, "zero": None}
    if controlador and desempenho and not controlador.get("pipeline"):
        angulo = criterio_de_angulo(desempenho["polo"], malha_aberta, controlador)
        if angulo["viavel"]:
            esboco["zero"] = localizar_zero(desempenho["polo"], angulo)
    return esboco


def projetar_controlador(entrada):
    controlador = obter_controlador(entrada["controlador"], entrada.get("fixo"))
    if controlador.get("pipeline") == "atraso":
        return projetar_atraso(entrada)
    if controlador.get("fixo") and len(controlador["zerosFixos"]) + len(controlador["polosFixos"]) == 0:
        raise ValueError(f"informe o {controlador['fixo']} dado do compensador.")
    _validar_proprio(entrada, controlador)

    desempenho = interpretar_especificacao(entrada["especificacao"])
    malha_aberta = montar_malha_aberta(entrada["nG"], entrada["dG"], entrada["nH"], entrada["dH"])
    angulo = criterio_de_angulo(desempenho["polo"], malha_aberta, controlador)
    base = {
        "entrada": entrada,
        "controlador": controlador,
        "desempenho": desempenho,
        "malhaAberta": malha_aberta,
        "angulo": angulo,
        "viavel": angulo["viavel"],
    }
    if not angulo["viavel"]:
        return base

    zero = localizar_zero(desempenho["polo"], angulo)
    modulo = criterio_de_modulo(desempenho["polo"], malha_aberta, controlador, zero)
    ganhos = ganhos_do_controlador(controlador["id"], modulo["kc"], zero["valor"])

    controlador_final = controlador
    atraso = None
    if controlador.get("atraso"):
        numerador_base = P.escalar(
            P.multiplicar(numerador_do_controlador(controlador, zero["valor"]), malha_aberta["numerador"]),
            modulo["kc"],
        )
        denominador_base = P.multiplicar(
            denominador_do_controlador(controlador, zero["valor"]), malha_aberta["denominador"]
        )
        atraso = parte_em_atraso(
            numerador_base, denominador_base,
            entrada["atraso"]["constante"], entrada["atraso"]["zero"], desempenho["polo"],
        )
        controlador_final = {
            **controlador,
            "zerosFixos": controlador["zerosFixos"] + [atraso["zero"]],
            "polosFixos": controlador["polosFixos"] + [atraso["polo"]],
        }
    malha_fechada = analisar_malha_fechada(entrada, controlador_final, zero, modulo["kc"], desempenho["polo"])

    projeto = {
        **base,
        "controladorFinal": controlador_final,
        "atraso": atraso,
        "zero": zero,
        "modulo": modulo,
        "ganhos": ganhos,
        "malhaFechada": malha_fechada,
        "resposta": _responder(malha_fechada, desempenho) if malha_fechada["estavel"] else None,
        "discretizacao": (
            _tentar_discretizar(malha_fechada, entrada, entrada["discretizacao"])
            if entrada.get("discretizacao") else None
        ),
    }
    projeto["varredura"] = _varrer(projeto)
    return projeto
