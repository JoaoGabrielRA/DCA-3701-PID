"""Mesmos casos da suíte original: especificações, critérios, degrau, discretização e questões da lista."""

import cmath
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pid_lgr.nucleo import polinomio as P
from pid_lgr.nucleo.entrada import interpretar_polinomio
from pid_lgr.nucleo.matriz import exponencial
from pid_lgr.nucleo.raizes import raizes
from pid_lgr.projeto.atraso import projetar_atraso, ganho_na_reta_de_amortecimento
from pid_lgr.projeto.controladores import obter_controlador, numerador_do_controlador
from pid_lgr.projeto.criterios import criterio_de_angulo
from pid_lgr.projeto.discretizacao import discretizar
from pid_lgr.projeto.erro_estatico import constantes_de_erro
from pid_lgr.projeto.especificacoes import (
    amortecimento_do_sobressinal,
    sobressinal_do_amortecimento,
    interpretar_especificacao,
)
from pid_lgr.projeto.lugar_raizes import ganhos_de_descolamento
from pid_lgr.projeto.malha import montar_malha_aberta
from pid_lgr.projeto.projeto import projetar_controlador
from pid_lgr.projeto.resposta_degrau import simular_degrau, medir_resposta
from pid_lgr.projeto.ziegler_nichols import primeiro_metodo, segundo_metodo, ponto_critico


def perto(recebido, esperado, tolerancia=1e-6):
    assert abs(recebido - esperado) < tolerancia, f"esperado {esperado}, recebido {recebido}"


QUESTOES = {
    "primeira": {
        "nG": [4, 16], "dG": [1, 4, 4, 0], "nH": [1], "dH": [1], "controlador": "pd",
        "especificacao": {"modo": "desempenho", "sobressinal": 10, "acomodacao": 4, "criterio": 5},
    },
    "segunda": {
        "nG": [1], "dG": [10000, 0, -11772], "nH": [1], "dH": [1], "controlador": "pd",
        "especificacao": {"modo": "amortecimento", "zeta": 0.7, "omegaN": 0.5},
    },
    "terceira": {
        "nG": [5, 25, 20], "dG": [1, 4, 4], "nH": [0.2], "dH": [1, 1], "controlador": "pi",
        "especificacao": {"modo": "polos", "real": -4, "imaginario": 4},
    },
    "quarta": {
        "nG": [5], "dG": [1, 12, 22, 20], "nH": [0.4], "dH": [1], "controlador": "pid",
        "especificacao": {"modo": "desempenho", "sobressinal": 20, "acomodacao": 5, "criterio": 2},
    },
}


def polos_desejados_em_malha_fechada(projeto):
    desejados = [item for item in projeto["malhaFechada"]["polos"] if item["classe"] == "desejado"]
    assert len(desejados) == 2, "o par desejado precisa aparecer na malha fechada"
    for item in desejados:
        perto(item["ponto"].real, projeto["desempenho"]["polo"].real, 1e-6)
        perto(abs(item["ponto"].imag), projeto["desempenho"]["polo"].imag, 1e-6)


def test_exponencial_de_matriz_diagonal():
    r = exponencial([[-2, 0], [0, 3]])
    perto(r[0][0], math.exp(-2), 1e-12)
    perto(r[1][1], math.exp(3), 1e-10)
    perto(r[0][1], 0, 1e-14)


def test_exponencial_de_matriz_de_rotacao():
    r = exponencial([[0, -math.pi / 2], [math.pi / 2, 0]])
    perto(r[0][0], 0, 1e-12)
    perto(r[1][0], 1, 1e-12)


def test_sobressinal_e_amortecimento_sao_inversos():
    zeta = amortecimento_do_sobressinal(10)
    perto(zeta, 0.591155, 1e-6)
    perto(sobressinal_do_amortecimento(zeta), 10, 1e-9)


def test_especificacao_por_desempenho_com_criterio_de_5():
    d = interpretar_especificacao(QUESTOES["primeira"]["especificacao"])
    perto(d["sigma"], 0.75, 1e-12)
    perto(d["omegaN"], 0.75 / 0.591155, 1e-5)


