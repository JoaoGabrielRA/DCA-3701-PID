"""Catálogo de controladores e os polinômios de cada um."""

import math

from ..nucleo import polinomio as P

CONTROLADORES = [
    {
        "id": "pd", "nome": "PD", "zeros": 1, "polosLivres": 0, "polosNaOrigem": 0,
        "simboloLivre": "z", "simboloGanho": "K_c",
    },
    {
        "id": "pi", "nome": "PI", "zeros": 1, "polosLivres": 0, "polosNaOrigem": 1,
        "simboloLivre": "z", "simboloGanho": "K_c",
    },
    {
        "id": "pid", "nome": "PID", "zeros": 2, "polosLivres": 0, "polosNaOrigem": 1,
        "simboloLivre": "z", "simboloGanho": "K_c",
    },
    {
        "id": "polo", "nome": "controlador a/(s+b)", "zeros": 0, "polosLivres": 1, "polosNaOrigem": 0,
        "simboloLivre": "b", "simboloGanho": "a",
    },
    {
        "id": "compensador-zero", "nome": "compensador K(s+z)/(s+p)", "zeros": 0, "polosLivres": 1,
        "polosNaOrigem": 0, "fixo": "zero", "simboloLivre": "p", "simboloGanho": "K",
    },
    {
        "id": "compensador-polo", "nome": "compensador K(s+z)/(s+p)", "zeros": 1, "polosLivres": 0,
        "polosNaOrigem": 0, "fixo": "polo", "simboloLivre": "z", "simboloGanho": "K",
    },
    {
        "id": "atraso-avanco", "nome": "compensador atraso-avanço", "zeros": 0, "polosLivres": 1,
        "polosNaOrigem": 0, "fixo": "zero", "rotuloFixo": "Zero do avanço z₁, fator (s + z₁)",
        "atraso": True, "simboloLivre": "p", "simboloGanho": "K",
        "latex": "K\\,\\dfrac{(s + z_1)(s + z_2)}{(s + p_1)(s + p_2)}",
    },
    {
        "id": "atraso", "nome": "compensador em atraso", "zeros": 0, "polosLivres": 0, "polosNaOrigem": 0,
        "pipeline": "atraso", "simboloLivre": "p", "simboloGanho": "K",
        "latex": "K\\,\\dfrac{(s + z)}{(s + p)}",
    },
]


def ganhos_do_controlador(id_do_controlador, kc, valor):
    if id_do_controlador == "pd":
        return {"kp": kc * valor, "ki": 0.0, "kd": kc}
    if id_do_controlador == "pi":
        return {"kp": kc, "ki": kc * valor, "kd": 0.0}
    if id_do_controlador == "pid":
        return {"kp": 2 * kc * valor, "ki": kc * valor * valor, "kd": kc}
    if id_do_controlador == "polo":
        return {"a": kc, "b": valor}
    if id_do_controlador in ("compensador-zero", "atraso-avanco"):
        return {"k": kc, "p": valor}
    if id_do_controlador == "compensador-polo":
        return {"k": kc, "z": valor}
    return {}


def obter_controlador(id_do_controlador, fixo=None):
    encontrado = next((c for c in CONTROLADORES if c["id"] == id_do_controlador), None)
    if encontrado is None:
        raise ValueError(f"Controlador desconhecido: {id_do_controlador}")
    tem_fixo = bool(encontrado.get("fixo")) and fixo is not None and math.isfinite(fixo)
    return {
        **encontrado,
        "zerosFixos": [fixo] if tem_fixo and encontrado["fixo"] == "zero" else [],
        "polosFixos": [fixo] if tem_fixo and encontrado["fixo"] == "polo" else [],
    }


def livre_eh_polo(controlador):
    return controlador["polosLivres"] > 0


def quantidade_livre(controlador):
    return controlador["zeros"] + controlador["polosLivres"]


def _produto_de_fatores(valores):
    resultado = [1.0]
    for valor in valores:
        resultado = P.multiplicar(resultado, [1.0, valor])
    return resultado


def numerador_do_controlador(controlador, valor):
    livres = [valor] * controlador["zeros"]
    return _produto_de_fatores(livres + list(controlador.get("zerosFixos", [])))


def denominador_do_controlador(controlador, valor):
    livres = [valor] * controlador["polosLivres"]
    origem = [1.0] + [0.0] * controlador["polosNaOrigem"]
    return P.multiplicar(origem, _produto_de_fatores(livres + list(controlador.get("polosFixos", []))))


def zeros_fixos_como_pontos(controlador):
    return [complex(-v, 0) for v in controlador.get("zerosFixos", [])]


def polos_fixos_como_pontos(controlador):
    return [0j] * controlador["polosNaOrigem"] + [complex(-v, 0) for v in controlador.get("polosFixos", [])]


def excesso_de_zeros(controlador):
    zeros = controlador["zeros"] + len(controlador.get("zerosFixos", []))
    polos = controlador["polosNaOrigem"] + controlador["polosLivres"] + len(controlador.get("polosFixos", []))
    return zeros - polos
