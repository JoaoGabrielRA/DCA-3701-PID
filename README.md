<div align="center" markdown="1">

# PD, PI e PID pelo lugar das raízes

**Projeto de controladores pelo LGR com a conta inteira, passo a passo — em Python e Streamlit.**

![Licença de código: MIT](https://img.shields.io/badge/c%C3%B3digo-MIT-blue) ![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab) ![Streamlit](https://img.shields.io/badge/Streamlit-app-ff4b4b)

**João Gabriel R. de Azevedo**<br>
DCA-3701 Projeto de Sistemas de Controle · 2ª unidade · DCA · UFRN

</div>

---

Informe $G(s)$, $H(s)$, o tipo de controlador e a especificação de malha fechada. O app encontra os
polos dominantes desejados, aplica o critério de ângulo para posicionar o zero (ou o polo) do
controlador e o critério de módulo para achar o ganho, devolve os parâmetros do controlador, confere o
projeto na resposta ao degrau simulada e, se pedido, discretiza o resultado.

**[Os passos](#os-passos)** · **[Rodar local](#rodar-local)** · **[Publicar no Streamlit](#publicar-no-streamlit-community-cloud)** · **[Estrutura](#estrutura)** · **[Testes](#testes)**

## Destaques

|||
|---|---|
| **PD, PI e PID** | o PID usa zeros reais e iguais, $G_c(s) = K_c (s+z)^2 / s$ |
| **Controlador $a/(s+b)$** | polo e ganho livres: o ângulo dá $b$ e o módulo dá $a$ |
| **Compensador $K(s+z)/(s+p)$** | com o zero ou o polo dado, o ângulo acha o outro e o módulo dá $K$ (avanço de fase) |
| **Atraso e atraso-avanço** | atraso pelo erro, com $\beta = K^{\text{comp}}/K$; atraso-avanço com a parte em avanço pelos critérios e a em atraso pelo $\beta$ |
| **Discretização** | Euler (Forward), Backward, Tustin ou invariância ao degrau (SOZ), do controlador, de $G_c G H$ ou de $G(s)$ |
| **Ferramentas avulsas** | discretizar qualquer $G(s)$ e Ziegler-Nichols, 1º e 2º métodos, com $K_{cr}$ e $P_{cr}$ tirados do modelo se preciso |
| **Seis formas de especificar** | $M_P$ e $t_s$, $M_P$ e $t_p$, $\zeta$ e $t_s$, $t_s$ e $t_p$, $\zeta$ e $\omega_n$, ou os próprios polos desejados |
| **Entrada fatorada** | $G(s)$ e $H(s)$ aceitam `5(s+3)`, `s(s+4)`, `(s+2)^2` ou a lista de coeficientes |
| **A conta, não só o resultado** | fórmula, substituição e resultado de cada passo, em LaTeX |
| **Projeto conferido** | polos de malha fechada, dominância e resposta ao degrau exata em espaço de estados |
| **Questões da lista** | cada questão do 1º e do 2º exercício preenche o formulário com um clique |
| **PDF** | **Baixar PDF** gera o relatório do projeto aberto; **PDF da lista** resolve a lista inteira |
| **Link que reabre o projeto** | os campos vão para a barra de endereços |

## Os passos

| | Passo | O que aparece |
|---|---|---|
| 1 | Especificações | $\zeta$ a partir de $M_P$, $\zeta\omega_n$ a partir de $t_s$, e $\omega_d$ |
| 2 | Polos desejados | $s_d = -\sigma \pm j\omega_d$ sobre a reta de amortecimento |
| 3 | Malha aberta | $G(s)H(s)$, polos, zeros, cancelamentos e a forma de $G_c(s)$ |
| 4 | Critério de ângulo | contribuição de cada polo e zero em $s_d$ e a deficiência angular $\phi_c$ |
| 5 | Zero ou polo do controlador | $z = \sigma + \omega_d / \tan\phi_z$ (ou $b$, para $a/(s+b)$) |
| 6 | Critério de módulo | ganho total $K_t$ e o ganho do controlador $K_c = K_t/k$ |
| 6b | Parte em atraso | constante de erro atual, $\beta$, zero e polo do atraso (só no atraso-avanço) |
| 7 | Ganhos | $K_p$, $K_i$ e $K_d$ e o controlador nas formas fatorada e paralela |
| 8 | Malha fechada | $T(s)$, polos de malha fechada e a verificação de dominância |
| 9 | Resposta ao degrau | $M_P$, $t_p$ e $t_s$ simulados contra a referência de segunda ordem |
| 10 | Discretização | substituição de $s$, $G(z)$ em $z$ e $z^{-1}$, equação de diferenças e polos discretos (só quando pedida) |

O passo 8 também traz as constantes de erro estático $K_p$, $K_v$ e $K_a$. O atraso de fase puro segue
o roteiro da apostila (seção 4.6) em cinco passos próprios: ganho de malha aberta, $\beta$, controlador,
polos com e sem o atraso e resposta ao degrau comparada.

Depois dos passos vem o LGR do sistema compensado, com os polos de malha fechada no ganho projetado.
Quando o critério de ângulo não tem solução para o controlador escolhido, o roteiro para no passo 4 e
explica o motivo.

## Rodar local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Depois abra <http://localhost:8501>.

**Como usar:** digite $G(s)$ e $H(s)$ como expressão, por exemplo `5(s+3)` e `s(s+4)`, ou como
coeficientes em ordem decrescente de $s$, separados por espaço — `1 4 4 0` é $s^3 + 4s^2 + 4s$. A
prévia abaixo de cada campo mostra o polinômio expandido. Escolha o controlador, a forma da
especificação e clique em **Projetar controlador**.

**PDF:** **Baixar PDF**, acima do resultado, e **PDF da lista**, ao lado das questões, baixam um
relatório HTML com todos os passos abertos e os gráficos em vetor. Abra o arquivo no navegador e use
**Imprimir → Salvar como PDF** (há um botão para isso no topo do relatório).

## Publicar no Streamlit Community Cloud

1. Suba esta pasta para um repositório no GitHub (com `app.py` e `requirements.txt` na raiz).
2. Em <https://share.streamlit.io>, clique em **Create app** → **Deploy a public app from GitHub**.
3. Escolha o repositório, o branch `main` e o arquivo principal `app.py`. Em **Advanced settings**,
   selecione Python 3.11 ou mais novo.
4. Clique em **Deploy**. O tema claro vem de `.streamlit/config.toml`.

## Estrutura

```
app.py                  página Streamlit: formulário, questões, resultado e ferramentas
assets/                 marcas da UFRN e do DCA
pid_lgr/
├── autoria.py          nome do autor e da disciplina (um lugar só)
├── nucleo/             polinômios, leitura de expressões, raízes e exponencial de matriz
├── projeto/            especificações, controladores, critérios, malhas, degrau, LGR,
│                       discretização, atraso e Ziegler-Nichols
├── formatacao/         números, controladores e conversão para LaTeX
└── interface/          documento em blocos, os passos, gráficos (matplotlib),
                        renderização no Streamlit e no relatório HTML
testes/                 suíte em pytest
```

A direção de dependência é fixa: `nucleo` não conhece ninguém, `projeto` usa `nucleo`, `formatacao`
só traduz resultados, e `interface` é a única camada que conhece Streamlit e matplotlib. Os passos
escrevem num `Documento` em blocos, que é desenhado tanto na tela quanto no relatório para PDF. Um
controlador novo entra como mais uma entrada em `projeto/controladores.py`, e as questões de outra
lista entram em `interface/exercicios.py`.

## Testes

```bash
pip install pytest
python -m pytest testes
```

A suíte cobre especificações, critérios de ângulo e de módulo, a simulação do degrau, a
discretização, o atraso de fase, Ziegler-Nichols, a leitura de expressões, raízes plantadas de grau 2
a 8 e as questões do 1º e do 2º exercício, com os mesmos valores esperados da versão original.

## Licença

Código sob licença MIT, em [LICENSE](LICENSE). As marcas da UFRN e do DCA em `assets/`
pertencem às respectivas instituições e aparecem apenas para identificar a disciplina.
