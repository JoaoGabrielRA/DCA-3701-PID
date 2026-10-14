"""Desenha um Documento com componentes do Streamlit."""

import matplotlib.pyplot as plt
import streamlit as st

AVISOS = {
    "erro": st.error,
    "atencao": st.warning,
    "sucesso": st.success,
    "informacao": st.info,
}


def renderizar(documento, expandir_tudo=False):
    for item in documento.itens:
        tipo = item[0]
        if tipo == "paragrafo":
            st.markdown(item[1])
        elif tipo == "formula":
            st.latex(item[1])
        elif tipo == "aviso":
            AVISOS[item[1]](item[2])
        elif tipo == "separador":
            st.divider()
        elif tipo == "figura":
            st.pyplot(item[1], width="stretch")
            plt.close(item[1])
        elif tipo == "colunas":
            for coluna, celula in zip(st.columns(len(item[1])), item[1]):
                with coluna:
                    renderizar(celula, expandir_tudo)
        elif tipo == "secao":
            _, titulo, aberta, corpo = item
            with st.expander(titulo, expanded=aberta or expandir_tudo):
                renderizar(corpo, expandir_tudo)
        elif tipo == "enunciado":
            _, etiqueta, corpo = item
            with st.container(border=True):
                st.caption(etiqueta.upper())
                renderizar(corpo, expandir_tudo)