def test_especificacao_por_polos_recupera_zeta_e_omega_n():
    d = interpretar_especificacao({"modo": "polos", "real": -4, "imaginario": 4})
    perto(d["zeta"], math.sqrt(0.5), 1e-12)
    perto(d["omegaN"], 4 * math.sqrt(2), 1e-12)


def test_numerador_do_pid_tem_zero_duplo():
    assert numerador_do_controlador(obter_controlador("pid"), 3) == [1, 6, 9]


def test_deficiencia_angular_sai_entre_0_e_360_graus():
    malha = montar_malha_aberta([1], [1, 2, 0], [1], [1])
    angulo = criterio_de_angulo(complex(-2, 2), malha, obter_controlador("pd"))
    perto(angulo["fase"], -225, 1e-9)
    perto(angulo["deficiencia"], 45, 1e-9)
    assert angulo["viavel"]


def test_pd_sem_deficiencia_angular_e_recusado():
    malha = montar_malha_aberta([1], [1, 2, 0], [1], [1])
    angulo = criterio_de_angulo(complex(-1, 2), malha, obter_controlador("pd"))
    assert not angulo["viavel"]
    assert angulo["motivo"] == "semDeficiencia"


def test_pd_sobre_planta_bipropria_e_recusado():
    with pytest.raises(ValueError, match="imprópria"):
        projetar_controlador({**QUESTOES["terceira"], "controlador": "pd", "dH": [1], "nH": [1]})


def test_ganho_de_descolamento_entre_dois_polos_reais():
    ganhos = ganhos_de_descolamento([1], [1, 2, 0])
    assert len(ganhos) == 1
    perto(ganhos[0], 1, 1e-12)


def test_degrau_de_primeira_ordem_bate_com_a_solucao_exata():
    s = simular_degrau([2], [1, 2], 3)
    for k in range(0, len(s["tempos"]), 160):
        perto(s["saidas"][k], 1 - math.exp(-2 * s["tempos"][k]), 1e-10)


def test_metricas_de_segunda_ordem_padrao():
    zeta, wn = 0.5, 2
    s = simular_degrau([wn ** 2], [1, 2 * zeta * wn, wn ** 2], 12)
    m = medir_resposta(s, 1)
    perto(m["sobressinal"], sobressinal_do_amortecimento(zeta), 1e-3)
    perto(m["tempoDePico"], math.pi / (wn * math.sqrt(1 - zeta ** 2)), 1e-2)


def test_questao_1_pd_com_zero_em_8_66():
    p = projetar_controlador(QUESTOES["primeira"])
    perto(p["angulo"]["deficiencia"], 7.371, 1e-3)
    perto(p["zero"]["valor"], 8.6598, 1e-3)
    perto(p["modulo"]["kc"], 0.030458, 1e-5)
    perto(p["ganhos"]["kp"], p["modulo"]["kc"] * p["zero"]["valor"], 1e-12)
    polos_desejados_em_malha_fechada(p)


def test_questao_2_pd_da_planta_instavel():
    p = projetar_controlador(QUESTOES["segunda"])
    perto(p["modulo"]["kc"], 7000, 1e-6)
    perto(p["zero"]["valor"], 2.0389, 1e-4)
    perto(p["ganhos"]["kd"], 7000, 1e-6)
    perto(p["ganhos"]["kp"], 14272, 1e-4)
    polos_desejados_em_malha_fechada(p)


def test_questao_3_pi_com_cancelamento_em_menos_1():
    p = projetar_controlador(QUESTOES["terceira"])
    assert len(p["malhaAberta"]["cancelamentos"]) == 1
    perto(p["ganhos"]["kp"], 7, 1e-9)
    perto(p["ganhos"]["ki"], 24, 1e-9)
    polos_desejados_em_malha_fechada(p)
    perto(p["resposta"]["metricas"]["valorFinal"], 5, 1e-9)


