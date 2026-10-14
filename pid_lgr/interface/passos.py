"""Os passos do roteiro de projeto (1 a 10) e o LGR do sistema compensado."""

import math

from ..formatacao.controlador import (
    controlador_latex,
    forma_fatorada_latex,
    forma_paralela_latex,
    relacoes_de_ganho,
)
from ..formatacao.latex import complexo_latex, polinomio_latex, razao_latex, rotular_contribuicoes
from ..formatacao.numero import fixo_latex, formatar_g, numero_latex
from ..nucleo import polinomio as P
from ..projeto.controladores import polos_fixos_como_pontos, zeros_fixos_como_pontos
from ..projeto.discretizacao import ALVOS
from ..projeto.erro_estatico import constantes_de_erro
from ..projeto.malha import RAZAO_DE_DOMINANCIA, pontos_notaveis
from . import graficos as G

N = numero_latex
F = fixo_latex
CL = complexo_latex


# Passo 1 ---------------------------------------------------------------------

def _bloco_do_sobressinal(d, des):
    mp, zeta = des["sobressinal"], des["zeta"]
    ln = math.log(mp / 100)
    d.paragrafo(f"**Sobressinal máximo:** $M_P \\le {N(mp)}\\%$")
    d.formula(
        "\\zeta = \\sqrt{\\dfrac{\\left(\\ln \\frac{M_P}{100}\\right)^2}{\\pi^2 + \\left(\\ln \\frac{M_P}{100}\\right)^2}}"
    )
    d.formula(
        f"\\ln\\left(\\frac{{{N(mp)}}}{{100}}\\right) = {F(ln)} \\;\\Rightarrow\\; "
        f"\\zeta = \\sqrt{{\\dfrac{{{F(ln ** 2)}}}{{{F(math.pi ** 2)} + {F(ln ** 2)}}}}} = {F(zeta)}"
    )


def _bloco_da_acomodacao(d, des):
    ts, criterio, c, sigma = des["acomodacao"], des["criterio"], des["constante"], des["sigma"]
    d.paragrafo(f"**Tempo de acomodação ({criterio}%):** $t_s < {N(ts)}\\,\\text{{s}}$")
    d.formula(
        f"t_s({criterio}\\%) = \\frac{{{c}}}{{\\zeta\\,\\omega_n}} \\;\\Rightarrow\\; \\zeta\\,\\omega_n = "
        f"\\frac{{{c}}}{{t_s}} = \\frac{{{c}}}{{{N(ts)}}} = {F(sigma)}"
    )


def _bloco_do_pico(d, des):
    tp, wd = des["tempoDePico"], des["omegaD"]
    d.paragrafo(f"**Tempo de pico:** $t_p = {N(tp)}\\,\\text{{s}}$")
    d.formula(
        f"t_p = \\frac{{\\pi}}{{\\omega_d}} \\;\\Rightarrow\\; \\omega_d = \\frac{{\\pi}}{{t_p}} = "
        f"\\frac{{\\pi}}{{{N(tp)}}} = {F(wd)}\\;\\text{{rad/s}}"
    )


def _avisar_fronteira(d):
    d.aviso(
        "informacao",
        "Os limites viram igualdade: o projeto usa os valores que atendem às especificações no limite, "
        "o que deixa os polos desejados sobre a fronteira da região permitida.",
    )


def _p1_desempenho(d, des):
    _bloco_do_sobressinal(d, des)
    d.separador()
    _bloco_da_acomodacao(d, des)
    d.formula(
        f"\\omega_n = \\frac{{\\zeta\\,\\omega_n}}{{\\zeta}} = \\frac{{{F(des['sigma'])}}}{{{F(des['zeta'])}}} = "
        f"{F(des['omegaN'])}\\;\\text{{rad/s}}"
    )
    _avisar_fronteira(d)


def _p1_pico(d, des):
    _bloco_do_sobressinal(d, des)
    d.separador()
    _bloco_do_pico(d, des)
    d.formula(
        f"\\omega_n = \\frac{{\\omega_d}}{{\\sqrt{{1 - \\zeta^2}}}} = \\frac{{{F(des['omegaD'])}}}"
        f"{{\\sqrt{{1 - {F(des['zeta'])}^2}}}} = {F(des['omegaN'])}\\;\\text{{rad/s}}"
    )
    d.formula(f"\\zeta\\,\\omega_n = {F(des['zeta'])} \\cdot {F(des['omegaN'])} = {F(des['sigma'])}")
    _avisar_fronteira(d)


def _p1_amortecimento_acomodacao(d, des):
    d.paragrafo(f"**Amortecimento dado:** $\\zeta = {N(des['zeta'])}$")
    d.separador()
    _bloco_da_acomodacao(d, des)
    d.formula(
        f"\\omega_n = \\frac{{\\zeta\\,\\omega_n}}{{\\zeta}} = \\frac{{{F(des['sigma'])}}}{{{N(des['zeta'])}}} = "
        f"{F(des['omegaN'])}\\;\\text{{rad/s}}"
    )
    _avisar_fronteira(d)


def _p1_acomodacao_pico(d, des):
    _bloco_da_acomodacao(d, des)
    d.separador()
    _bloco_do_pico(d, des)
    d.separador()
    d.paragrafo("Com a parte real e a parte imaginária dos polos definidas:")
    d.formula(
        f"\\omega_n = \\sqrt{{(\\zeta\\omega_n)^2 + \\omega_d^2}} = \\sqrt{{{F(des['sigma'])}^2 + "
        f"{F(des['omegaD'])}^2}} = {F(des['omegaN'])}\\;\\text{{rad/s}}"
    )
    d.formula(
        f"\\zeta = \\frac{{\\zeta\\omega_n}}{{\\omega_n}} = \\frac{{{F(des['sigma'])}}}{{{F(des['omegaN'])}}} = "
        f"{F(des['zeta'])}"
    )
    _avisar_fronteira(d)


def _p1_amortecimento(d, des):
    d.paragrafo("**Especificação dada diretamente:**")
    d.formula(f"\\zeta = {N(des['zeta'])}, \\qquad \\omega_n = {N(des['omegaN'])}\\;\\text{{rad/s}}")
    d.formula(f"\\zeta\\,\\omega_n = {N(des['zeta'])} \\cdot {N(des['omegaN'])} = {F(des['sigma'])}")


def _p1_polos(d, des):
    re, im = des["real"], abs(des["imaginario"])
    d.paragrafo("**Polos de malha fechada dados:**")
    d.formula(f"s_d = {N(re)} \\pm {N(im)}\\,j")
    d.formula(
        f"\\omega_n = |s_d| = \\sqrt{{({N(re)})^2 + ({N(im)})^2}} = {F(des['omegaN'])}\\;\\text{{rad/s}}"
    )
    d.formula(
        f"\\zeta = \\frac{{-\\operatorname{{Re}}(s_d)}}{{\\omega_n}} = \\frac{{{N(-re)}}}{{{F(des['omegaN'])}}} = "
        f"{F(des['zeta'])}"
    )


