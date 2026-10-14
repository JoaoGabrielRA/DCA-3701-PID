"""Campos do formulário, valores padrão e a validação que vira a entrada do projeto."""

import math

from ..nucleo.entrada import interpretar_polinomio, interpretar_numero
from ..projeto.controladores import obter_controlador

CAMPOS = [
    "nG", "dG", "nH", "dH", "controlador", "fixo", "modo", "sobressinal", "acomodacao", "criterio", "zeta",
    "omegaN", "tempoPico", "poloReal", "poloImaginario", "discretizacao", "periodo", "alvo", "constante",
    "zeroAtraso", "zetaAtraso",
]

CAMPOS_FIXOS = ["nG", "dG", "nH", "dH", "controlador", "modo", "discretizacao"]

CAMPOS_POR_MODO = {
    "desempenho": ["sobressinal", "acomodacao", "criterio"],
    "amortecimento": ["zeta", "omegaN"],
    "polos": ["poloReal", "poloImaginario"],
    "pico": ["sobressinal", "tempoPico"],
    "amortecimentoAcomodacao": ["zeta", "acomodacao", "criterio"],
    "acomodacaoPico": ["acomodacao", "criterio", "tempoPico"],
}

CAMPOS_DA_DISCRETIZACAO = ["periodo", "alvo"]

# Valores iniciais da página (os mesmos da versão web).
VALORES_INICIAIS = {
    "nG": "4 16", "dG": "1 4 4 0", "nH": "1", "dH": "1", "controlador": "pd", "fixo": "1",
    "modo": "desempenho", "sobressinal": "10", "acomodacao": "4", "criterio": "5", "zeta": "0.7",
    "omegaN": "0.5", "tempoPico": "1", "poloReal": "-4", "poloImaginario": "4", "discretizacao": "nenhuma",
    "periodo": "1", "alvo": "controlador", "constante": "", "zeroAtraso": "0.1", "zetaAtraso": "",
}

# Aplicados antes de cada questão da lista.
VALORES_PADRAO = {
    "nH": "1", "dH": "1", "criterio": "5", "fixo": "1", "discretizacao": "nenhuma", "periodo": "1",
    "alvo": "controlador", "constante": "", "zeroAtraso": "0.1", "zetaAtraso": "",
}

CONTROLADORES = {
    "pd": "PD",
    "pi": "PI",
    "pid": "PID com zeros reais e iguais",
    "polo": "a/(s + b), polo e ganho livres",
    "compensador-zero": "K(s + z)/(s + p), zero dado",
    "compensador-polo": "K(s + z)/(s + p), polo dado",
    "atraso-avanco": "Atraso-avanço de fase",
    "atraso": "Atraso de fase, pelo erro",
}

MODOS = {
    "desempenho": "Sobressinal e tempo de acomodação",
    "pico": "Sobressinal e tempo de pico",
    "amortecimentoAcomodacao": "Fator de amortecimento e tempo de acomodação",
    "acomodacaoPico": "Tempo de acomodação e tempo de pico",
    "amortecimento": "Fator de amortecimento e frequência natural",
    "polos": "Polos desejados",
}

DISCRETIZACOES = {
    "nenhuma": "Não discretizar",
    "tustin": "Tustin (trapezoidal)",
    "euler": "Euler ou Forward, s = (z − 1)/T",
    "euler-atraso": "Backward, s = (z − 1)/(Tz)",
    "degrau": "Invariância ao degrau (SOZ)",
}

ALVOS_DA_DISCRETIZACAO = {
    "controlador": "Controlador Gc(s)",
    "malha": "Malha aberta Gc(s)G(s)H(s)",
    "planta": "Planta G(s)",
}

ROTULOS_DO_FIXO = {
    "zero": "Zero dado z, fator (s + z)",
    "polo": "Polo dado p, fator (s + p)",
}

VALIDACOES = {
    "sobressinal": ("sobressinal", lambda v: 0 < v < 100,
                    "O sobressinal $M_P$ precisa ficar entre $0\\%$ e $100\\%$, sem os extremos."),
    "acomodacao": ("acomodacao", lambda v: v > 0, "O tempo de acomodação $t_s$ precisa ser positivo."),
    "zeta": ("zeta", lambda v: 0 < v < 1,
             "O fator de amortecimento $\\zeta$ precisa ficar entre $0$ e $1$ para gerar polos complexos."),
    "omegaN": ("omegaN", lambda v: v > 0, "A frequência natural $\\omega_n$ precisa ser positiva."),
    "tempoPico": ("tempoDePico", lambda v: v > 0, "O tempo de pico $t_p$ precisa ser positivo."),
    "poloReal": ("real", lambda v: v < 0, "A parte real dos polos desejados precisa ser negativa."),
    "poloImaginario": ("imaginario", lambda v: v > 0,
                       "A parte imaginária dos polos desejados precisa ser diferente de zero."),
}


def _numero(valores, nome):
    return interpretar_numero(str(valores.get(nome) or ""), math.nan)


def _informacao(id_do_controlador):
    try:
        return obter_controlador(id_do_controlador)
    except ValueError:
        return None


def tipo_do_fixo(id_do_controlador):
    info = _informacao(id_do_controlador)
    return info.get("fixo") if info else None


