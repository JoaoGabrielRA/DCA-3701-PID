"""Leitura de polinômios digitados como expressão (5(s+3), s(s+4)) ou como coeficientes."""

import math
import re

from . import polinomio as P

MAIOR_EXPOENTE = 30
SINAIS_DE_EXPRESSAO = re.compile(r"[sS()^*+]")
NUMERO = re.compile(r"^(\d+([.,]\d*)?|[.,]\d+)")


def _numero(texto):
    try:
        valor = float(texto.replace(",", ".", 1))
    except ValueError:
        return None
    return valor if math.isfinite(valor) else None


def interpretar_coeficientes(texto):
    if not isinstance(texto, str):
        return None
    itens = [item for item in re.split(r"[\s;]+", texto.strip()) if item]
    if not itens:
        return None
    valores = [_numero(item) for item in itens]
    if any(valor is None for valor in valores):
        return None
    return valores


def _separar_simbolos(texto):
    simbolos = []
    i = 0
    while i < len(texto):
        atual = texto[i]
        if atual.isspace():
            i += 1
            continue
        numero = NUMERO.match(texto[i:])
        if numero:
            simbolos.append(("numero", float(numero.group(0).replace(",", "."))))
            i += len(numero.group(0))
            continue
        if atual in "sS":
            simbolos.append(("s", None))
        elif atual in "+-*^()":
            simbolos.append((atual, None))
        else:
            return None
        i += 1
    return simbolos


class _Analisador:
    def __init__(self, simbolos):
        self.simbolos = simbolos
        self.posicao = 0

    def atual(self):
        return self.simbolos[self.posicao] if self.posicao < len(self.simbolos) else None

    def consumir(self, tipo):
        simbolo = self.atual()
        if simbolo is None or simbolo[0] != tipo:
            raise ValueError(f"esperado {tipo}")
        self.posicao += 1

    def primario(self):
        simbolo = self.atual()
        if simbolo is None:
            raise ValueError("expressão incompleta")
        tipo, valor = simbolo
        if tipo == "numero":
            self.posicao += 1
            return [valor]
        if tipo == "s":
            self.posicao += 1
            return [1.0, 0.0]
        if tipo == "(":
            self.posicao += 1
            interno = self.expressao()
            self.consumir(")")
            return interno
        raise ValueError(f"símbolo inesperado {tipo}")

    def potencia(self):
        base = self.primario()
        simbolo = self.atual()
        if simbolo is None or simbolo[0] != "^":
            return base
        self.posicao += 1
        expoente = self.atual()
        if (
            expoente is None
            or expoente[0] != "numero"
            or not float(expoente[1]).is_integer()
            or expoente[1] > MAIOR_EXPOENTE
        ):
            raise ValueError("expoente inválido")
        self.posicao += 1
        resultado = [1.0]
        for _ in range(int(expoente[1])):
            resultado = P.multiplicar(resultado, base)
        return resultado

    def termo(self):
        resultado = self.potencia()
        while True:
            simbolo = self.atual()
            if simbolo is not None and simbolo[0] == "*":
                self.posicao += 1
                resultado = P.multiplicar(resultado, self.potencia())
            elif simbolo is not None and simbolo[0] in ("numero", "s", "("):
                resultado = P.multiplicar(resultado, self.potencia())
            else:
                return resultado

    def expressao(self):
        resultado = [0.0]
        sinal = 1
        simbolo = self.atual()
        if simbolo is not None and simbolo[0] in "+-":
            sinal = -1 if simbolo[0] == "-" else 1
            self.posicao += 1
        resultado = P.somar(resultado, P.escalar(self.termo(), sinal))
        while self.atual() is not None and self.atual()[0] in ("+", "-"):
            sinal = -1 if self.atual()[0] == "-" else 1
            self.posicao += 1
            resultado = P.somar(resultado, P.escalar(self.termo(), sinal))
        return resultado

    def analisar(self):
        resultado = self.expressao()
        if self.posicao != len(self.simbolos):
            raise ValueError("sobrou texto")
        return resultado


def interpretar_polinomio(texto):
    if not isinstance(texto, str) or texto.strip() == "":
        return None
    if not SINAIS_DE_EXPRESSAO.search(texto):
        return interpretar_coeficientes(texto)
    simbolos = _separar_simbolos(texto)
    if not simbolos:
        return None
    try:
        coeficientes = P.normalizar(_Analisador(simbolos).analisar())
    except (ValueError, IndexError):
        return None
    coeficientes = [0.0 if c == 0 else c for c in coeficientes]
    return coeficientes if all(math.isfinite(c) for c in coeficientes) else None


def interpretar_numero(texto, padrao=0.0):
    if not isinstance(texto, str) or texto.strip() == "":
        return padrao
    valor = _numero(texto.strip())
    return padrao if valor is None else valor