_P1 = {
    "desempenho": _p1_desempenho,
    "amortecimento": _p1_amortecimento,
    "polos": _p1_polos,
    "pico": _p1_pico,
    "amortecimentoAcomodacao": _p1_amortecimento_acomodacao,
    "acomodacaoPico": _p1_acomodacao_pico,
}


def passo01(d, projeto):
    des = projeto["desempenho"]
    _P1[des["modo"]](d, des)
    d.separador()
    d.paragrafo("**Frequência natural amortecida:**")
    d.formula(
        f"\\omega_d = \\omega_n\\sqrt{{1 - \\zeta^2}} = {F(des['omegaN'])}\\sqrt{{1 - {F(des['zeta'])}^2}} = "
        f"{F(des['omegaD'])}\\;\\text{{rad/s}}"
    )


# Passo 2 ---------------------------------------------------------------------

def passo02(d, projeto):
    des, ma = projeto["desempenho"], projeto["malhaAberta"]
    d.paragrafo("Par de polos complexos de um sistema de segunda ordem:")
    d.formula("s_d = -\\zeta\\,\\omega_n \\pm j\\,\\omega_n\\sqrt{1 - \\zeta^2} = -\\sigma \\pm j\\,\\omega_d")
    d.formula(f"s_d = -{F(des['sigma'])} \\pm {F(des['omegaD'])}\\,j")
    d.paragrafo("Os polos ficam sobre a reta de amortecimento, que faz com o semieixo real negativo o ângulo:")
    d.formula(
        f"\\beta = \\arccos \\zeta = \\arccos({F(des['zeta'])}) = {F(math.degrees(math.acos(des['zeta'])), 2)}^\\circ, "
        f"\\qquad |s_d| = \\omega_n = {F(des['omegaN'])}"
    )
    d.separador()
    plano = G.Plano(
        pontos_notaveis(projeto, polo_do_controlador=False, zero_do_controlador=False),
        "Polos desejados no plano s",
    )
    G.desenhar_retas_de_amortecimento(plano, des["zeta"])
    G.desenhar_polos_zeros(plano, ma["polos"], ma["zeros"])
    G.desenhar_polos_desejados(plano, des["polo"])
    d.figura(plano.figura())


# Passo 3 ---------------------------------------------------------------------

def _listar_raizes(d, rotulo, simbolo, lista, vazio):
    contagem = "n_p" if simbolo == "p" else "n_z"
    d.paragrafo(f"**{rotulo}** (${contagem} = {len(lista)}$)")
    if not lista:
        d.paragrafo(vazio)
        return
    for indice, item in enumerate(lista):
        d.formula(f"{simbolo}_{{{indice + 1}}} = {CL(item)}")


def passo03(d, projeto):
    entrada, ma, ctrl = projeto["entrada"], projeto["malhaAberta"], projeto["controlador"]
    d.formula(
        f"G(s) = {razao_latex(entrada['nG'], entrada['dG'])}, \\qquad H(s) = {razao_latex(entrada['nH'], entrada['dH'])}"
    )
    d.paragrafo("Função de transferência de malha aberta da planta:")
    d.formula(f"G(s)H(s) = {razao_latex(ma['numerador'], ma['denominador'])}")
    d.formula(f"k = \\frac{{{N(ma['numerador'][0])}}}{{{N(ma['denominador'][0])}}} = {N(ma['ganho'])}")

    esquerda, direita = d.colunas(2)
    _listar_raizes(esquerda, "Polos", "p", ma["polos"], "Nenhum polo finito.")
    _listar_raizes(direita, "Zeros", "z", ma["zeros"], "Nenhum zero finito.")

    for ponto in ma["cancelamentos"]:
        d.aviso(
            "informacao",
            f"Polo e zero coincidem em $s = {CL(ponto)}$. As contribuições deles se anulam nos "
            "critérios de ângulo e de módulo, mas o modo continua presente na malha fechada.",
        )

    d.separador()
    familia_pid = ctrl["id"] in ("pd", "pi", "pid")
    d.paragrafo(f"**Controlador {ctrl['nome']}:**" if familia_pid else "**Controlador:**")
    d.formula(controlador_latex(ctrl))
    if ctrl["zeros"] > 1:
        d.paragrafo("Os dois zeros são reais e iguais, então um único valor $z$ descreve os dois.")
    d.paragrafo("Malha aberta compensada:")
    d.formula(
        f"G_c(s)G(s)H(s) = {forma_fatorada_latex(ctrl)} \\cdot {razao_latex(ma['numerador'], ma['denominador'])}"
    )
    livre = "a posição do polo" if ctrl["polosLivres"] > 0 else "a posição do zero"
    d.paragrafo(
        f"Restam duas incógnitas: ${ctrl['simboloLivre']}$, {livre}, que sai do critério de ângulo, e "
        f"${ctrl['simboloGanho']}$, que sai do critério de módulo, ambos aplicados em $s = s_d$."
    )
    if ctrl.get("atraso"):
        d.aviso(
            "informacao",
            "No atraso-avanço, os passos 4 a 6 projetam só a parte em avanço, com o zero $z_1$ dado. "
            "A parte em atraso entra no passo 6b, pela constante de erro.",
        )


# Passo 4 ---------------------------------------------------------------------

def _listar_angulos(d, itens, polo):
    for item in itens:
        d.formula(
            f"\\angle(s_d - {item['rotulo']}) = \\angle({CL(polo)} - ({CL(item['referencia'])})) = "
            f"\\angle({CL(item['diferenca'])}) = {F(item['angulo'], 2)}^\\circ"
        )


def _explicar_inviabilidade(d, projeto):
    angulo, ctrl = projeto["angulo"], projeto["controlador"]
    singularidade = "polo" if ctrl["polosLivres"] > 0 else "zero"
    if angulo["motivo"] == "semDeficiencia":
        d.aviso(
            "erro",
            f"**Sem deficiência angular.** $s_d$ já satisfaz o critério de ângulo sem o {singularidade}, então um "
            f"ganho proporcional basta e o {singularidade} do {ctrl['nome']} iria para o infinito.",
        )
        return
    if ctrl["polosLivres"] > 0:
        d.aviso(
            "erro",
            "**Falta fase em $s_d$.** Um polo real só retira fase, e aqui ele precisaria retirar "
            f"${F(angulo['porSingularidade'], 2)}^\\circ$, mais que os $180^\\circ$ possíveis. "
            "Use um controlador com zero, como PD ou PID.",
        )
        return
    d.aviso(
        "erro",
        "**Deficiência grande demais.** Cada zero real contribui com menos de $180^\\circ$, e aqui cada um "
        f"precisaria de ${F(angulo['porSingularidade'], 2)}^\\circ$. O {ctrl['nome']} não alcança $s_d$; "
        "revise as especificações ou use um controlador com mais zeros.",
    )


