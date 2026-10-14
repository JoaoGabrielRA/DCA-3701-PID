"""Documento em blocos: os passos escrevem aqui e cada renderizador (Streamlit ou HTML) desenha do seu jeito.

Textos seguem a convenção da versão web: ``**negrito**`` e ``$latex$`` em linha.
"""


class Documento:
    def __init__(self):
        self.itens = []

    def paragrafo(self, texto):
        self.itens.append(("paragrafo", texto))

    def formula(self, latex):
        self.itens.append(("formula", latex))

    def aviso(self, tipo, texto):
        self.itens.append(("aviso", tipo, texto))

    def separador(self):
        self.itens.append(("separador",))

    def figura(self, fig):
        self.itens.append(("figura", fig))

    def colunas(self, quantidade):
        celulas = [Documento() for _ in range(quantidade)]
        self.itens.append(("colunas", celulas))
        return celulas

    def secao(self, titulo, aberta=False):
        corpo = Documento()
        self.itens.append(("secao", titulo, aberta, corpo))
        return corpo

    def enunciado(self, etiqueta):
        corpo = Documento()
        self.itens.append(("enunciado", etiqueta, corpo))
        return corpo

    def anexar(self, outro):
        self.itens.extend(outro.itens)
