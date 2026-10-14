"""Polinômios, razões e complexos em LaTeX."""

from ..nucleo import polinomio as P
from .numero import numero_latex

EPS = 1e-12


def polinomio_latex(coeficientes, variavel="s"):
    grau = len(coeficientes) - 1
    partes = []
    for k, c in enumerate(coeficientes):
        expoente = grau - k
        if abs(c) < EPS:
            continue
        absoluto = abs(c)
        if expoente == 0:
            coeficiente_texto = numero_latex(absoluto)
        elif abs(absoluto - 1) < EPS:
            coeficiente_texto = ""
        else:
            coeficiente_texto = numero_latex(absoluto)

        if expoente == 0:
            termo = coeficiente_texto
        elif expoente == 1:
            termo = f"{coeficiente_texto}{variavel}" if coeficiente_texto else variavel
        else:
            termo = (
                f"{coeficiente_texto}{variavel}^{{{expoente}}}" if coeficiente_texto else f"{variavel}^{{{expoente}}}"
            )

        if not partes:
            partes.append(f"-{termo}" if c < 0 else termo)
        else:
            partes.append(f" - {termo}" if c < 0 else f" + {termo}")
    return "".join(partes) if partes else "0"


def razao_latex(numerador, denominador, variavel="s"):
    den = P.normalizar(denominador)
    num = polinomio_latex(numerador, variavel)
    if len(den) == 1 and abs(den[0] - 1) < 1e-12:
        return num
    return f"\\frac{{{num}}}{{{polinomio_latex(den, variavel)}}}"


def complexo_latex(z, decimais=4):
    z = complex(z)
    re = float(f"{z.real:.{decimais}f}")
    im = float(f"{z.imag:.{decimais}f}")
    if abs(im) < 1e-10:
        return numero_latex(re)
    if abs(re) < 1e-10:
        if abs(abs(im) - 1) < 1e-10:
            return "j" if im > 0 else "-j"
        return f"{numero_latex(im)}j"
    sinal = "+" if im >= 0 else "-"
    return f"{numero_latex(re)} {sinal} {numero_latex(abs(im))}j"


def rotular_contribuicoes(itens, simbolo):
    contador = 0
    saida = []
    for item in itens:
        if item["origem"] == "controlador":
            saida.append({**item, "rotulo": f"{simbolo}_{{c}}"})
            continue
        contador += 1
        saida.append({**item, "rotulo": f"{simbolo}_{{{contador}}}"})
    return saida
