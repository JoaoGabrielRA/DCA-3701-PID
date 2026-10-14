"""PD, PI e PID pelo lugar das raízes — app Streamlit.

Projeto de controladores pelo LGR com a conta inteira, passo a passo.
Autor: João Gabriel R. de Azevedo · DCA-3701 · UFRN
"""

import json
from pathlib import Path

import streamlit as st

from pid_lgr.autoria import AUTOR, DISCIPLINA, INICIAIS
from pid_lgr.formatacao.controlador import controlador_latex
from pid_lgr.formatacao.latex import razao_latex
from pid_lgr.interface import graficos as G
from pid_lgr.interface.avulsas import NOMES as NOMES_DAS_FERRAMENTAS, METODOS_AVULSOS, calcular_ferramenta
from pid_lgr.interface.exercicios import EXERCICIOS
from pid_lgr.interface.formulario import (
    ALVOS_DA_DISCRETIZACAO,
    CAMPOS,
    CAMPOS_POR_MODO,
    CONTROLADORES,
    DISCRETIZACOES,
    MODOS,
    VALORES_INICIAIS,
    VALORES_PADRAO,
    campos_do_endereco,
    interpretar_especificacao_de,
    interpretar_fixo,
    interpretar_formulario,
    ler_coeficientes,
    rotulo_do_fixo,
    so_atraso,
    tipo_do_fixo,
    usa_atraso,
)
from pid_lgr.interface.passos import PASSOS
from pid_lgr.interface.render_html import gerar_html
from pid_lgr.interface.render_streamlit import renderizar
from pid_lgr.interface.resultado import documento_da_questao, montar_documento, titulo_do_arquivo
from pid_lgr.projeto.controladores import obter_controlador
from pid_lgr.projeto.malha import pontos_notaveis
from pid_lgr.projeto.projeto import esbocar_projeto, projetar_controlador

ASSETS = Path(__file__).parent / "assets"
OPCOES = {
    "controlador": CONTROLADORES,
    "modo": MODOS,
    "criterio": {"2": "2%", "5": "5%"},
    "discretizacao": DISCRETIZACOES,
    "alvo": ALVOS_DA_DISCRETIZACAO,
}

