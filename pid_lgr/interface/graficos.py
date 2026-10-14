"""Plano s e gráfico temporal em matplotlib, com as mesmas camadas da versão web."""

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from ..formatacao.numero import fixo  # noqa: E402

CORES = {
    "polo": "#d0342c",
    "zero": "#1f9d55",
    "ramo": "#2b6cd9",
    "desejado": "#a435c9",
    "desejadoBorda": "#5b1a72",
    "controlador": "#e08b1a",
    "malhaFechada": "#12b0c8",
    "malhaFechadaBorda": "#123c8c",
    "amortecimento": "#7b8794",
    "resposta": "#2b6cd9",
    "valorFinal": "#46535f",
    "faixa": "#1f9d55",
    "limite": "#d0342c",
    "eixo": "#9aa5b1",
    "grade": "#e8edf3",
    "texto": "#16202b",
}

AMPLITUDE_MINIMA = 1
FATOR_MARGEM = 0.18
MARGEM_MINIMA = 0.5

plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.edgecolor": "#c3ccd6",
    "axes.labelcolor": CORES["texto"],
    "xtick.color": "#46535f",
    "ytick.color": "#46535f",
    "legend.fontsize": 8,
    "legend.frameon": False,
    "svg.fonttype": "none",
})


def limites_brutos(pontos):
    if not pontos:
        return -1.0, 1.0, -1.0, 1.0
    x_min = min(p.real for p in pontos)
    x_max = max(p.real for p in pontos)
    modulo_imaginario = max(abs(p.imag) for p in pontos)
    amplitude = max(x_max - x_min, 2 * modulo_imaginario, AMPLITUDE_MINIMA)
    margem = max(MARGEM_MINIMA, FATOR_MARGEM * amplitude)
    limite_imaginario = max(modulo_imaginario + margem, (x_max - x_min) * 0.35, margem)
    return x_min - margem, x_max + margem, -limite_imaginario, limite_imaginario


class _Base:
    def __init__(self, largura, altura):
        self.fig, self.ax = plt.subplots(figsize=(largura, altura), dpi=110)
        self._legendas = set()

    def rotulo_de_legenda(self, texto):
        if not texto or texto in self._legendas:
            return "_nolegend_"
        self._legendas.add(texto)
        return texto

    def _finalizar_legenda(self, compacto):
        if compacto or not self._legendas:
            return
        self.ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3, handletextpad=0.5,
                       columnspacing=1.4)


