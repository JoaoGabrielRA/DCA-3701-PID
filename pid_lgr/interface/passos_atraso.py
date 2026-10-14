"""Roteiro próprio do compensador em atraso de fase pelo erro (seção 4.6 da apostila)."""

from ..formatacao.latex import complexo_latex, razao_latex
from ..formatacao.numero import fixo_latex, numero_latex
from . import graficos as G
from .passos import renderizar_parte, tempo_latex

N = numero_latex
F = fixo_latex
CL = complexo_latex


def passo1(d, projeto):
    entrada, ajuste, ganho, dominante, ma = (
        projeto["entrada"], projeto["ajuste"], projeto["ganho"], projeto["dominante"], projeto["malhaAberta"]
    )
    d.formula(f"G(s)H(s) = {razao_latex(ma['numerador'], ma['denominador'])}")
    if ajuste:
        zeta = entrada["atraso"]["zeta"]
        d.paragrafo(
            f"Procura-se, sobre a reta de $\\zeta = {N(zeta)}$, o ponto $s_1$ do LGR, onde a condição de ângulo vale:"
        )
        d.formula(
            f"\\angle G(s_1)H(s_1) = 180^\\circ \\;\\Rightarrow\\; s_1 = {CL(ajuste['ponto'])}, "
            f"\\qquad \\omega_n = {F(ajuste['omegaN'])}"
        )
        d.paragrafo("O ganho sai da condição de módulo:")
        d.formula(f"K = \\frac{{1}}{{|G(s_1)H(s_1)|}} = {N(ganho)}")
        return
    d.paragrafo("O ganho de $G(s)$ fica como está ($K = 1$). Polo dominante de malha fechada do sistema original:")
    d.formula(f"s_1 = {CL(dominante)}")


def passo2(d, projeto):
    d.paragrafo(
        "O controlador em atraso aumenta a constante de erro sem mexer muito no transitório: "
        "zero e polo ficam próximos entre si e da origem."
    )
    renderizar_parte(d, projeto["parte"], "s_1", "KGH")


def passo3(d, projeto):
    ganho, parte, comp = projeto["ganho"], projeto["parte"], projeto["compensada"]
    d.formula(
        f"G_c(s) = {N(ganho)}\\,\\frac{{s + {N(parte['zero'])}}}{{s + {N(parte['polo'])}}} = "
        f"{razao_latex(comp['numeradorControlador'], comp['denominadorControlador'])}"
    )
    d.formula(f"{parte['simbolo']}^{{\\text{{comp}}}} = {N(projeto['constanteFinal'])}")
    d.aviso(
        "sucesso",
        f"**Atraso:** $z = {N(parte['zero'])}$, $p = {N(parte['polo'])}$, $\\beta = {N(parte['beta'])}$, "
        f"$K = {N(ganho)}$",
    )


def _listar_polos(d, rotulo, polos):
    d.paragrafo(rotulo)
    d.formula(", \\quad ".join(f"s_{{{i + 1}}} = {CL(p)}" for i, p in enumerate(polos)))


def passo4(d, projeto):
    original, comp = projeto["original"], projeto["compensada"]
    _listar_polos(d, "**Sem o atraso:**", original["polos"])
    _listar_polos(d, "**Com o atraso:**", comp["polos"])
    d.formula(f"s_1 = {CL(projeto['dominante'])} \\;\\longrightarrow\\; {CL(projeto['novoDominante'])}")
    d.paragrafo(
        "O par dominante quase não se move. O polo e o zero novos perto da origem quase se cancelam, "
        "mas deixam uma cauda lenta na resposta."
    )
    d.separador()
    plano = G.Plano(list(original["polos"]) + list(comp["polos"]) + list(comp["zeros"]), "Polos de malha fechada")
    if projeto["entrada"]["atraso"].get("zeta"):
        G.desenhar_retas_de_amortecimento(plano, projeto["entrada"]["atraso"]["zeta"])
    G.desenhar_polos_zeros(plano, original["polos"], [], legenda_polos="Sem o atraso")
    G.desenhar_polos_de_malha_fechada(plano, comp["polos"])
    d.figura(plano.figura())


def passo5(d, projeto):
    original, comp = projeto["original"], projeto["compensada"]
    if not original["resposta"] or not comp["resposta"]:
        d.aviso("erro", "Uma das malhas fechadas é instável, então não há resposta ao degrau para comparar.")
        return
    mo, mc = original["resposta"]["metricas"], comp["resposta"]["metricas"]
    if mo is None or mc is None:
        d.aviso("atencao", "O valor final de $y(t)$ é nulo, então sobressinal e acomodação não se aplicam.")
        return
    linhas = [
        ["M_P", f"{F(mo['sobressinal'], 2)}\\%", f"{F(mc['sobressinal'], 2)}\\%"],
        ["t_p", tempo_latex(mo["tempoDePico"]), tempo_latex(mc["tempoDePico"])],
        ["t_s(2\\%)", tempo_latex(mo["acomodacao2"]), tempo_latex(mc["acomodacao2"])],
        ["y(\\infty)", F(mo["valorFinal"]), F(mc["valorFinal"])],
    ]
    corpo = " \\\\ ".join(" & ".join(linha) for linha in linhas)
    d.formula(
        "\\begin{array}{l|c|c} \\text{Grandeza} & \\text{Sem atraso} & \\text{Com atraso} \\\\ \\hline "
        f"{corpo} \\end{{array}}"
    )
    d.separador()
    so, sc = original["resposta"]["simulacao"], comp["resposta"]["simulacao"]
    grafico = G.GraficoTemporal(
        max(so["duracao"], sc["duracao"]),
        float(min(so["saidas"].min(), sc["saidas"].min())),
        float(max(so["saidas"].max(), sc["saidas"].max())),
        "Resposta ao degrau unitário",
    )
    G.desenhar_nivel(grafico, mc["valorFinal"], G.CORES["valorFinal"], "Valor final")
    G.desenhar_resposta(grafico, so, cor=G.CORES["amortecimento"], legenda="Sem o atraso", tracejado=(0, (6, 4)),
                        espessura=2)
    G.desenhar_resposta(grafico, sc, legenda="Com o atraso")
    d.figura(grafico.figura())


PASSOS_DO_ATRASO = [
    {"titulo": "**Passo 1:** Ganho de malha aberta", "renderizar": passo1},
    {"titulo": "**Passo 2:** Constante de erro e parte em atraso", "renderizar": passo2},
    {"titulo": "**Passo 3:** Controlador projetado", "renderizar": passo3},
    {"titulo": "**Passo 4:** Malha fechada com e sem o atraso (verificação)", "renderizar": passo4, "fechado": True},
    {"titulo": "**Passo 5:** Resposta ao degrau (verificação)", "renderizar": passo5, "fechado": True},
]