def test_questao_4_pid_com_zeros_reais_e_iguais():
    p = projetar_controlador(QUESTOES["quarta"])
    perto(p["zero"]["valor"], 2.049, 1e-3)
    perto(p["modulo"]["kc"], 3.13596, 1e-4)
    perto(p["ganhos"]["ki"], p["modulo"]["kc"] * p["zero"]["valor"] ** 2, 1e-12)
    polos_desejados_em_malha_fechada(p)
    assert p["resposta"]["metricas"]["sobressinal"] <= 20
    assert p["resposta"]["metricas"]["acomodacao2"] < 5


def test_varredura_passa_pelos_polos_desejados_em_k_igual_a_kc():
    p = projetar_controlador(QUESTOES["quarta"])
    v, kc, polo = p["varredura"], p["modulo"]["kc"], p["desempenho"]["polo"]
    indices = np.where(np.abs(v["ganhos"] - kc) < 1e-9 * kc)[0]
    assert len(indices) > 0, "Kc precisa virar amostra da varredura"
    folga = np.min(np.abs(v["pontos"][indices[0]] - polo))
    assert folga < 1e-6, f"ramo passou a {folga} de s_d"


def test_euler_para_frente_em_1_sobre_s_mais_1():
    d = discretizar([1], [1, 1], "euler", 0.5)
    perto(d["numeradorZ"][0], 0.5, 1e-12)
    perto(d["denominadorZ"][0], 1, 1e-12)
    perto(d["denominadorZ"][1], -0.5, 1e-12)


def test_discretizacao_bate_com_a_substituicao_de_s_em_z():
    numerador, denominador = [0.539, 1.436, 0.957], [1, 0]
    z = complex(0.3, 0.7)
    substituicoes = {
        "euler": lambda T: (z - 1) / T,
        "euler-atraso": lambda T: (z - 1) / (z * T),
        "tustin": lambda T: (2 / T) * (z - 1) / (z + 1),
    }
    for metodo, substituir in substituicoes.items():
        s = substituir(2)
        esperado = P.avaliar(numerador, s) / P.avaliar(denominador, s)
        d = discretizar(numerador, denominador, metodo, 2)
        obtido = P.avaliar(d["numeradorZ"], z) / P.avaliar(d["denominadorZ"], z)
        perto(obtido.real, esperado.real, 1e-9)
        perto(obtido.imag, esperado.imag, 1e-9)


def test_segundo_exercicio_questao_1_pid_com_tustin():
    p = projetar_controlador({
        "nG": [5, 15], "dG": [1, 4, 0], "nH": [1], "dH": [1, 1], "controlador": "pid",
        "especificacao": {"modo": "desempenho", "sobressinal": 10, "acomodacao": 3, "criterio": 5},
        "discretizacao": {"metodo": "tustin", "periodo": 2, "alvo": "controlador"},
    })
    assert p["viavel"]
    polos_desejados_em_malha_fechada(p)
    perto(p["zero"]["valor"], 1.3322, 1e-4)
    perto(p["modulo"]["kc"], 0.5390, 1e-4)
    assert [round(v, 9) for v in p["discretizacao"]["denominadorZ"]] == [1, 0, -1]
    perto(p["discretizacao"]["numeradorZ"][0], 2.9319, 1e-4)


def test_segundo_exercicio_questao_2_a_sobre_s_mais_b_e_euler():
    p = projetar_controlador({
        "nG": [2, 2], "dG": [1, 2, 2], "nH": [1, 3], "dH": [1, 5], "controlador": "polo",
        "especificacao": {"modo": "polos", "real": -2.5, "imaginario": 2},
        "discretizacao": {"metodo": "euler", "periodo": 1, "alvo": "malha"},
    })
    assert p["viavel"]
    polos_desejados_em_malha_fechada(p)
    perto(p["zero"]["valor"], 2.80608, 1e-5)
    perto(p["modulo"]["kc"], 3.79990, 1e-5)
    assert p["ganhos"] == {"a": p["modulo"]["kc"], "b": p["zero"]["valor"]}
    assert not p["discretizacao"]["estavel"]
    modulos = sorted(item["modulo"] for item in p["discretizacao"]["polos"])
    perto(modulos[3], 4, 1e-9)