class Plano(_Base):
    def __init__(self, pontos, titulo="", compacto=False):
        x_min, x_max, y_min, y_max = limites_brutos(pontos)
        proporcao = (x_max - x_min) / (y_max - y_min)
        largura = 3.6 if compacto else 7.0
        altura = min(max(largura / proporcao, 2.6 if compacto else 3.4), 3.4 if compacto else 6.0)
        super().__init__(largura, altura + (0 if compacto else 0.6))
        self.compacto = compacto
        self.janela = (x_min, x_max, y_min, y_max)
        ax = self.ax
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.axhline(0, color=CORES["eixo"], linewidth=0.9, zorder=1)
        ax.axvline(0, color=CORES["eixo"], linewidth=0.9, zorder=1)
        ax.grid(True, color=CORES["grade"], linewidth=0.7, zorder=0)
        ax.set_axisbelow(True)
        if titulo:
            ax.set_title(titulo)
        if not compacto:
            ax.set_xlabel("Real (σ)")
            ax.set_ylabel("Imaginário (jω)")
        else:
            ax.tick_params(labelsize=7)

    # Marcadores ------------------------------------------------------------
    def cruz(self, ponto, cor, legenda=None, tamanho=8, espessura=2.2):
        self.ax.plot([ponto.real], [ponto.imag], marker="x", markersize=tamanho, markeredgewidth=espessura,
                     color=cor, linestyle="none", zorder=5, label=self.rotulo_de_legenda(legenda))

    def circulo(self, ponto, cor, legenda=None, tamanho=8, espessura=2.0):
        self.ax.plot([ponto.real], [ponto.imag], marker="o", markersize=tamanho, markeredgewidth=espessura,
                     markerfacecolor="none", color=cor, linestyle="none", zorder=5,
                     label=self.rotulo_de_legenda(legenda))

    def estrela(self, ponto, legenda=None):
        self.ax.plot([ponto.real], [ponto.imag], marker="*", markersize=13, markerfacecolor=CORES["desejado"],
                     markeredgecolor=CORES["desejadoBorda"], markeredgewidth=0.9, linestyle="none", zorder=7,
                     label=self.rotulo_de_legenda(legenda))

    def quadrado(self, ponto, legenda=None):
        self.ax.plot([ponto.real], [ponto.imag], marker="s", markersize=6.5, markerfacecolor=CORES["malhaFechada"],
                     markeredgecolor=CORES["malhaFechadaBorda"], markeredgewidth=1.2, linestyle="none", zorder=8,
                     label=self.rotulo_de_legenda(legenda))

    def linha(self, a, b, cor, estilo="--", largura=1.2, opacidade=1.0, legenda=None):
        self.ax.plot([a.real, b.real], [a.imag, b.imag], color=cor, linestyle=estilo, linewidth=largura,
                     alpha=opacidade, zorder=2, label=self.rotulo_de_legenda(legenda))

    def caminho(self, pontos, cor, largura=2.0, opacidade=0.95, legenda=None):
        self.ax.plot(np.real(pontos), np.imag(pontos), color=cor, linewidth=largura, alpha=opacidade,
                     solid_joinstyle="round", solid_capstyle="round", zorder=3,
                     label=self.rotulo_de_legenda(legenda))

    def rotulo(self, ponto, texto, cor):
        if self.compacto:
            return
        self.ax.annotate(texto, (ponto.real, ponto.imag), xytext=(7, 7), textcoords="offset points",
                         color=cor, fontsize=8, fontweight="bold", zorder=9)

    def figura(self):
        self._finalizar_legenda(self.compacto)
        self.fig.tight_layout()
        # Mesma escala nos dois eixos: amplia a janela para a proporção da área do gráfico.
        caixa = self.ax.get_position()
        largura_fig, altura_fig = self.fig.get_size_inches()
        largura, altura = caixa.width * largura_fig, caixa.height * altura_fig
        x_min, x_max, y_min, y_max = self.janela
        escala = max((x_max - x_min) / largura, (y_max - y_min) / altura)
        cx, cy = (x_min + x_max) / 2, (y_min + y_max) / 2
        self.ax.set_xlim(cx - escala * largura / 2, cx + escala * largura / 2)
        self.ax.set_ylim(cy - escala * altura / 2, cy + escala * altura / 2)
        return self.fig


class GraficoTemporal(_Base):
    def __init__(self, duracao, minimo, maximo, titulo):
        super().__init__(7.0, 4.3)
        inferior = min(0.0, minimo)
        superior = max(0.0, maximo)
        folga = max(superior - inferior, 1e-9) * 0.08
        self.janela = (0.0, duracao, inferior - folga, superior + folga)
        ax = self.ax
        ax.set_xlim(0, duracao)
        ax.set_ylim(inferior - folga, superior + folga)
        ax.grid(True, color=CORES["grade"], linewidth=0.7)
        ax.set_axisbelow(True)
        ax.axhline(0, color=CORES["eixo"], linewidth=0.9)
        ax.set_title(titulo)
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Saída y(t)")

    def figura(self):
        self._finalizar_legenda(False)
        self.fig.tight_layout()
        return self.fig


# Camadas do plano s ----------------------------------------------------------

def desenhar_ramos(plano, varredura, legenda="Ramos do LGR"):
    x_min, x_max, y_min, y_max = plano.janela
    folga_x = (x_max - x_min) * 3
    folga_y = (y_max - y_min) * 3
    pontos = varredura["pontos"]
    dentro = (
        (pontos.real >= x_min - folga_x) & (pontos.real <= x_max + folga_x)
        & (pontos.imag >= y_min - folga_y) & (pontos.imag <= y_max + folga_y)
    )
    for j in range(varredura["ramos"]):
        ramo = pontos[:, j].copy()
        ramo[~dentro[:, j]] = complex(math.nan, math.nan)
        plano.caminho(ramo, CORES["ramo"], largura=2.2, legenda=legenda)


def desenhar_polos_zeros(plano, polos, zeros, legenda_polos=None, legenda_zeros=None):
    for p in polos:
        plano.cruz(p, CORES["polo"], legenda_polos or "Polos de G(s)H(s)")
    for z in zeros:
        plano.circulo(z, CORES["zero"], legenda_zeros or "Zeros de G(s)H(s)")