def passo04(d, projeto):
    angulo, des, ma, ctrl = projeto["angulo"], projeto["desempenho"], projeto["malhaAberta"], projeto["controlador"]
    polo = des["polo"]
    polos = rotular_contribuicoes(angulo["contribuicaoPolos"], "p")
    zeros = rotular_contribuicoes(angulo["contribuicaoZeros"], "z")
    singularidade = "polo" if ctrl["polosLivres"] > 0 else "zero"
    simbolo = ctrl["simboloLivre"]

    d.paragrafo("**Condição para $s_d$ pertencer ao LGR:**")
    d.formula(
        "\\angle G_c(s_d)G(s_d)H(s_d) = \\sum \\angle(s_d - z_j) - \\sum \\angle(s_d - p_i) = 180^\\circ \\pm q\\,360^\\circ"
    )
    conhecidos = (
        (["o polo do controlador na origem ($p_c$)"] if ctrl["polosNaOrigem"] > 0 else [])
        + [f"o polo dado em $s = {N(-v)}$ ($p_c$)" for v in ctrl.get("polosFixos", [])]
        + [f"o zero dado em $s = {N(-v)}$ ($z_c$)" for v in ctrl.get("zerosFixos", [])]
    )
    incluindo = f", incluindo {' e '.join(conhecidos)}" if conhecidos else ""
    d.paragrafo(
        f"Primeiro soma-se tudo o que já é conhecido{incluindo}. O {singularidade} do controlador fica para depois."
    )

    d.separador()
    d.paragrafo("**Ângulos dos polos:**")
    _listar_angulos(d, polos, polo)
    d.formula(f"\\sum \\angle(s_d - p_i) = {F(angulo['somaPolos'], 2)}^\\circ")

    if zeros:
        d.paragrafo("**Ângulos dos zeros:**" if ctrl.get("zerosFixos") else "**Ângulos dos zeros da planta:**")
        _listar_angulos(d, zeros, polo)
        d.formula(f"\\sum \\angle(s_d - z_j) = {F(angulo['somaZeros'], 2)}^\\circ")
    else:
        d.paragrafo("Sem zeros finitos na planta: $\\sum \\angle(s_d - z_j) = 0^\\circ$.")

    if angulo["anguloDoGanho"] != 0:
        d.aviso("informacao", "O ganho $k$ de $G(s)H(s)$ é negativo e soma $180^\\circ$ à fase.")

    d.separador()
    d.paragrafo(f"**Fase sem o {singularidade} do controlador:**")
    parcela = f" + {F(angulo['anguloDoGanho'], 0)}^\\circ" if angulo["anguloDoGanho"] != 0 else ""
    d.formula(
        f"\\theta = {F(angulo['somaZeros'], 2)}^\\circ - {F(angulo['somaPolos'], 2)}^\\circ{parcela} = "
        f"{F(angulo['fase'], 2)}^\\circ"
    )
    d.paragrafo(f"**Deficiência angular** que o {singularidade} precisa suprir:")
    d.formula(
        f"\\phi_c = -180^\\circ - \\theta = -180^\\circ - ({F(angulo['fase'], 2)}^\\circ) \\equiv "
        f"{F(angulo['deficiencia'], 2)}^\\circ \\pmod{{360^\\circ}}"
    )

    if ctrl["polosLivres"] > 0:
        d.paragrafo(f"Um polo contribui com sinal negativo, então $-\\angle(s_d + {simbolo}) \\equiv \\phi_c$:")
        d.formula(
            f"\\angle(s_d + {simbolo}) = 360^\\circ - \\phi_c = 360^\\circ - {F(angulo['deficiencia'], 2)}^\\circ = "
            f"{F(angulo['porSingularidade'], 2)}^\\circ"
        )
    elif ctrl["zeros"] > 1:
        d.formula(
            f"{ctrl['zeros']}\\,\\angle(s_d + z) = \\phi_c \\;\\Rightarrow\\; \\angle(s_d + z) = "
            f"\\frac{{{F(angulo['deficiencia'], 2)}^\\circ}}{{{ctrl['zeros']}}} = {F(angulo['porSingularidade'], 2)}^\\circ"
        )
    else:
        d.formula(f"\\angle(s_d + z) = \\phi_c = {F(angulo['porSingularidade'], 2)}^\\circ")

    if not angulo["viavel"]:
        _explicar_inviabilidade(d, projeto)

    d.separador()
    plano = G.Plano(pontos_notaveis(projeto, zero_do_controlador=False), "Contribuições angulares em sd")
    G.desenhar_vetores(plano, list(ma["polos"]) + polos_fixos_como_pontos(ctrl), polo, G.CORES["polo"])
    G.desenhar_vetores(plano, list(ma["zeros"]) + zeros_fixos_como_pontos(ctrl), polo, G.CORES["zero"])
    G.desenhar_polos_zeros(plano, ma["polos"], ma["zeros"])
    G.desenhar_fixos_do_controlador(plano, ctrl)
    G.desenhar_polos_desejados(plano, polo)
    d.figura(plano.figura())


# Passo 5 ---------------------------------------------------------------------

def titulo05(projeto):
    if projeto["controlador"]["polosLivres"] > 0:
        return "**Passo 5:** Localização do polo do controlador"
    return "**Passo 5:** Localização do zero do controlador"


def _descrever(ctrl):
    if ctrl["polosLivres"] > 0:
        return "Polo do controlador"
    return "Zeros do controlador (duplos)" if ctrl["zeros"] > 1 else "Zero do controlador"


def passo05(d, projeto):
    zero, angulo, des, ma, ctrl = (
        projeto["zero"], projeto["angulo"], projeto["desempenho"], projeto["malhaAberta"], projeto["controlador"]
    )
    eh_polo = ctrl["polosLivres"] > 0
    s = ctrl["simboloLivre"]
    angular = "\\phi_p" if eh_polo else "\\phi_z"

    d.paragrafo(
        f"O {'polo' if eh_polo else 'zero'} em $s = -{s}$ enxerga $s_d$ sob o ângulo ${angular}$. "
        "No triângulo formado com o eixo real:"
    )
    d.formula(
        f"\\tan {angular} = \\frac{{\\omega_d}}{{{s} - \\sigma}} \\;\\Longrightarrow\\; "
        f"{s} = \\sigma + \\frac{{\\omega_d}}{{\\tan {angular}}}"
    )
    d.paragrafo("Substituindo:")
    d.formula(
        f"{s} = {F(zero['sigma'])} + \\frac{{{F(zero['omegaD'])}}}{{\\tan({F(angulo['porSingularidade'], 2)}^\\circ)}} = "
        f"{F(zero['sigma'])} + \\frac{{{F(zero['omegaD'])}}}{{{F(zero['tangente'])}}} = "
        f"{F(zero['sigma'])} + ({F(zero['afastamento'])}) = {F(zero['valor'])}"
    )
    d.aviso("sucesso", f"**{_descrever(ctrl)}:** $s = -{s} = {F(-zero['valor'])}$")

    if zero["semiplanoDireito"]:
        d.aviso(
            "atencao",
            "O polo caiu no semiplano direito: o controlador sozinho é instável." if eh_polo
            else "O zero caiu no semiplano direito: o controlador fica de fase não mínima e a resposta pode "
                 "começar no sentido contrário ao degrau.",
        )
    elif ctrl["polosNaOrigem"] > 0 and abs(zero["valor"]) < 1e-6 * max(1, des["omegaN"]):
        d.aviso("atencao", "O zero caiu sobre o polo do controlador na origem e anula a ação integral.")

    d.separador()
    plano = G.Plano(pontos_notaveis(projeto), f"{_descrever(ctrl)} e polos desejados")
    G.desenhar_vetores(plano, [zero["ponto"]], des["polo"], G.CORES["controlador"])
    G.desenhar_polos_zeros(plano, ma["polos"], ma["zeros"])
    G.desenhar_controlador(plano, ctrl, zero)
    G.desenhar_polos_desejados(plano, des["polo"])
    d.figura(plano.figura())