def test_a_sobre_s_mais_b_recusa_quando_falta_fase():
    malha = montar_malha_aberta([1], [1, 2, 0], [1], [1])
    angulo = criterio_de_angulo(complex(-2, 2), malha, obter_controlador("polo"))
    assert not angulo["viavel"]
    assert angulo["motivo"] == "excesso"


def test_expressao_fatorada_vira_coeficientes():
    casos = [
        ("5(s+3)", [5, 15]),
        ("s(s+4)", [1, 4, 0]),
        ("(s+2)^2", [1, 4, 4]),
        ("s^2 + 2s + 2", [1, 2, 2]),
        ("5(s+1)(s+4)", [5, 25, 20]),
        ("10000s^2 - 11772", [10000, 0, -11772]),
        ("-(s+1)", [-1, -1]),
        ("0,2", [0.2]),
        ("1 4 4 0", [1, 4, 4, 0]),
    ]
    for texto, esperado in casos:
        assert interpretar_polinomio(texto) == esperado, texto
    for texto in ["(s+", "abc", "", "s^-1"]:
        assert interpretar_polinomio(texto) is None, texto


def test_especificacao_por_mp_e_tempo_de_pico():
    d = interpretar_especificacao({"modo": "pico", "sobressinal": 10, "tempoDePico": 1})
    perto(d["omegaD"], math.pi, 1e-12)
    perto(d["zeta"], amortecimento_do_sobressinal(10), 1e-12)


def test_especificacao_por_zeta_e_ts():
    d = interpretar_especificacao({"modo": "amortecimentoAcomodacao", "zeta": 0.6, "acomodacao": 2, "criterio": 2})
    perto(d["sigma"], 2, 1e-12)
    perto(d["omegaN"], 2 / 0.6, 1e-12)


def test_especificacao_por_ts_e_tempo_de_pico():
    d = interpretar_especificacao({"modo": "acomodacaoPico", "acomodacao": 2, "criterio": 2, "tempoDePico": 1})
    perto(d["sigma"], 2, 1e-12)
    perto(d["omegaD"], math.pi, 1e-12)


def test_compensador_com_zero_dado_acha_o_polo_e_k():
    p = projetar_controlador({
        "nG": [1], "dG": [1, 2, 0], "nH": [1], "dH": [1], "controlador": "compensador-zero", "fixo": 1,
        "especificacao": {"modo": "polos", "real": -2, "imaginario": 2},
    })
    polos_desejados_em_malha_fechada(p)
    perto(p["zero"]["valor"], 8 / 3, 1e-9)
    perto(p["modulo"]["kc"], 16 / 3, 1e-9)


def test_compensador_com_polo_dado_acha_o_zero_e_k():
    p = projetar_controlador({
        "nG": [1], "dG": [1, 2, 0], "nH": [1], "dH": [1], "controlador": "compensador-polo", "fixo": 10,
        "especificacao": {"modo": "polos", "real": -2, "imaginario": 2},
    })
    polos_desejados_em_malha_fechada(p)
    perto(p["zero"]["valor"], 3.2, 1e-9)
    perto(p["modulo"]["kc"], 20, 1e-9)


def test_compensador_sem_o_valor_dado_e_recusado():
    with pytest.raises(ValueError, match="informe o zero dado"):
        projetar_controlador({
            "nG": [1], "dG": [1, 2, 0], "nH": [1], "dH": [1], "controlador": "compensador-zero", "fixo": None,
            "especificacao": {"modo": "polos", "real": -2, "imaginario": 2},
        })


def test_constantes_de_erro_do_exemplo_do_pi_da_apostila():
    erro = constantes_de_erro([2], [1, 2, 0])
    assert erro["tipo"] == 1
    assert erro["kp"] == math.inf
    perto(erro["kv"], 1, 1e-12)
    assert erro["ka"] == 0
    perto(erro["erroRampa"], 1, 1e-12)


