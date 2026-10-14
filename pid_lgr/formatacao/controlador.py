"""Forma fatorada e paralela do controlador em LaTeX."""

from .numero import numero_latex

RELACOES = {
    "pd": [("kp", "K_c\\,z"), ("kd", "K_c")],
    "pi": [("kp", "K_c"), ("ki", "K_c\\,z")],
    "pid": [("kp", "2K_c\\,z"), ("ki", "K_c\\,z^2"), ("kd", "K_c")],
    "polo": [("a", "a"), ("b", "b")],
    "compensador-zero": [("k", "K"), ("p", "p")],
    "compensador-polo": [("k", "K"), ("z", "z")],
}

SIMBOLOS = {"kp": "K_p", "ki": "K_i", "kd": "K_d", "a": "a", "b": "b", "k": "K", "p": "p", "z": "z"}


def fator_do_zero_latex(valor):
    if isinstance(valor, str):
        return f"(s + {valor})"
    if abs(valor) < 1e-12:
        return "s"
    return f"(s + {numero_latex(valor)})" if valor > 0 else f"(s - {numero_latex(-valor)})"


def _tem_fixos(controlador):
    return (
        len(controlador.get("zerosFixos", [])) + len(controlador.get("polosFixos", [])) > 0
        or bool(controlador.get("fixo"))
    )


def forma_paralela_latex(controlador):
    if controlador["polosLivres"] > 0 or _tem_fixos(controlador):
        return None
    termos = ["K_p"]
    if controlador["polosNaOrigem"] > 0:
        termos.append("\\dfrac{K_i}{s}")
    if controlador["zeros"] > controlador["polosNaOrigem"]:
        termos.append("K_d\\,s")
    return " + ".join(termos)


def _potencia_latex(fator, expoente):
    if expoente == 0:
        return ""
    return f"{fator}^{{{expoente}}}" if expoente > 1 else fator


def _fator_fixo_latex(controlador, tipo):
    valores = controlador.get("zerosFixos", []) if tipo == "zero" else controlador.get("polosFixos", [])
    if valores:
        return "".join(fator_do_zero_latex(v) for v in valores)
    if controlador.get("fixo") == tipo:
        return f"(s + {'z' if tipo == 'zero' else 'p'})"
    return ""


def forma_fatorada_latex(controlador, livre=None, ganho=None):
    livre = controlador["simboloLivre"] if livre is None else livre
    ganho = controlador["simboloGanho"] if ganho is None else ganho
    fator = fator_do_zero_latex(livre)
    numerador = _potencia_latex(fator, controlador["zeros"]) + _fator_fixo_latex(controlador, "zero")
    denominador = (
        _potencia_latex("s", controlador["polosNaOrigem"])
        + _potencia_latex(fator, controlador["polosLivres"])
        + _fator_fixo_latex(controlador, "polo")
    )
    if not denominador:
        return f"{ganho}\\,{numerador}"
    if not numerador:
        return f"\\dfrac{{{ganho}}}{{{denominador}}}"
    return f"{ganho}\\,\\dfrac{{{numerador}}}{{{denominador}}}"


def controlador_latex(controlador):
    if controlador.get("latex"):
        return f"G_c(s) = {controlador['latex']}"
    paralela = forma_paralela_latex(controlador)
    fatorada = forma_fatorada_latex(controlador)
    return f"G_c(s) = {paralela} = {fatorada}" if paralela else f"G_c(s) = {fatorada}"


def relacoes_de_ganho(controlador):
    return [
        {"chave": chave, "simbolo": SIMBOLOS[chave], "expressao": expressao}
        for chave, expressao in RELACOES[controlador["id"]]
    ]