def desenhar_retas_de_amortecimento(plano, zeta):
    angulo = math.acos(zeta)
    x_min, x_max, y_min, y_max = plano.janela
    comprimento = 2 * math.hypot(x_max - x_min, y_max - y_min)
    for sinal in (1, -1):
        plano.linha(0j, complex(-comprimento * math.cos(angulo), sinal * comprimento * math.sin(angulo)),
                    CORES["amortecimento"], estilo=(0, (6, 5)), largura=1.2,
                    legenda=f"Reta de ζ = {fixo(zeta, 4)}")


def desenhar_polos_desejados(plano, polo, rotular=True):
    for ponto in (polo, polo.conjugate()):
        plano.estrela(ponto, "Polos desejados")
    if rotular:
        plano.rotulo(polo, f"sd = {fixo(polo.real, 2)} ± j{fixo(polo.imag, 2)}", CORES["desejadoBorda"])


def desenhar_fixos_do_controlador(plano, controlador):
    polos = [0j] * controlador["polosNaOrigem"] + [complex(-v, 0) for v in controlador.get("polosFixos", [])]
    zeros = [complex(-v, 0) for v in controlador.get("zerosFixos", [])]
    rotulo_polo = "Polo do controlador" if controlador["polosNaOrigem"] > 0 else "Polo dado do controlador"
    for ponto in polos:
        plano.cruz(ponto, CORES["controlador"], rotulo_polo, tamanho=10, espessura=2.4)
    for ponto in zeros:
        plano.circulo(ponto, CORES["controlador"], "Zero dado do controlador", tamanho=10, espessura=2.4)


def desenhar_controlador(plano, controlador, zero, rotular=True):
    desenhar_fixos_do_controlador(plano, controlador)
    if controlador["polosLivres"] > 0:
        plano.cruz(zero["ponto"], CORES["controlador"], "Polo do controlador", tamanho=10, espessura=2.4)
        if rotular:
            plano.rotulo(zero["ponto"], f"-{controlador['simboloLivre']} = {fixo(-zero['valor'], 3)}",
                         CORES["controlador"])
        return
    legenda = "Zero duplo do controlador" if controlador["zeros"] > 1 else "Zero do controlador"
    plano.circulo(zero["ponto"], CORES["controlador"], legenda, tamanho=11, espessura=2.4)
    if controlador["zeros"] > 1:
        plano.circulo(zero["ponto"], CORES["controlador"], legenda, tamanho=5, espessura=1.6)
    if rotular:
        plano.rotulo(zero["ponto"], f"-z = {fixo(-zero['valor'], 3)}", CORES["controlador"])


def desenhar_vetores(plano, origens, ponto, cor):
    for origem in origens:
        plano.linha(origem, ponto, cor, estilo=(0, (3, 4)), largura=1.0, opacidade=0.7)


def desenhar_polos_de_malha_fechada(plano, polos):
    for ponto in polos:
        plano.quadrado(ponto, "Polos de malha fechada")


# Camadas do gráfico temporal ------------------------------------------------

def desenhar_resposta(grafico, simulacao, cor=None, legenda="y(t)", tracejado=None, espessura=2.2):
    grafico.ax.plot(simulacao["tempos"], simulacao["saidas"], color=cor or CORES["resposta"], linewidth=espessura,
                    linestyle=tracejado or "-", zorder=4, label=grafico.rotulo_de_legenda(legenda))


def desenhar_nivel(grafico, valor, cor, rotulo, tracejado=(0, (6, 5))):
    grafico.ax.axhline(valor, color=cor, linewidth=1.2, linestyle=tracejado, zorder=2,
                       label=grafico.rotulo_de_legenda(rotulo))


def desenhar_faixa(grafico, valor_final, faixa):
    desvio = abs(valor_final) * faixa
    rotulo = f"Faixa de ±{fixo(faixa * 100, 0)}%"
    for nivel in (valor_final - desvio, valor_final + desvio):
        grafico.ax.axhline(nivel, color=CORES["faixa"], linewidth=1.0, linestyle=(0, (2, 4)), zorder=2,
                           label=grafico.rotulo_de_legenda(rotulo))


def desenhar_instante(grafico, tempo, cor, rotulo):
    if tempo is None or not math.isfinite(tempo) or tempo > grafico.janela[1]:
        return
    grafico.ax.axvline(tempo, color=cor, linewidth=1.2, linestyle=(0, (4, 4)), zorder=2,
                       label=grafico.rotulo_de_legenda(rotulo))