def test_atraso_de_fase_do_exemplo_4_6_da_apostila():
    p = projetar_atraso({
        "nG": [5], "dG": [1, 2, 0], "nH": [1], "dH": [1],
        "atraso": {"zeta": None, "constante": 20, "zero": 0.1},
    })
    perto(p["parte"]["atual"], 2.5, 1e-12)
    perto(p["parte"]["beta"], 8, 1e-12)
    perto(p["parte"]["polo"], 0.0125, 1e-12)
    perto(p["constanteFinal"], 20, 1e-9)


def test_ganho_na_reta_de_zeta_do_exercicio_2b_da_apostila():
    ajuste = ganho_na_reta_de_amortecimento([820], [1, 30, 200, 0], 0.6)
    perto(ajuste["ganho"], 1, 2e-3)
    perto(-ajuste["ponto"].real / ajuste["omegaN"], 0.6, 1e-9)


def test_atraso_avanco_do_exemplo_4_7_da_apostila():
    p = projetar_controlador({
        "nG": [4], "dG": [1, 0.5, 0], "nH": [1], "dH": [1], "controlador": "atraso-avanco", "fixo": 0.5,
        "especificacao": {"modo": "amortecimento", "zeta": 0.5, "omegaN": 5},
        "atraso": {"constante": 80, "zero": 0.2},
    })
    perto(p["zero"]["valor"], 5, 1e-6)
    perto(p["modulo"]["kc"], 6.25, 1e-6)
    perto(p["atraso"]["beta"], 16, 1e-6)
    perto(p["atraso"]["polo"], 0.0125, 1e-9)


def test_invariancia_ao_degrau_bate_com_as_formas_fechadas():
    T, a = 0.5, 2
    e = math.exp(-a * T)
    d = discretizar([1], [1, a], "degrau", T)
    perto(d["numeradorZ"][0], (1 - e) / a, 1e-12)
    perto(d["denominadorZ"][1], -e, 1e-12)
    d = discretizar([1], [1, 0, 0], "degrau", T)
    assert [round(v, 12) for v in d["numeradorZ"]] == [0.125, 0.125]
    assert [round(v, 12) for v in d["denominadorZ"]] == [1, -2, 1]
    with pytest.raises(ValueError, match="própria"):
        discretizar([1, 1], [1], "degrau", T)


def test_ziegler_nichols_bate_com_os_exemplos_da_apostila():
    primeiro = primeiro_metodo(0.19104, 2.0041)[2]
    perto(primeiro["kp"], 12.5886, 1e-3)
    perto(primeiro["ti"], 0.3821, 1e-4)
    perto(primeiro["td"], 0.0955, 1e-4)
    segundo = segundo_metodo(4, 6.3)[2]
    perto(segundo["kp"], 2.4, 1e-12)
    perto(segundo["ti"], 3.15, 1e-12)
    perto(segundo["td"], 0.7875, 1e-12)


def test_ganho_critico_de_1_sobre_s_s1_s5():
    critico = ponto_critico([1], [1, 6, 5, 0])
    perto(critico["ganhoCritico"], 30, 1e-6)
    perto(critico["omega"], math.sqrt(5), 1e-6)
    assert ponto_critico([1], [1, 1]) is None


@pytest.mark.parametrize("grau", range(2, 9))
def test_raizes_plantadas_sao_reencontradas(grau):
    gerador = np.random.default_rng(grau)
    plantadas = []
    while len(plantadas) < grau:
        if grau - len(plantadas) >= 2 and gerador.random() < 0.5:
            z = complex(gerador.uniform(-5, 5), gerador.uniform(0.2, 5))
            plantadas += [z, z.conjugate()]
        else:
            plantadas.append(complex(gerador.uniform(-5, 5), 0))
    coeficientes = [float(c) for c in np.real(np.poly(plantadas))]
    encontradas = raizes(coeficientes)
    assert len(encontradas) == grau
    for z in plantadas:
        assert min(abs(z - r) for r in encontradas) < 1e-6
    assert all(cmath.isfinite(r) for r in encontradas)
