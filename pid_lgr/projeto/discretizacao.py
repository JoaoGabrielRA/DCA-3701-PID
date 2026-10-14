"""Discretização por Euler (Forward), Backward, Tustin ou invariância ao degrau (SOZ)."""

import cmath

import numpy as np

from ..nucleo import polinomio as P
from ..nucleo.raizes import raizes, ordenar_para_exibicao
from .resposta_degrau import realizar_em_espaco_de_estados, discretizar_estados

FOLGA_RELATIVA = 1e-12
FOLGA_DE_RAIZ_REPETIDA = 1e-6

METODOS = {
    "euler": {
        "nome": "Euler ou Forward",
        "substituicao": "s = \\frac{z - 1}{T}",
        "alfa": lambda T: [1.0, -1.0],
        "beta": lambda T: [0.0, T],
    },
    "euler-atraso": {
        "nome": "Backward",
        "substituicao": "s = \\frac{z - 1}{T\\,z}",
        "alfa": lambda T: [1.0, -1.0],
        "beta": lambda T: [T, 0.0],
    },
    "tustin": {
        "nome": "Tustin (trapezoidal)",
        "substituicao": "s = \\frac{2}{T}\\,\\frac{z - 1}{z + 1}",
        "alfa": lambda T: [2.0, -2.0],
        "beta": lambda T: [T, T],
    },
    "degrau": {
        "nome": "invariância ao degrau (SOZ)",
        "segurador": True,
    },
}

ALVOS = {
    "controlador": "G_c(s)",
    "malha": "G_c(s)G(s)H(s)",
    "planta": "G(s)",
}


def descricao_do_metodo(id_do_metodo):
    """Parte serializável do método (sem as funções alfa e beta)."""
    metodo = METODOS[id_do_metodo]
    return {chave: valor for chave, valor in metodo.items() if not callable(valor)}


def _potencia(base, expoente):
    resultado = [1.0]
    for _ in range(expoente):
        resultado = P.multiplicar(resultado, base)
    return resultado


def _aparar(p):
    escala = max(P.maior_coeficiente(p), 1e-300)
    inicio = 0
    while inicio < len(p) - 1 and abs(p[inicio]) < FOLGA_RELATIVA * escala:
        inicio += 1
    return [0.0 if abs(v) < FOLGA_RELATIVA * escala else v for v in p[inicio:]]


def _substituir(polinomio, alfa, beta, ordem):
    p = P.normalizar(polinomio)
    grau = len(p) - 1
    resultado = [0.0]
    for k in range(grau + 1):
        coeficiente = p[grau - k]
        termo = P.multiplicar(_potencia(alfa, k), _potencia(beta, ordem - k))
        resultado = P.somar(resultado, P.escalar(termo, coeficiente))
    return _aparar(resultado)


def _cancelar_fatores_z(numerador, denominador):
    num = list(numerador)
    den = list(denominador)
    cancelados = 0
    while len(num) > 1 and len(den) > 1 and num[-1] == 0 and den[-1] == 0:
        num.pop()
        den.pop()
        cancelados += 1
    return num, den, cancelados


def _equacao_de_diferencas(numerador, denominador):
    ordem = len(denominador) - 1
    if len(numerador) - 1 > ordem:
        return None
    return {"entrada": P.preencher(numerador, ordem + 1), "saida": list(denominador)}


def _funcao_discreta_dos_estados(transicao, entrada, saida, direto):
    """Faddeev-LeVerrier: coeficientes de det(zI - Φ) e de C adj(zI - Φ) Γ."""
    ordem = transicao.shape[0]
    identidade = np.eye(ordem)
    denominador = [1.0]
    numerador = []
    acumulada = identidade
    for k in range(1, ordem + 1):
        numerador.append(float(saida @ (acumulada @ entrada)))
        produto = transicao @ acumulada
        coeficiente = -float(np.trace(produto)) / k
        denominador.append(coeficiente)
        acumulada = produto + identidade * coeficiente
    return {
        "numerador": P.somar(P.preencher(numerador, ordem + 1), P.escalar(denominador, direto)),
        "denominador": denominador,
    }