def rotulo_do_fixo(id_do_controlador):
    info = _informacao(id_do_controlador)
    if not info or not info.get("fixo"):
        return ""
    return info.get("rotuloFixo") or ROTULOS_DO_FIXO[info["fixo"]]


def usa_atraso(id_do_controlador):
    info = _informacao(id_do_controlador)
    return bool(info and (info.get("atraso") or info.get("pipeline") == "atraso"))


def so_atraso(id_do_controlador):
    info = _informacao(id_do_controlador)
    return bool(info and info.get("pipeline") == "atraso")


def interpretar_especificacao_de(valores):
    nomes = CAMPOS_POR_MODO.get(valores.get("modo"))
    if not nomes:
        return {"erro": "Escolha como a especificação será informada."}
    especificacao = {"modo": valores["modo"]}
    for nome in nomes:
        if nome == "criterio":
            especificacao["criterio"] = int(float(valores.get("criterio") or 5))
            continue
        chave, valido, erro = VALIDACOES[nome]
        valor = _numero(valores, nome)
        if nome == "poloImaginario":
            valor = abs(valor)
        if not (math.isfinite(valor) and valido(valor)):
            return {"erro": erro}
        especificacao[chave] = valor
    return {"especificacao": especificacao}


def _interpretar_discretizacao(valores):
    if not valores.get("discretizacao") or valores["discretizacao"] == "nenhuma":
        return {"discretizacao": None}
    periodo = _numero(valores, "periodo")
    if not periodo > 0:
        return {"erro": "O período de amostragem $T$ precisa ser positivo."}
    return {"discretizacao": {
        "metodo": valores["discretizacao"], "periodo": periodo, "alvo": valores.get("alvo") or "controlador",
    }}


def interpretar_fixo(valores):
    if tipo_do_fixo(valores.get("controlador")) is None:
        return {"fixo": None}
    fixo = _numero(valores, "fixo")
    if not math.isfinite(fixo):
        return {"erro": "Informe o valor dado do compensador."}
    return {"fixo": fixo}


def _interpretar_atraso(valores):
    if not usa_atraso(valores.get("controlador")):
        return {"atraso": None}
    constante = _numero(valores, "constante")
    if not constante > 0:
        return {"erro": "Informe a constante de erro desejada ($K_p$, $K_v$ ou $K_a$, conforme o tipo do sistema)."}
    zero = _numero(valores, "zeroAtraso")
    if not zero > 0:
        return {"erro": "O zero da parte em atraso precisa ser positivo, perto da origem, como 0,1."}
    zeta = None
    if so_atraso(valores.get("controlador")) and str(valores.get("zetaAtraso") or "").strip() != "":
        zeta = _numero(valores, "zetaAtraso")
        if not 0 < zeta < 1:
            return {"erro": "O $\\zeta$ dos polos dominantes precisa ficar entre $0$ e $1$, ou ficar em branco."}
    return {"atraso": {"constante": constante, "zero": zero, "zeta": zeta}}


def ler_coeficientes(valores):
    return [interpretar_polinomio(str(valores.get(nome) or "")) for nome in ("nG", "dG", "nH", "dH")]


def interpretar_formulario(dados):
    valores = {**VALORES_PADRAO, **dados}
    nG, dG, nH, dH = ler_coeficientes(valores)
    if any(item is None for item in (nG, dG, nH, dH)):
        return {"erro": "Confira $G(s)$ e $H(s)$: use coeficientes em ordem decrescente de $s$, como 1 4 0, "
                        "ou a expressão, como s(s+4)."}
    if any(all(v == 0 for v in item) for item in (nG, dG, nH, dH)):
        return {"erro": "Nenhum numerador ou denominador de $G(s)$ e $H(s)$ pode ser nulo."}

    somente_atraso = so_atraso(valores.get("controlador"))
    leituras = [interpretar_fixo(valores), _interpretar_atraso(valores)]
    if not somente_atraso:
        leituras += [interpretar_especificacao_de(valores), _interpretar_discretizacao(valores)]
    for leitura in leituras:
        if "erro" in leitura:
            return leitura

    return {"entrada": {
        "nG": nG, "dG": dG, "nH": nH, "dH": dH,
        "controlador": valores["controlador"],
        "fixo": interpretar_fixo(valores)["fixo"],
        "atraso": _interpretar_atraso(valores)["atraso"],
        "especificacao": None if somente_atraso else interpretar_especificacao_de(valores)["especificacao"],
        "discretizacao": None if somente_atraso else _interpretar_discretizacao(valores)["discretizacao"],
    }}


def campos_do_endereco(valores):
    """Campos relevantes para o link que reabre o projeto (mesma regra da versão web)."""
    controlador = valores.get("controlador")
    nomes = list(CAMPOS_FIXOS)
    if tipo_do_fixo(controlador):
        nomes.append("fixo")
    if usa_atraso(controlador):
        nomes += ["constante", "zeroAtraso"]
    if so_atraso(controlador):
        nomes.append("zetaAtraso")
    nomes += CAMPOS_POR_MODO.get(valores.get("modo"), [])
    if valores.get("discretizacao") != "nenhuma":
        nomes += CAMPOS_DA_DISCRETIZACAO
    return {nome: str(valores.get(nome, "")).strip() for nome in nomes}
