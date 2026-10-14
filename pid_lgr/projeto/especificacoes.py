"""Especificações de malha fechada convertidas em ζ, ωn e polos desejados."""

import math

CONSTANTES_DE_ACOMODACAO = {2: 4, 5: 3}


def amortecimento_do_sobressinal(sobressinal):
    logaritmo = math.log(sobressinal / 100)
    return -logaritmo / math.sqrt(math.pi ** 2 + logaritmo ** 2)


def sobressinal_do_amortecimento(zeta):
    return 100 * math.exp((-zeta * math.pi) / math.sqrt(1 - zeta ** 2))


def _polos_desejados(zeta, omega_n):
    sigma = zeta * omega_n
    omega_d = omega_n * math.sqrt(1 - zeta ** 2)
    return {
        "zeta": zeta,
        "omegaN": omega_n,
        "sigma": sigma,
        "omegaD": omega_d,
        "polo": complex(-sigma, omega_d),
        "referencia": {
            "sobressinal": sobressinal_do_amortecimento(zeta),
            "acomodacao2": CONSTANTES_DE_ACOMODACAO[2] / sigma,
            "acomodacao5": CONSTANTES_DE_ACOMODACAO[5] / sigma,
            "tempoDePico": math.pi / omega_d,
        },
    }


def _por_desempenho(e):
    zeta = amortecimento_do_sobressinal(e["sobressinal"])
    constante = CONSTANTES_DE_ACOMODACAO[e["criterio"]]
    sigma = constante / e["acomodacao"]
    return {**e, "constante": constante, **_polos_desejados(zeta, sigma / zeta)}


def _por_polos(e):
    omega_n = math.hypot(e["real"], e["imaginario"])
    return {**e, **_polos_desejados(-e["real"] / omega_n, omega_n)}


def _por_pico(e):
    zeta = amortecimento_do_sobressinal(e["sobressinal"])
    omega_d = math.pi / e["tempoDePico"]
    return {**e, **_polos_desejados(zeta, omega_d / math.sqrt(1 - zeta ** 2))}


def _por_amortecimento_e_acomodacao(e):
    constante = CONSTANTES_DE_ACOMODACAO[e["criterio"]]
    sigma = constante / e["acomodacao"]
    return {**e, "constante": constante, **_polos_desejados(e["zeta"], sigma / e["zeta"])}


def _por_acomodacao_e_pico(e):
    constante = CONSTANTES_DE_ACOMODACAO[e["criterio"]]
    sigma = constante / e["acomodacao"]
    omega_d = math.pi / e["tempoDePico"]
    omega_n = math.hypot(sigma, omega_d)
    return {**e, "constante": constante, **_polos_desejados(sigma / omega_n, omega_n)}


_INTERPRETES = {
    "desempenho": _por_desempenho,
    "polos": _por_polos,
    "pico": _por_pico,
    "amortecimentoAcomodacao": _por_amortecimento_e_acomodacao,
    "acomodacaoPico": _por_acomodacao_e_pico,
}


def interpretar_especificacao(especificacao):
    interprete = _INTERPRETES.get(especificacao["modo"])
    if interprete:
        return interprete(especificacao)
    return {**especificacao, **_polos_desejados(especificacao["zeta"], especificacao["omegaN"])}