def _fracoes_parciais(numerador, denominador, periodo):
    denominador_com_degrau = P.multiplicar(P.normalizar(denominador), [1.0, 0.0])
    polos = ordenar_para_exibicao(raizes(denominador_com_degrau))
    escala = max([1.0] + [abs(p) for p in polos])
    for i in range(len(polos)):
        for j in range(i + 1, len(polos)):
            if abs(polos[i] - polos[j]) < FOLGA_DE_RAIZ_REPETIDA * escala:
                return None
    derivada = P.derivar(denominador_com_degrau)
    return [
        {
            "polo": polo,
            "residuo": complex(P.avaliar(numerador, polo)) / complex(P.avaliar(derivada, polo)),
            "amostrado": cmath.exp(polo * periodo),
        }
        for polo in polos
    ]


def _por_segurador(numerador, denominador, periodo):
    if P.grau(numerador) > P.grau(denominador):
        raise ValueError(
            "a invariância ao degrau exige uma função própria, com grau do numerador até o do denominador."
        )
    r = realizar_em_espaco_de_estados(numerador, denominador)
    if r["ordem"] == 0:
        return {"numerador": [r["direto"]], "denominador": [1.0], "fracoes": None}
    d = discretizar_estados(r["estados"], r["ordem"], periodo)
    discreta = _funcao_discreta_dos_estados(d["transicao"], d["entrada"], r["saida"], r["direto"])
    return {
        "numerador": _aparar(discreta["numerador"]),
        "denominador": _aparar(discreta["denominador"]),
        "fracoes": _fracoes_parciais(numerador, denominador, periodo),
    }


def _finalizar(base, numerador, denominador):
    num, den, cancelados = _cancelar_fatores_z(_aparar(numerador), _aparar(denominador))
    lider = den[0]
    numerador_z = P.escalar(num, 1 / lider)
    denominador_z = P.escalar(den, 1 / lider)
    polos = ordenar_para_exibicao(raizes(denominador_z)) if len(denominador_z) > 1 else []
    polos_continuos = ordenar_para_exibicao(raizes(base["denominadorS"])) if P.grau(base["denominadorS"]) > 0 else []
    return {
        **base,
        "cancelados": cancelados,
        "numeradorZ": numerador_z,
        "denominadorZ": denominador_z,
        "causal": len(numerador_z) <= len(denominador_z),
        "diferencas": _equacao_de_diferencas(numerador_z, denominador_z),
        "polos": [{"ponto": ponto, "modulo": abs(ponto)} for ponto in polos],
        "estavel": all(abs(ponto) < 1 - 1e-9 for ponto in polos),
        "continuoEstavel": all(ponto.real < -1e-9 for ponto in polos_continuos),
    }


def discretizar(numerador, denominador, id_do_metodo, periodo):
    metodo = METODOS.get(id_do_metodo)
    if metodo is None:
        raise ValueError(f"Método de discretização desconhecido: {id_do_metodo}")
    base = {
        "id": id_do_metodo,
        "metodo": descricao_do_metodo(id_do_metodo),
        "periodo": periodo,
        "numeradorS": P.normalizar(numerador),
        "denominadorS": P.normalizar(denominador),
    }

    if metodo.get("segurador"):
        resultado = _por_segurador(numerador, denominador, periodo)
        return _finalizar(
            {
                **base,
                "fracoes": resultado["fracoes"],
                "numeradorBruto": resultado["numerador"],
                "denominadorBruto": resultado["denominador"],
            },
            resultado["numerador"],
            resultado["denominador"],
        )

    alfa = metodo["alfa"](periodo)
    beta = metodo["beta"](periodo)
    ordem = max(P.grau(numerador), P.grau(denominador))
    numerador_substituido = _substituir(numerador, alfa, beta, ordem)
    denominador_substituido = _substituir(denominador, alfa, beta, ordem)
    return _finalizar(
        {
            **base,
            "ordem": ordem,
            "alfa": alfa,
            "beta": beta,
            "numeradorSubstituido": numerador_substituido,
            "denominadorSubstituido": denominador_substituido,
        },
        numerador_substituido,
        denominador_substituido,
    )


def discretizar_projeto(malha_fechada, entrada, pedido):
    alvos = {
        "malha": (malha_fechada["numeradorAberto"], malha_fechada["denominadorAberto"]),
        "controlador": (malha_fechada["numeradorControlador"], malha_fechada["denominadorControlador"]),
        "planta": (entrada["nG"], entrada["dG"]),
    }
    numerador, denominador = alvos.get(pedido["alvo"], alvos["controlador"])
    return {"alvo": pedido["alvo"], **discretizar(numerador, denominador, pedido["metodo"], pedido["periodo"])}