# Passo 6 ---------------------------------------------------------------------

def titulo06(projeto):
    return f"**Passo 6:** Critério de módulo e ${projeto['controlador']['simboloGanho']}$"


def _listar_distancias(d, itens, polo):
    for item in itens:
        d.formula(
            f"\\lvert s_d - {item['rotulo']} \\rvert = \\lvert {CL(polo)} - ({CL(item['referencia'])}) \\rvert = "
            f"\\lvert {CL(item['diferenca'])} \\rvert = {F(item['valor'])}"
        )


def _produto_latex(itens):
    return " \\cdot ".join(F(item["valor"]) for item in itens)


def passo06(d, projeto):
    modulo, des, ctrl = projeto["modulo"], projeto["desempenho"], projeto["controlador"]
    ganho = ctrl["simboloGanho"]
    polo = des["polo"]
    polos = rotular_contribuicoes(modulo["distanciasPolos"], "p")
    zeros = rotular_contribuicoes(modulo["distanciasZeros"], "z")

    d.paragrafo("**Condição de módulo em $s_d$:**")
    d.formula(
        f"|{ganho}\\,P(s_d)| = 1 \\;\\Longrightarrow\\; {ganho} = \\frac{{\\prod |s_d - p_i|}}{{|k|\\,\\prod |s_d - z_j|}}"
    )
    d.paragrafo(
        "Agora o polo do controlador ($p_c$) entra no produto, junto com os polos e zeros da planta."
        if ctrl["polosLivres"] > 0
        else "Agora o zero do controlador ($z_c$) entra no produto, junto com os polos e zeros da planta."
    )

    d.separador()
    d.paragrafo("**Distâncias aos polos:**")
    _listar_distancias(d, polos, polo)
    d.formula(f"\\prod |s_d - p_i| = {_produto_latex(polos)} = {F(modulo['produtoPolos'])}")

    if zeros:
        d.paragrafo("**Distâncias aos zeros:**")
        _listar_distancias(d, zeros, polo)
        d.formula(f"\\prod |s_d - z_j| = {_produto_latex(zeros)} = {F(modulo['produtoZeros'])}")
    else:
        d.paragrafo("Sem zeros finitos: $\\prod |s_d - z_j| = 1$.")

    d.separador()
    d.paragrafo("**Ganho total** da malha em $s_d$:")
    ganho_total = modulo["produtoPolos"] / modulo["produtoZeros"]
    d.formula(
        f"K_t = \\frac{{\\prod |s_d - p_i|}}{{\\prod |s_d - z_j|}} = "
        f"\\frac{{{F(modulo['produtoPolos'])}}}{{{F(modulo['produtoZeros'])}}} = {N(ganho_total)}"
    )
    d.paragrafo(f"Como $G(s)H(s)$ já tem ganho $k = {N(modulo['ganhoDaPlanta'])}$, o ganho do controlador é:")
    d.formula(
        f"{ganho} = \\frac{{K_t}}{{|k|}} = \\frac{{{N(ganho_total)}}}{{{N(modulo['ganhoDaPlanta'])}}} = {N(modulo['kc'])}"
    )
    d.aviso("sucesso", f"${ganho} = {N(modulo['kc'])}$")


# Passo 6b --------------------------------------------------------------------

LIMITE_DE_ANGULO = -5
LIMITES = [
    "K_p = \\lim_{s \\to 0} G_cGH",
    "K_v = \\lim_{s \\to 0} s\\,G_cGH",
    "K_a = \\lim_{s \\to 0} s^2 G_cGH",
]


def renderizar_parte(d, parte, nome_do_ponto="s_d", malha="G_cGH"):
    d.paragrafo(f"**Constante de erro atual** (sistema tipo {parte['tipo']}):")
    d.formula(f"{LIMITES[parte['tipo']].replace('G_cGH', malha)} = {N(parte['atual'])}")

    d.paragrafo("**Aumento necessário:**")
    d.formula(
        f"\\beta = \\frac{{{parte['simbolo']}^{{\\text{{comp}}}}}}{{{parte['simbolo']}}} = "
        f"\\frac{{{N(parte['desejada'])}}}{{{N(parte['atual'])}}} = {N(parte['beta'])}"
    )
    if not parte["necessario"]:
        d.aviso(
            "informacao",
            "A constante atual já atende ao pedido ($\\beta \\le 1$), então a parte em atraso não é necessária.",
        )

    d.separador()
    d.paragrafo("Zero perto da origem e polo $\\beta$ vezes mais perto:")
    d.formula(
        f"z = {N(parte['zero'])} \\;\\Rightarrow\\; p = \\frac{{z}}{{\\beta}} = "
        f"\\frac{{{N(parte['zero'])}}}{{{N(parte['beta'])}}} = {N(parte['polo'])}"
    )
    d.formula(f"G_{{\\text{{atraso}}}}(s) = \\frac{{s + {N(parte['zero'])}}}{{s + {N(parte['polo'])}}}")

    d.separador()
    d.paragrafo(f"**Verificação em ${nome_do_ponto}$:** a parte em atraso deve mexer pouco no LGR.")
    fracao = f"\\frac{{{nome_do_ponto} + {N(parte['zero'])}}}{{{nome_do_ponto} + {N(parte['polo'])}}}"
    d.formula(
        f"\\angle{fracao} = {F(parte['angulo'], 2)}^\\circ, \\qquad \\left|{fracao}\\right| = {F(parte['modulo'])}"
    )
    if parte["angulo"] < LIMITE_DE_ANGULO:
        d.aviso(
            "atencao",
            f"A contribuição passa de ${LIMITE_DE_ANGULO}^\\circ$. Aproxime o zero da origem (aumente $T$) "
            "para o atraso mexer menos no transitório.",
        )
    else:
        d.aviso(
            "sucesso",
            f"Contribuição entre ${LIMITE_DE_ANGULO}^\\circ$ e $0^\\circ$ e módulo perto de $1$: "
            "o transitório quase não muda.",
        )