st.set_page_config(page_title="PD, PI e PID pelo LGR", page_icon="📈", layout="wide")

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.6rem; max-width: 1180px; }
      .etiqueta { color: #1f4fa3; font-weight: 600; letter-spacing: .04em; font-size: .82rem;
                  text-transform: uppercase; margin-bottom: .2rem; }
      .assinatura { display: flex; align-items: center; gap: .7rem; margin-top: .6rem; }
      .assinatura-inicial { width: 2.4rem; height: 2.4rem; border-radius: 50%; background: #2b6cd9; color: #fff;
                            display: flex; align-items: center; justify-content: center; font-weight: 700; }
      .assinatura-nome { font-weight: 600; line-height: 1.1; }
      .assinatura-papel { color: #6b7885; font-size: .85rem; }
      .rodape { color: #6b7885; font-size: .85rem; text-align: center; margin-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# Estado ----------------------------------------------------------------------

def _valor_valido(nome, valor):
    opcoes = OPCOES.get(nome)
    return valor if opcoes is None or valor in opcoes else VALORES_INICIAIS[nome]


def iniciar_estado():
    if "iniciado" in st.session_state:
        # Mantém o valor de campos que ficaram ocultos nesta execução.
        for nome in CAMPOS:
            st.session_state[nome] = st.session_state[nome]
        return
    parametros = st.query_params
    veio_do_endereco = any(nome in parametros for nome in CAMPOS)
    for nome in CAMPOS:
        st.session_state[nome] = _valor_valido(nome, parametros.get(nome, VALORES_INICIAIS[nome]))
    primeiro = EXERCICIOS[0]
    st.session_state.questao = None if veio_do_endereco else {
        **primeiro["questoes"][0], "exercicio": primeiro["nome"],
    }
    st.session_state.resultado = (
        {"valores": valores_atuais(), "questao": None} if veio_do_endereco else None
    )
    st.session_state.iniciado = True


def valores_atuais():
    return {nome: st.session_state[nome] for nome in CAMPOS}


def limpar_questao():
    st.session_state.questao = None


def aplicar_questao(exercicio, questao):
    for nome, valor in {**VALORES_PADRAO, **questao}.items():
        if nome in CAMPOS:
            st.session_state[nome] = valor
    st.session_state.questao = {**questao, "exercicio": exercicio["nome"]}


def projetar():
    valores = valores_atuais()
    st.session_state.resultado = {"valores": valores, "questao": st.session_state.questao}
    st.query_params.from_dict(campos_do_endereco(valores))


@st.cache_data(show_spinner=False, max_entries=64)
def projeto_em_cache(entrada_json):
    return projetar_controlador(json.loads(entrada_json))


# Componentes do formulário ---------------------------------------------------

def texto(nome, rotulo, **extra):
    st.text_input(rotulo, key=nome, on_change=limpar_questao, **extra)


def escolha(nome, rotulo):
    opcoes = OPCOES[nome]
    st.selectbox(rotulo, list(opcoes), format_func=opcoes.get, key=nome, on_change=limpar_questao)


def previa(nome, numerador, denominador):
    num, den = ler_coeficientes({"nG": numerador, "dG": denominador, "nH": "1", "dH": "1"})[:2]
    if num is None or den is None:
        st.caption(":red[Expressão inválida]")
    else:
        st.latex(f"{nome} = {razao_latex(num, den)}")


def miniatura():
    valores = valores_atuais()
    coeficientes = ler_coeficientes(valores)
    if any(item is None for item in coeficientes):
        st.caption("Aguardando coeficientes válidos")
        return
    try:
        leitura = interpretar_especificacao_de(valores)
        esboco = esbocar_projeto(
            *coeficientes, leitura.get("especificacao"), valores["controlador"], interpretar_fixo(valores).get("fixo")
        )
        plano = G.Plano(pontos_notaveis(esboco), "", compacto=True)
        if esboco["desempenho"]:
            G.desenhar_retas_de_amortecimento(plano, esboco["desempenho"]["zeta"])
        G.desenhar_polos_zeros(plano, esboco["malhaAberta"]["polos"], esboco["malhaAberta"]["zeros"])
        if esboco["zero"]:
            G.desenhar_controlador(plano, esboco["controlador"], esboco["zero"], rotular=False)
        else:
            G.desenhar_fixos_do_controlador(plano, esboco["controlador"])
        if esboco["desempenho"]:
            G.desenhar_polos_desejados(plano, esboco["desempenho"]["polo"], rotular=False)
        st.pyplot(plano.figura(), width="stretch")
    except (ValueError, ZeroDivisionError, ArithmeticError, IndexError):
        st.caption("Prévia indisponível")


# Cabeçalho -------------------------------------------------------------------

def cabecalho():
    marcas = st.columns([1, 1, 8], vertical_alignment="center")
    marcas[0].image(str(ASSETS / "ufrn.png"), width=90)
    marcas[1].image(str(ASSETS / "dca.gif"), width=70)
    marcas[2].markdown(
        "**Departamento de Engenharia de Computação e Automação**  \n"
        ":gray[Universidade Federal do Rio Grande do Norte]"
    )
    st.divider()

    capa, figura = st.columns([3, 2], gap="large")
    with capa:
        st.markdown('<p class="etiqueta">DCA-3701 · Projeto de Sistemas de Controle · 2ª unidade</p>',
                    unsafe_allow_html=True)
        st.title("Projeto de PD, PI e PID pelo lugar das raízes")
        st.markdown(
            "Informe $G(s)$, $H(s)$, o controlador e a especificação. A página leva os polos desejados ao LGR "
            "pelos critérios de ângulo e de módulo, devolve $K_p$, $K_i$ e $K_d$ e confere o resultado na "
            "resposta ao degrau."
        )
        st.markdown(
            f'<div class="assinatura"><span class="assinatura-inicial">{INICIAIS}</span>'
            f'<span><div class="assinatura-nome">{AUTOR}</div><div class="assinatura-papel">Autor</div></span></div>',
            unsafe_allow_html=True,
        )
    with figura:
        st.caption("Prévia do plano s")
        miniatura()


# Questões da lista -------------------------------------------------------------

def questoes_da_lista():
    st.markdown("**Questões da lista**")
    atual = st.session_state.questao
    for exercicio in EXERCICIOS:
        colunas = st.columns([1.3] + [1] * len(exercicio["questoes"]) + [1.4], vertical_alignment="center")
        colunas[0].caption(exercicio["nome"])
        for coluna, questao in zip(colunas[1:], exercicio["questoes"]):
            ativa = bool(atual) and atual["exercicio"] == exercicio["nome"] and atual["nome"] == questao["nome"]
            coluna.button(
                questao["nome"], key=f"q-{exercicio['nome']}-{questao['nome']}",
                type="primary" if ativa else "secondary", width="stretch",
                on_click=aplicar_questao, args=(exercicio, questao),
            )

        def relatorio_da_lista(exercicio=exercicio):
            documentos = [documento_da_questao(exercicio, questao) for questao in exercicio["questoes"]]
            return gerar_html(f"{exercicio['nome']} - PD, PI e PID pelo LGR", documentos)

        colunas[-1].download_button(
            "PDF da lista", data=relatorio_da_lista, file_name=f"{exercicio['nome']} - PD PI PID pelo LGR.html",
            mime="text/html", key=f"pdf-{exercicio['nome']}", icon=":material/picture_as_pdf:", width="stretch",
            on_click="ignore",
            help=f"Resolve todas as questões do {exercicio['nome']} num relatório; abra o arquivo e use "
                 "Imprimir → Salvar como PDF.",
        )


# Formulário ------------------------------------------------------------------

def formulario():
    planta, realimentacao = st.columns(2, gap="medium")
    with planta, st.container(border=True):
        st.markdown("##### Planta $G(s)$")
        a, b = st.columns(2)
        with a:
            texto("nG", "Numerador")
        with b:
            texto("dG", "Denominador")
        previa("G(s)", st.session_state.nG, st.session_state.dG)
    with realimentacao, st.container(border=True):
        st.markdown("##### Realimentação $H(s)$")
        a, b = st.columns(2)
        with a:
            texto("nH", "Numerador")
        with b:
            texto("dH", "Denominador")
        previa("H(s)", st.session_state.nH, st.session_state.dH)

    st.caption(
        "Digite a expressão, como `5(s+3)`, `s(s+4)` ou `(s+2)^2`, ou os coeficientes em ordem decrescente de s: "
        "`1 4 4 0` vale s³ + 4s² + 4s."
    )

    id_controlador = st.session_state.controlador
    somente_atraso = so_atraso(id_controlador)
    controle, especificacao = st.columns(2, gap="medium")

    with controle, st.container(border=True):
        st.markdown("##### Controlador")
        escolha("controlador", "Tipo")
        id_controlador = st.session_state.controlador
        somente_atraso = so_atraso(id_controlador)
        if tipo_do_fixo(id_controlador):
            texto("fixo", rotulo_do_fixo(id_controlador))
        if usa_atraso(id_controlador):
            a, b = st.columns(2)
            with a:
                texto("constante", "Constante desejada (Kp, Kv ou Ka)")
            with b:
                texto("zeroAtraso", "Zero do atraso z (perto da origem)")
        if somente_atraso:
            texto("zetaAtraso", "ζ dos polos dominantes (em branco: mantém o ganho de G)")
        try:
            fixo = interpretar_fixo(valores_atuais()).get("fixo")
            st.latex(controlador_latex(obter_controlador(id_controlador, fixo)))
        except ValueError:
            pass
        if not somente_atraso:
            escolha("discretizacao", "Discretização")
            if st.session_state.discretizacao != "nenhuma":
                a, b = st.columns(2)
                with a:
                    texto("periodo", "Período T (s)")
                with b:
                    escolha("alvo", "Discretizar")

    if not somente_atraso:
        with especificacao, st.container(border=True):
            st.markdown("##### Especificação de malha fechada")
            escolha("modo", "Informar por")
            visiveis = CAMPOS_POR_MODO[st.session_state.modo]
            rotulos = {
                "sobressinal": "Mp máximo (%)", "zeta": "ζ", "omegaN": "ωn (rad/s)", "acomodacao": "ts máximo (s)",
                "criterio": "Critério", "tempoPico": "tp (s)", "poloReal": "Parte real",
                "poloImaginario": "Parte imaginária (±)",
            }
            for coluna, nome in zip(st.columns(len(visiveis)), visiveis):
                with coluna:
                    if nome == "criterio":
                        escolha("criterio", rotulos[nome])
                    else:
                        texto(nome, rotulos[nome])

    st.button("Projetar controlador", type="primary", on_click=projetar, icon=":material/calculate:")


# Resultado -------------------------------------------------------------------

def roteiro():
    with st.container(border=True):
        st.markdown("##### O que você vai ver")
        for indice, passo in enumerate(PASSOS, start=1):
            nome = passo["titulo"].replace("**", "")
            st.markdown(f"{indice}. {nome.split(': ', 1)[-1]}")


def resultado():
    pedido = st.session_state.resultado
    if pedido is None:
        roteiro()
        return
    leitura = interpretar_formulario(pedido["valores"])
    if "erro" in leitura:
        st.error(leitura["erro"])
        return
    try:
        with st.spinner("Calculando"):
            projeto = projeto_em_cache(json.dumps(leitura["entrada"]))
    except (ValueError, ZeroDivisionError, ArithmeticError, IndexError) as falha:
        st.error(f"Não foi possível concluir o projeto: {falha}")
        return

    questao = pedido["questao"]
    titulo = titulo_do_arquivo(projeto, questao)
    barra = st.columns([2, 2, 4], vertical_alignment="center")
    expandir = barra[0].toggle("Expandir todos os passos", key="expandir")
    barra[1].download_button(
        "Baixar PDF", data=lambda: gerar_html(titulo, [montar_documento(projeto, questao, aberto=True)]),
        file_name=f"{titulo}.html", mime="text/html", icon=":material/picture_as_pdf:", on_click="ignore",
        help="Baixa o relatório com todos os passos; abra o arquivo e use Imprimir → Salvar como PDF.",
    )
    barra[2].caption("Link que reabre o projeto: copie o endereço da barra do navegador.")
    renderizar(montar_documento(projeto, questao), expandir_tudo=expandir)


# Ferramentas avulsas -----------------------------------------------------------

def ferramentas():
    st.caption("Discretizar uma G(s) e Ziegler-Nichols, sem projetar controlador.")
    escolhida = st.selectbox(
        "Ferramenta", ["discretizar", "zn1", "zn2"], key="ferramenta",
        format_func={
            "discretizar": "Discretizar uma função G(s)",
            "zn1": "Ziegler-Nichols, 1º método (L e T da curva em S)",
            "zn2": "Ziegler-Nichols, 2º método (Kcr e Pcr)",
        }.get,
    )
    valores = {}
    if escolhida == "discretizar":
        a, b = st.columns(2)
        valores["numerador"] = a.text_input("Numerador de G(s)", "1", key="f-num")
        valores["denominador"] = b.text_input("Denominador de G(s)", "s+2", key="f-den")
        a, b = st.columns(2)
        valores["metodo"] = a.selectbox("Método", list(METODOS_AVULSOS), index=2, format_func=METODOS_AVULSOS.get,
                                        key="f-metodo")
        valores["periodo"] = b.text_input("Período T (s)", "0.1", key="f-periodo")
    elif escolhida == "zn1":
        a, b = st.columns(2)
        valores["L"] = a.text_input("Atraso L (s)", "0.2", key="f-l")
        valores["T"] = b.text_input("Constante de tempo T (s)", "2", key="f-t")
    else:
        a, b = st.columns(2)
        valores["kcr"] = a.text_input("Ganho crítico Kcr", "", key="f-kcr")
        valores["pcr"] = b.text_input("Período crítico Pcr (s)", "", key="f-pcr")
        st.caption("Em branco, Kcr e Pcr saem de G(s)H(s) do formulário do projeto.")

    if st.button("Calcular", type="primary", key="calcular-ferramenta"):
        st.session_state.ferramenta_pedida = (escolhida, valores, ler_coeficientes(valores_atuais()))
    pedido = st.session_state.get("ferramenta_pedida")
    if pedido:
        documento = calcular_ferramenta(*pedido)
        st.download_button(
            "Baixar PDF", data=lambda: gerar_html(NOMES_DAS_FERRAMENTAS[pedido[0]], [calcular_ferramenta(*pedido)]),
            file_name=f"{NOMES_DAS_FERRAMENTAS[pedido[0]]}.html", mime="text/html",
            icon=":material/picture_as_pdf:", on_click="ignore", key="pdf-ferramenta",
        )
        renderizar(documento)


# Página ----------------------------------------------------------------------

iniciar_estado()
cabecalho()

aba_projeto, aba_ferramentas = st.tabs(["Projeto do controlador", "Ferramentas avulsas"])
with aba_projeto:
    questoes_da_lista()
    formulario()
    st.divider()
    resultado()
with aba_ferramentas:
    ferramentas()

st.markdown(f'<p class="rodape">{DISCIPLINA}<br>{AUTOR}</p>', unsafe_allow_html=True)
