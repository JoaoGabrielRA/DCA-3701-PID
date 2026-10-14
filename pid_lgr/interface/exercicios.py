"""Questões do 1º e do 2º exercício; cada uma preenche o formulário com um clique."""

EXERCICIOS = [
    {
        "nome": "1º exercício",
        "questoes": [
            {
                "nome": "Questão 1",
                "enunciado": [
                    "Dado o sistema $G(s) = \\dfrac{4(s + 4)}{s(s + 2)^2}$ e $H(s) = 1$, projetar um controlador PD para "
                    "que em MF o sistema apresente $M_P(\\%) \\le 10\\%$ e tempo de acomodação ($5\\%$) inferior a "
                    "$4\\,\\text{s}$.",
                ],
                "nG": "4 16", "dG": "1 4 4 0", "nH": "1", "dH": "1",
                "controlador": "pd", "modo": "desempenho", "sobressinal": "10", "acomodacao": "4", "criterio": "5",
            },
            {
                "nome": "Questão 2",
                "enunciado": [
                    "Dado o sistema $G(s) = \\dfrac{1}{10000\\,s^2 - 11772}$ e $H(s) = 1$, projetar um controlador PD "
                    "para que em MF o sistema apresente $\\zeta = 0{,}7$ e $\\omega_n = 0{,}5\\,\\text{rad/s}$.",
                ],
                "nG": "1", "dG": "10000 0 -11772", "nH": "1", "dH": "1",
                "controlador": "pd", "modo": "amortecimento", "zeta": "0.7", "omegaN": "0.5",
            },
            {
                "nome": "Questão 3",
                "enunciado": [
                    "Dado o sistema $G(s) = \\dfrac{5(s + 1)(s + 4)}{(s + 2)^2}$ e $H(s) = \\dfrac{0{,}2}{s + 1}$, "
                    "projetar um controlador PI para que a MF apresente um par de polos em $-4 \\pm 4j$.",
                ],
                "nG": "5 25 20", "dG": "1 4 4", "nH": "0.2", "dH": "1 1",
                "controlador": "pi", "modo": "polos", "poloReal": "-4", "poloImaginario": "4",
            },
            {
                "nome": "Questão 4",
                "enunciado": [
                    "Dado o sistema $G(s) = \\dfrac{5}{s^3 + 12s^2 + 22s + 20}$ e $H(s) = 0{,}4$, projetar um "
                    "controlador PID, com $z_1 = z_2$, para que em MF o sistema apresente $M_P(\\%) \\le 20\\%$ e "
                    "tempo de acomodação ($2\\%$) inferior a $5\\,\\text{s}$.",
                ],
                "nG": "5", "dG": "1 12 22 20", "nH": "0.4", "dH": "1",
                "controlador": "pid", "modo": "desempenho", "sobressinal": "20", "acomodacao": "5", "criterio": "2",
            },
        ],
    },
    {
        "nome": "2º exercício",
        "questoes": [
            {
                "nome": "Questão 1",
                "enunciado": [
                    "Dado o sistema $G(s) = \\dfrac{5(s + 3)}{s(s + 4)}$ e $H(s) = \\dfrac{1}{s + 1}$:",
                    "**a.** Projetar um controlador PID, com $z_1 = z_2$, para que em MF o sistema apresente "
                    "$M_P(\\%) \\le 10\\%$ e tempo de acomodação ($5\\%$) inferior a $3\\,\\text{s}$.",
                    "**b.** Encontrar uma aproximação discretizada para o controlador encontrado utilizando um período "
                    "de amostragem de $2{,}0\\,\\text{s}$ e o método de Tustin.",
                ],
                "nG": "5 15", "dG": "1 4 0", "nH": "1", "dH": "1 1",
                "controlador": "pid", "modo": "desempenho", "sobressinal": "10", "acomodacao": "3", "criterio": "5",
                "discretizacao": "tustin", "periodo": "2", "alvo": "controlador",
            },
            {
                "nome": "Questão 2",
                "enunciado": [
                    "Dado o sistema $G(s) = \\dfrac{2(s + 1)}{s^2 + 2s + 2}$ e $H(s) = \\dfrac{s + 3}{s + 5}$, sabendo "
                    "que o controlador $G_c(s) = \\dfrac{a}{s + b}$ será utilizado:",
                    "**a.** Quais devem ser os valores de $a$ e $b$ para que o sistema controlado, em malha fechada, "
                    "apresente um par de polos em $-2{,}5 \\pm 2{,}0j$?",
                    "**b.** Discretizar o sistema encontrado $\\{G(s)H(s)G_c(s)\\}$ utilizando um período de "
                    "amostragem de $1\\,\\text{s}$ e o método de Euler.",
                ],
                "nG": "2 2", "dG": "1 2 2", "nH": "1 3", "dH": "1 5",
                "controlador": "polo", "modo": "polos", "poloReal": "-2.5", "poloImaginario": "2",
                "discretizacao": "euler", "periodo": "1", "alvo": "malha",
            },
        ],
    },
]