def passo06b(d, projeto):
    d.paragrafo(
        "A parte em avanço já leva $s_d$ para o LGR. A parte em atraso aumenta a constante de erro sem mudar "
        "muito o transitório."
    )
    renderizar_parte(d, projeto["atraso"])


# Passo 7 ---------------------------------------------------------------------

def _forma_paralela_numerica(ctrl, ganhos):
    termos = [N(ganhos["kp"])]
    if ctrl["polosNaOrigem"] > 0:
        termos.append(f"\\dfrac{{{N(ganhos['ki'])}}}{{s}}")
    if ctrl["zeros"] > ctrl["polosNaOrigem"]:
        termos.append(f"{N(ganhos['kd'])}\\,s")
    return " + ".join(termos)


def _passo07_direto(d, projeto):
    zero, modulo, mf, atraso = projeto["zero"], projeto["modulo"], projeto["malhaFechada"], projeto["atraso"]
    ctrl = projeto.get("controladorFinal") or projeto["controlador"]
    ganho, livre = ctrl["simboloGanho"], ctrl["simboloLivre"]
    d.paragrafo("Os parâmetros saem direto dos dois critérios:")
    d.formula(
        f"{ganho} = {N(modulo['kc'])} \\quad (\\text{{critério de módulo}}), \\qquad "
        f"{livre} = {N(zero['valor'])} \\quad (\\text{{critério de ângulo}})"
    )
    d.separador()
    d.paragrafo("**Controlador projetado:**")
    d.formula(f"G_c(s) = {forma_fatorada_latex(ctrl, zero['valor'], N(modulo['kc']))}")
    d.formula(f"G_c(s) = {razao_latex(mf['numeradorControlador'], mf['denominadorControlador'])}")
    extra = f", atraso com $z = {N(atraso['zero'])}$ e $p = {N(atraso['polo'])}$" if atraso else ""
    d.aviso("sucesso", f"**Controlador:** ${ganho} = {N(modulo['kc'])}$, ${livre} = {N(zero['valor'])}${extra}")


def passo07(d, projeto):
    ctrl, zero, modulo, ganhos, mf = (
        projeto["controlador"], projeto["zero"], projeto["modulo"], projeto["ganhos"], projeto["malhaFechada"]
    )
    if not forma_paralela_latex(ctrl):
        _passo07_direto(d, projeto)
        return

    d.paragrafo("Expandindo a forma fatorada e comparando com a forma paralela:")
    d.formula(f"G_c(s) = {forma_fatorada_latex(ctrl)} = {forma_paralela_latex(ctrl)}")
    d.separador()
    for relacao in relacoes_de_ganho(ctrl):
        d.formula(f"{relacao['simbolo']} = {relacao['expressao']} = {N(ganhos[relacao['chave']])}")
    d.paragrafo(f"com $K_c = {N(modulo['kc'])}$ e $z = {N(zero['valor'])}$.")

    d.separador()
    d.paragrafo("**Controlador projetado:**")
    d.formula(f"G_c(s) = {forma_fatorada_latex(ctrl, zero['valor'], N(modulo['kc']))}")
    d.formula(f"G_c(s) = {_forma_paralela_numerica(ctrl, ganhos)}")
    d.formula(f"G_c(s) = {razao_latex(mf['numeradorControlador'], mf['denominadorControlador'])}")
    valores = ", ".join(f"${r['simbolo']} = {N(ganhos[r['chave']])}$" for r in relacoes_de_ganho(ctrl))
    d.aviso("sucesso", f"**{ctrl['nome']}:** {valores}")


# Passo 8 ---------------------------------------------------------------------

def _descrever_polo(item):
    razao = f"{F(item['razao'], 2)}\\,\\sigma"
    return {
        "desejado": "\\text{polo desejado}",
        "cancelado": "\\text{cancelado por um zero de } T(s)",
        "rapido": f"\\text{{rápido: }} \\lvert \\operatorname{{Re}} \\rvert = {razao}",
        "influente": f"\\text{{próximo: }} \\lvert \\operatorname{{Re}} \\rvert = {razao}",
        "instavel": "\\text{instável}",
    }[item["classe"]]


def _concluir_dominancia(d, mf):
    if not mf["estavel"]:
        d.aviso(
            "erro",
            "A malha fechada tem polo no semiplano direito ou sobre o eixo $j\\omega$: o sistema é **instável**.",
        )
        return
    if mf["dominante"]:
        d.aviso(
            "sucesso",
            f"Os demais polos estão pelo menos {RAZAO_DE_DOMINANCIA} vezes mais à esquerda que $s_d$ ou foram "
            "cancelados por zeros: o par desejado domina a resposta.",
        )
        return
    d.aviso(
        "atencao",
        f"Há polo a menos de {RAZAO_DE_DOMINANCIA} vezes a parte real de $s_d$. A aproximação de segunda ordem "
        "fica fraca, e a resposta real (passo 9) pode fugir das especificações.",
    )


def _infinito_ou_numero(valor):
    return N(valor) if math.isfinite(valor) else "\\infty"


def _erro_estatico(d, projeto):
    mf, entrada = projeto["malhaFechada"], projeto["entrada"]
    erro = constantes_de_erro(mf["numeradorAberto"], mf["denominadorAberto"])
    unitaria = len(entrada["nH"]) == 1 and len(entrada["dH"]) == 1 and entrada["nH"][0] == entrada["dH"][0]
    I = _infinito_ou_numero
    d.paragrafo(f"**Constantes de erro estático** de $G_c(s)G(s)H(s)$, sistema tipo {erro['tipo']}:")
    d.formula(
        f"K_p = \\lim_{{s \\to 0}} G_cGH = {I(erro['kp'])}, \\qquad K_v = \\lim_{{s \\to 0}} s\\,G_cGH = {I(erro['kv'])}, "
        f"\\qquad K_a = \\lim_{{s \\to 0}} s^2 G_cGH = {I(erro['ka'])}"
    )
    d.formula(
        f"e_{{\\text{{degrau}}}} = \\frac{{1}}{{1 + K_p}} = {I(erro['erroDegrau'])}, \\qquad "
        f"e_{{\\text{{rampa}}}} = \\frac{{1}}{{K_v}} = {I(erro['erroRampa'])}, \\qquad "
        f"e_{{\\text{{parábola}}}} = \\frac{{1}}{{K_a}} = {I(erro['erroParabola'])}"
    )
    if not unitaria:
        d.paragrafo("Com $H(s) \\ne 1$, esses erros valem para o sinal atuante $E(s) = R(s) - H(s)C(s)$, não para $r - c$.")


