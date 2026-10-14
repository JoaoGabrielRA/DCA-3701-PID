"""Monta o Documento com o enunciado e todos os passos de um projeto."""

from ..formatacao.controlador import controlador_latex
from ..formatacao.latex import razao_latex
from ..formatacao.numero import numero_latex
from ..projeto.controladores import obter_controlador
from ..projeto.discretizacao import ALVOS, METODOS
from ..projeto.projeto import projetar_controlador
from .documento import Documento
from .formulario import interpretar_formulario
from .passos import PASSOS, grafico_completo
from .passos_atraso import PASSOS_DO_ATRASO

N = numero_latex


def especificacao_latex(e):
    if e["modo"] == "polos":
        return f"s_d = {N(e['real'])} \\pm {N(e['imaginario'])}\\,j"
    partes = []
    if "sobressinal" in e:
        partes.append(f"M_P \\le {N(e['sobressinal'])}\\%")
    if "zeta" in e:
        partes.append(f"\\zeta = {N(e['zeta'])}")
    if "omegaN" in e:
        partes.append(f"\\omega_n = {N(e['omegaN'])}\\,\\text{{rad/s}}")
    if "acomodacao" in e:
        partes.append(f"t_s({e['criterio']}\\%) < {N(e['acomodacao'])}\\,\\text{{s}}")
    if "tempoDePico" in e:
        partes.append(f"t_p = {N(e['tempoDePico'])}\\,\\text{{s}}")
    return ", \\qquad ".join(partes)


def titulo_do_arquivo(projeto, questao=None):
    if questao:
        return f"{questao['exercicio']} - {questao['nome']}"
    nomes = {"polo": "a-(s+b)", "compensador-zero": "compensador", "compensador-polo": "compensador"}
    controlador = projeto.get("controlador") or obter_controlador(projeto["entrada"]["controlador"])
    return f"Projeto {nomes.get(controlador['id'], controlador['nome'])}"


def _cabecalho(doc, projeto, questao):
    entrada = projeto["entrada"]
    controlador = projeto.get("controlador") or obter_controlador(entrada["controlador"], entrada.get("fixo"))
    bloco = doc.enunciado(f"{questao['exercicio']} · {questao['nome']}" if questao else "Dados do projeto")
    for texto in (questao or {}).get("enunciado", []):
        bloco.paragrafo(texto)
    bloco.formula(
        f"G(s) = {razao_latex(entrada['nG'], entrada['dG'])}, \\qquad H(s) = {razao_latex(entrada['nH'], entrada['dH'])}"
    )
    bloco.formula(controlador_latex(controlador))
    if entrada.get("especificacao"):
        bloco.formula(especificacao_latex(entrada["especificacao"]))
    if entrada.get("atraso"):
        a = entrada["atraso"]
        partes = [f"K^{{\\text{{comp}}}} = {N(a['constante'])}", f"z_{{\\text{{atraso}}}} = {N(a['zero'])}"]
        if a.get("zeta"):
            partes.append(f"\\zeta = {N(a['zeta'])}")
        bloco.formula(", \\qquad ".join(partes))
    if entrada.get("discretizacao"):
        dsc = entrada["discretizacao"]
        bloco.formula(
            f"\\text{{Discretizar }} {ALVOS[dsc['alvo']]} \\text{{ por {METODOS[dsc['metodo']]['nome']}}}, "
            f"\\quad T = {N(dsc['periodo'])}\\,\\text{{s}}"
        )


def montar_documento(projeto, questao=None, aberto=False):
    doc = Documento()
    _cabecalho(doc, projeto, questao)

    if projeto.get("tipo") == "atraso":
        for passo in PASSOS_DO_ATRASO:
            passo["renderizar"](doc.secao(passo["titulo"], aberto or not passo.get("fechado")), projeto)
        return doc

    for passo in PASSOS:
        if passo.get("requer_viabilidade") and not projeto["viavel"]:
            break
        if passo.get("aplicavel") and not passo["aplicavel"](projeto):
            continue
        titulo = passo["titulo_para"](projeto) if passo.get("titulo_para") else passo["titulo"]
        passo["renderizar"](doc.secao(titulo, aberto or not passo.get("fechado")), projeto)
    if projeto["viavel"]:
        grafico_completo(doc, projeto, aberto)
    return doc


def documento_da_questao(exercicio, questao):
    """Resolve uma questão da lista inteira; usado no relatório da lista."""
    descricao = {**questao, "exercicio": exercicio["nome"]}
    leitura = interpretar_formulario(questao)
    try:
        if "erro" in leitura:
            raise ValueError(leitura["erro"])
        return montar_documento(projetar_controlador(leitura["entrada"]), descricao, aberto=True)
    except (ValueError, ZeroDivisionError, ArithmeticError) as falha:
        doc = Documento()
        doc.enunciado(f"{exercicio['nome']} · {questao['nome']}")
        doc.aviso("erro", f"Não foi possível concluir o projeto: {falha}")
        return doc