def passo08(d, projeto):
    mf, des, ma, ctrl = projeto["malhaFechada"], projeto["desempenho"], projeto["malhaAberta"], projeto["controlador"]
    d.paragrafo("**Função de transferência de malha fechada:**")
    d.formula("T(s) = \\frac{G_c(s)G(s)}{1 + G_c(s)G(s)H(s)} = \\frac{N_c N_G D_H}{D_c D_G D_H + N_c N_G N_H}")
    d.formula(f"T(s) = {razao_latex(mf['numerador'], mf['caracteristica'])}")

    d.separador()
    d.paragrafo("**Equação característica:**")
    d.formula(f"{polinomio_latex(mf['caracteristica'])} = 0")
    d.paragrafo(f"**Polos de malha fechada** (com $\\sigma = {F(des['sigma'])}$):")
    for indice, item in enumerate(mf["polos"]):
        d.formula(f"s_{{{indice + 1}}} = {CL(item['ponto'])} \\quad {_descrever_polo(item)}")
    if mf["zeros"]:
        d.paragrafo("**Zeros de malha fechada:**")
        d.formula(", \\quad ".join(f"z_{{{i + 1}}} = {CL(z)}" for i, z in enumerate(mf["zeros"])))
    _concluir_dominancia(d, mf)

    d.separador()
    _erro_estatico(d, projeto)

    d.separador()
    pontos = [item["ponto"] for item in mf["polos"]] + list(mf["zeros"]) + [des["polo"], des["polo"].conjugate()]
    plano = G.Plano(pontos, f"Malha fechada com o {ctrl['nome']}")
    G.desenhar_retas_de_amortecimento(plano, des["zeta"])
    G.desenhar_polos_zeros(plano, [], mf["zeros"], legenda_zeros="Zeros de T(s)")
    G.desenhar_polos_desejados(plano, des["polo"], rotular=False)
    G.desenhar_polos_de_malha_fechada(plano, [item["ponto"] for item in mf["polos"]])
    d.figura(plano.figura())
    if ma["cancelamentos"]:
        d.paragrafo("Os cancelamentos da planta reaparecem aqui como polo e zero coincidentes de $T(s)$.")


# Passo 9 ---------------------------------------------------------------------

FOLGA_DE_COMPARACAO = 1e-3


def tempo_latex(valor):
    if valor is None:
        return "\\text{sem pico}"
    if not math.isfinite(valor):
        return "\\text{não acomoda}"
    return f"{F(valor, 3)}\\,\\text{{s}}"


def _tabela_degrau(referencia, metricas):
    linhas = [
        ["M_P", f"{F(referencia['sobressinal'], 2)}\\%", f"{F(metricas['sobressinal'], 2)}\\%"],
        ["t_p", tempo_latex(referencia["tempoDePico"]), tempo_latex(metricas["tempoDePico"])],
        ["t_s(2\\%)", tempo_latex(referencia["acomodacao2"]), tempo_latex(metricas["acomodacao2"])],
        ["t_s(5\\%)", tempo_latex(referencia["acomodacao5"]), tempo_latex(metricas["acomodacao5"])],
        ["y(\\infty)", "\\text{---}", F(metricas["valorFinal"])],
    ]
    corpo = " \\\\ ".join(" & ".join(linha) for linha in linhas)
    return (
        "\\begin{array}{l|c|c} \\text{Grandeza} & \\text{2ª ordem ideal} & \\text{Simulado} \\\\ \\hline "
        f"{corpo} \\end{{array}}"
    )


def _dentro_do_limite(medido, limite):
    return medido is not None and math.isfinite(medido) and medido <= limite * (1 + FOLGA_DE_COMPARACAO)


def _verificacoes(des, m):
    lista = []
    if "sobressinal" in des:
        ok = _dentro_do_limite(m["sobressinal"], des["sobressinal"])
        lista.append((ok, f"$M_P = {F(m['sobressinal'], 2)}\\%$ {'atende' if ok else 'não atende'} a "
                          f"$M_P \\le {N(des['sobressinal'])}\\%$."))
    if "acomodacao" in des:
        medido = m["acomodacao2"] if des["criterio"] == 2 else m["acomodacao5"]
        ok = _dentro_do_limite(medido, des["acomodacao"])
        lista.append((ok, f"$t_s({des['criterio']}\\%) = {tempo_latex(medido)}$ {'atende' if ok else 'não atende'} a "
                          f"$t_s < {N(des['acomodacao'])}\\,\\text{{s}}$."))
    if "tempoDePico" in des:
        ok = _dentro_do_limite(m["tempoDePico"], des["tempoDePico"])
        lista.append((ok, f"$t_p = {tempo_latex(m['tempoDePico'])}$ {'atende' if ok else 'não atende'} a "
                          f"$t_p \\le {N(des['tempoDePico'])}\\,\\text{{s}}$."))
    return lista


def passo09(d, projeto):
    resposta, mf, des = projeto["resposta"], projeto["malhaFechada"], projeto["desempenho"]
    if not mf["estavel"] or resposta is None:
        d.aviso("erro", "A malha fechada é instável, então não há resposta ao degrau para medir.")
        return
    metricas, simulacao = resposta["metricas"], resposta["simulacao"]
    if metricas is None:
        d.aviso("atencao", "O valor final de $y(t)$ é nulo, então sobressinal e acomodação não se aplicam.")
        return

    d.paragrafo(
        "Simulação exata de $T(s)$ em espaço de estados, com $x_{k+1} = e^{A\\,\\Delta t}x_k + \\Gamma$ "
        "para entrada em degrau."
    )
    d.formula(f"y(\\infty) = T(0) = {F(metricas['valorFinal'])}")
    if abs(simulacao["saidas"][0]) > 1e-9 * max(1, abs(metricas["valorFinal"])):
        d.aviso(
            "informacao",
            "$G_c(s)G(s)$ tem tantos zeros quanto polos, então a saída salta para "
            f"$y(0^+) = {F(simulacao['saidas'][0])}$ no instante do degrau.",
        )

    d.separador()
    d.formula(_tabela_degrau(des["referencia"], metricas))
    lista = _verificacoes(des, metricas)
    for ok, texto in lista:
        d.aviso("sucesso" if ok else "atencao", texto)
    if any(not ok for ok, _ in lista):
        d.paragrafo(
            "A diferença vem dos polos e zeros que a aproximação de segunda ordem ignora (passo 8). "
            "Para ganhar folga, refaça o projeto com especificações um pouco mais rígidas."
        )

    d.separador()
    saidas = simulacao["saidas"]
    vf = metricas["valorFinal"]
    grafico = G.GraficoTemporal(
        simulacao["duracao"], float(saidas.min()),
        max(float(saidas.max()), vf * (1 + des["referencia"]["sobressinal"] / 100)),
        "Resposta ao degrau unitário",
    )
    G.desenhar_faixa(grafico, vf, (des.get("criterio") or 2) / 100)
    G.desenhar_nivel(grafico, vf, G.CORES["valorFinal"], "Valor final")
    if "sobressinal" in des:
        G.desenhar_nivel(grafico, vf * (1 + des["sobressinal"] / 100), G.CORES["limite"],
                         "Limite de sobressinal", (0, (3, 3)))
    if "acomodacao" in des:
        G.desenhar_instante(grafico, des["acomodacao"], G.CORES["limite"], "Limite de acomodação")
    if "tempoDePico" in des:
        G.desenhar_instante(grafico, des["tempoDePico"], G.CORES["desejado"], "Tempo de pico pedido")
    G.desenhar_resposta(grafico, simulacao)
    d.figura(grafico.figura())


# Passo 10 --------------------------------------------------------------------

FOLGA_DO_CIRCULO = 1e-6
TERMOS_POR_LINHA = 3
SINAIS = {
    "controlador": {"nome": "G_c", "saida": "u", "entrada": "e"},
    "malha": {"nome": "G_{MA}", "saida": "y", "entrada": "u"},
    "planta": {"nome": "G", "saida": "y", "entrada": "u"},
}


def _potencias_negativas_latex(coeficientes):
    partes = []
    for i, c in enumerate(coeficientes):
        if abs(c) < 1e-12:
            continue
        absoluto = abs(c)
        potencia = "" if i == 0 else f"z^{{-{i}}}"
        numero = "" if i > 0 and abs(absoluto - 1) < 1e-12 else N(absoluto)
        juncao = "\\," if numero and potencia else ""
        termo = f"{numero}{juncao}{potencia}"
        if not partes:
            partes.append(f"-{termo}" if c < 0 else termo)
        else:
            partes.append(f" - {termo}" if c < 0 else f" + {termo}")
    return "".join(partes) if partes else "0"


def _atraso_latex(sinal, i):
    return f"{sinal}[k]" if i == 0 else f"{sinal}[k-{i}]"


def _parcelas_latex(termos):
    partes = []
    for coeficiente, texto in termos:
        if abs(coeficiente) < 1e-12:
            continue
        corpo = texto if abs(abs(coeficiente) - 1) < 1e-12 else f"{N(abs(coeficiente))}\\,{texto}"
        if not partes:
            partes.append(f"-{corpo}" if coeficiente < 0 else corpo)
        else:
            partes.append(f" - {corpo}" if coeficiente < 0 else f" + {corpo}")
    return partes or ["0"]


def _igualdade_em_linhas(esquerda, partes):
    if len(partes) <= TERMOS_POR_LINHA + 1:
        return f"{esquerda} = {''.join(partes)}"
    linhas = ["".join(partes[i:i + TERMOS_POR_LINHA]) for i in range(0, len(partes), TERMOS_POR_LINHA)]
    corpo = " \\\\ & ".join(linhas)
    return f"\\begin{{aligned}} {esquerda} = {{}} & {corpo} \\end{{aligned}}"


def _diferencas(d, disc, sinais):
    if not disc["causal"] or disc["diferencas"] is None:
        d.aviso(
            "atencao",
            "O numerador ficou com grau maior que o denominador: a função discreta não é causal, e a saída "
            "dependeria de amostras futuras. Isso acontece quando a função contínua tem mais zeros que polos "
            "e o método não cria polos novos, como Euler (Forward).",
        )
        return
    entrada, saida = disc["diferencas"]["entrada"], disc["diferencas"]["saida"]
    termos = [(c, _atraso_latex(sinais["entrada"], i)) for i, c in enumerate(entrada)]
    termos += [(-c, _atraso_latex(sinais["saida"], i + 1)) for i, c in enumerate(saida[1:])]
    d.paragrafo("**Equação de diferenças** (multiplicando cruzado e voltando ao tempo):")
    d.formula(_igualdade_em_linhas(f"{sinais['saida']}[k]", _parcelas_latex(termos)))


def _classificar_polo_discreto(item):
    if item["modulo"] < 1 - FOLGA_DO_CIRCULO:
        return "\\text{dentro do círculo unitário}"
    if item["modulo"] <= 1 + FOLGA_DO_CIRCULO:
        return "\\text{sobre o círculo unitário}"
    return "\\text{fora do círculo unitário}"


def _polos_discretos(d, disc):
    if not disc["polos"]:
        return
    d.paragrafo("**Polos discretos:**")
    for i, item in enumerate(disc["polos"]):
        d.formula(
            f"z_{{{i + 1}}} = {CL(item['ponto'])}, \\quad |z_{{{i + 1}}}| = {F(item['modulo'])} \\quad "
            f"{_classificar_polo_discreto(item)}"
        )
    fora = any(item["modulo"] > 1 + FOLGA_DO_CIRCULO for item in disc["polos"])
    sobre = any(abs(item["modulo"] - 1) <= FOLGA_DO_CIRCULO for item in disc["polos"])
    if fora and disc["continuoEstavel"]:
        d.aviso(
            "atencao",
            f"Com $T = {N(disc['periodo'])}\\,\\text{{s}}$, o método leva polos estáveis em $s$ para fora "
            "do círculo unitário: o modelo discreto é instável. Um período menor ou o método de Tustin evitam isso.",
        )
    elif fora:
        d.aviso("informacao", "Há polo fora do círculo unitário, mas a função contínua já tinha polo instável.")
    elif sobre:
        extra = (
            ", e com Tustin a imagem de $s = \\infty$ é $z = -1$, que aparece quando a função contínua tem mais "
            "zeros que polos." if disc["id"] == "tustin" else "."
        )
        d.aviso("informacao", f"Há polo sobre o círculo unitário. Um integrador em $s = 0$ vai para $z = 1${extra}")
    else:
        d.aviso("sucesso", "Todos os polos ficaram dentro do círculo unitário.")


def _substituicao(d, disc):
    metodo = disc["metodo"]
    d.formula(f"{metodo['substituicao']} = {razao_latex(disc['alfa'], disc['beta'], 'z')}")
    beta = P.normalizar(disc["beta"])
    if len(beta) == 1 and abs(beta[0] - 1) < 1e-12:
        d.paragrafo("Substituindo:")
    else:
        d.paragrafo(
            f"Substituindo e multiplicando numerador e denominador por $({polinomio_latex(beta, 'z')})^{{{disc['ordem']}}}$:"
        )
    d.formula(f"N(z) = {polinomio_latex(disc['numeradorSubstituido'], 'z')}")
    d.formula(f"D(z) = {polinomio_latex(disc['denominadorSubstituido'], 'z')}")


def _fator_do_polo_latex(polo, variavel):
    if abs(polo.imag) < 1e-10:
        if abs(polo.real) < 1e-12:
            return variavel
        return f"{variavel} + {N(-polo.real)}" if polo.real < 0 else f"{variavel} - {N(polo.real)}"
    return f"{variavel} - ({CL(polo)})"


def _coeficiente_latex(valor):
    return N(valor.real) if abs(valor.imag) < 1e-10 else f"({CL(valor)})"


def _segurador(d, disc):
    d.formula("H(z) = \\frac{z - 1}{z}\\;\\mathcal{Z}\\left\\{\\frac{G(s)}{s}\\right\\}")
    fracoes = disc.get("fracoes")
    if not fracoes:
        d.paragrafo(
            "Como $G(s)/s$ tem polo repetido, o resultado sai da discretização exata em espaço de estados, com "
            "$\\Phi = e^{AT}$ e $\\Gamma = \\int_0^T e^{A\\tau}B\\,d\\tau$, que equivale à mesma fórmula."
        )
        return
    d.paragrafo("Frações parciais de $G(s)/s$:")
    termos = " + ".join(
        f"\\frac{{{_coeficiente_latex(f['residuo'])}}}{{{_fator_do_polo_latex(f['polo'], 's')}}}" for f in fracoes
    )
    d.formula(f"\\frac{{G(s)}}{{s}} = {termos}")
    d.paragrafo("Cada termo $\\frac{r}{s - p}$ vira $\\frac{r\\,z}{z - e^{pT}}$:")
    termos_z = " + ".join(
        f"\\frac{{{_coeficiente_latex(f['residuo'])}\\,z}}{{{_fator_do_polo_latex(f['amostrado'], 'z')}}}"
        for f in fracoes
    )
    d.formula(f"\\mathcal{{Z}}\\left\\{{\\frac{{G(s)}}{{s}}\\right\\}} = {termos_z}")
    d.paragrafo("Multiplicando por $\\frac{z - 1}{z}$ e juntando os termos:")


def renderizar_discretizacao(d, disc):
    if disc.get("erro"):
        d.aviso("erro", f"Não foi possível discretizar: {disc['erro']}")
        return
    sinais = SINAIS.get(disc["alvo"], SINAIS["planta"])
    metodo, periodo = disc["metodo"], disc["periodo"]
    nome = ALVOS.get(disc["alvo"], "G(s)")

    d.paragrafo(f"**Função discretizada:** ${nome}$")
    d.formula(f"{nome} = {razao_latex(disc['numeradorS'], disc['denominadorS'])}")
    d.separador()
    d.paragrafo(f"**Método:** {metodo['nome']}, com $T = {N(periodo)}\\,\\text{{s}}$")
    if metodo.get("segurador"):
        _segurador(d, disc)
    else:
        _substituicao(d, disc)
    if disc["cancelados"] > 0:
        expoente = f"^{{{disc['cancelados']}}}" if disc["cancelados"] > 1 else ""
        d.aviso("informacao", f"Numerador e denominador tinham o fator $z{expoente}$ em comum, que foi cancelado.")

    d.separador()
    d.paragrafo("Dividindo pelo coeficiente líder do denominador:")
    d.formula(f"{sinais['nome']}(z) = {razao_latex(disc['numeradorZ'], disc['denominadorZ'], 'z')}")
    if disc["causal"]:
        d.formula(
            f"{sinais['nome']}(z) = \\frac{{{sinais['saida'].upper()}(z)}}{{{sinais['entrada'].upper()}(z)}} = "
            f"\\frac{{{_potencias_negativas_latex(disc['diferencas']['entrada'])}}}"
            f"{{{_potencias_negativas_latex(disc['denominadorZ'])}}}"
        )
    _diferencas(d, disc, sinais)
    d.separador()
    _polos_discretos(d, disc)


def passo10(d, projeto):
    renderizar_discretizacao(d, projeto["discretizacao"])


# LGR compensado --------------------------------------------------------------

def grafico_completo(pai, projeto, aberto=False):
    v, ma, zero, des, mf, modulo = (
        projeto["varredura"], projeto["malhaAberta"], projeto["zero"], projeto["desempenho"],
        projeto["malhaFechada"], projeto["modulo"],
    )
    ctrl = projeto.get("controladorFinal") or projeto["controlador"]
    corpo = pai.secao("**LGR do sistema compensado** (verificação)", aberto)
    plano = G.Plano(
        pontos_notaveis({**projeto, "controlador": ctrl}, malha_fechada=True),
        f"Lugar geométrico das raízes com o {ctrl['nome']}",
    )
    G.desenhar_retas_de_amortecimento(plano, des["zeta"])
    G.desenhar_ramos(plano, v)
    G.desenhar_polos_zeros(plano, ma["polos"], ma["zeros"])
    G.desenhar_controlador(plano, ctrl, zero)
    G.desenhar_polos_desejados(plano, des["polo"], rotular=False)
    G.desenhar_polos_de_malha_fechada(plano, [item["ponto"] for item in mf["polos"]])
    corpo.figura(plano.figura())
    corpo.paragrafo(
        f"Varredura de ${ctrl['simboloGanho']}$ de $0$ até ${formatar_g(v['ganhoMaximo'], 4)}$. Os quadrados marcam "
        f"os polos de malha fechada em ${ctrl['simboloGanho']} = {formatar_g(modulo['kc'], 6)}$, e o par desejado "
        "cai sobre os ramos."
    )


# Índice ----------------------------------------------------------------------

PASSOS = [
    {"titulo": "**Passo 1:** Especificações, $\\zeta$ e $\\omega_n$", "renderizar": passo01},
    {"titulo": "**Passo 2:** Polos dominantes desejados", "renderizar": passo02},
    {"titulo": "**Passo 3:** Malha aberta com o controlador", "renderizar": passo03},
    {"titulo": "**Passo 4:** Critério de ângulo em $s_d$", "renderizar": passo04},
    {"titulo": "**Passo 5:** Localização do zero do controlador", "renderizar": passo05,
     "titulo_para": titulo05, "requer_viabilidade": True},
    {"titulo": "**Passo 6:** Critério de módulo e $K_c$", "renderizar": passo06,
     "titulo_para": titulo06, "requer_viabilidade": True},
    {"titulo": "**Passo 6b:** Parte em atraso de fase", "renderizar": passo06b, "requer_viabilidade": True,
     "aplicavel": lambda projeto: bool(projeto.get("atraso"))},
    {"titulo": "**Passo 7:** Ganhos do controlador", "renderizar": passo07, "requer_viabilidade": True},
    {"titulo": "**Passo 8:** Malha fechada, dominância e erro (verificação)", "renderizar": passo08,
     "requer_viabilidade": True, "fechado": True},
    {"titulo": "**Passo 9:** Resposta ao degrau unitário (verificação)", "renderizar": passo09,
     "requer_viabilidade": True, "fechado": True},
    {"titulo": "**Passo 10:** Discretização", "renderizar": passo10, "requer_viabilidade": True,
     "aplicavel": lambda projeto: projeto.get("discretizacao") is not None},
]
