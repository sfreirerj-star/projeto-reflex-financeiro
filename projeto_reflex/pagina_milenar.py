import reflex as rx
from datetime import datetime
from .navegacao import barra_navegacao

# --- ESTADO (STATE) PARA GERENCIAR LÓGICA E DADOS ---
class MilenarState(rx.State):
    competencia: str = "10/2026"
    entradas: float = 11734.59
    gastos_comuns: float = 5337.45

    @rx.var
    def saldo_remanescente(self) -> float:
        return self.entradas - self.gastos_comuns

    @rx.var
    def tsedaca(self) -> float:
        if self.saldo_remanescente > 0:
            return self.saldo_remanescente * 0.10
        return 0.0

    @rx.var
    def saldo_investivel(self) -> float:
        if self.saldo_remanescente > 0:
            return self.saldo_remanescente - self.tsedaca
        return 0.0

    @rx.var
    def um_terco(self) -> float:
        if self.saldo_investivel > 0:
            return self.saldo_investivel / 3
        return 0.0

    @rx.var
    def tsedaca_fmt(self) -> str:
        return f"R$ {self.tsedaca:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def um_terco_fmt(self) -> str:
        return f"R$ {self.um_terco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def entradas_fmt(self) -> str:
        return f"R$ {self.entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def gastos_fmt(self) -> str:
        return f"R$ {self.gastos_comuns:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def saldo_fmt(self) -> str:
        return f"R$ {self.saldo_remanescente:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# --- COMPONENTE DA PÁGINA ---
def pagina_milenar() -> rx.Component:
    return rx.vstack(
        barra_navegacao(),  # Menu superior azul padronizado
        rx.container(
            rx.vstack(
                # Título e Descrição
                rx.heading("📜 Estratégia de Alocação Milenar (Talmude)", size="7", margin_bottom="2"),
                rx.text(
                    "Aplicação prática dos conceitos de Tsedacá e da Regra dos Três Terços usando seus dados reais.",
                    color="gray",
                    margin_bottom="4"
                ),

                # --- SEÇÃO EDUCATIVA (EXPANDER / ACCORDION) ---
                rx.accordion.root(
                    rx.accordion.item(
                        header=rx.heading("📖 Clique aqui para entender a Origem e a Filosofia da Riqueza Milenar", size="3"),
                        content=rx.vstack(
                            rx.markdown("""
                            ### A Regra dos Três Terços do Talmude
                            Para aprofundar seus conhecimentos, o ponto de partida ideal é a **Regra dos Três Terços do Talmude**, uma das diretrizes financeiras mais antigas e eficazes do mundo sobre gestão e diversificação de patrimônio.
                            Há mais de 1.500 anos, o tratado **Baba Metzia (42a)** determinou a seguinte estratégia de alocação de recursos:
                            > *"Uma pessoa deve sempre dividir seu dinheiro em três partes: um terço em terras, um terço em negócios e um terço mantido em mãos."*

                            ---

                            ### A Estrutura Prática dos Três Terços
                            Traduzindo esse ensinamento milenar para o cenário financeiro e econômico moderno, a divisão funciona da seguinte forma:

                            * **1/3 em Terras (Segurança):** Investimentos de base sólida, real e menos voláteis (FIIs, imóveis, terras).
                            * **1/3 em Negócios (Crescimento):** Investimentos de risco e potencial de multiplicação (Ações, empresas, novos projetos).
                            * **1/3 em Mãos (Liquidez e Oportunidade):** Dinheiro de fácil acesso e reserva imediata (Tesouro Selic, CDB 100% CDI).

                            ---

                            ### O Conceito de Tsedacá (Justiça Social)
                            Ao contrário da palavra "caridade", **Tsedacá** vem da raiz *Tsedek* (**justiça/retidão**).
                            * **Mentalidade de Canal:** O dinheiro circula para apoiar a comunidade.
                            * **A Regra dos 10% a 20%:** Destinar uma parte dos ganhos é uma prática de justiça e equilíbrio social.
                            """),
                            spacing="2",
                            padding="4"
                        )
                    ),
                    width="100%",
                    collapsible=True,
                    variant="outline",
                    margin_bottom="4"
                ),

                rx.divider(margin_y="4"),

                # --- RESUMO DA COMPETÊNCIA (MÉTRICAS) ---
                rx.heading(f"📱 Resumo da Competência: {MilenarState.competencia}", size="4", margin_bottom="3"),
                
                rx.grid(
                    rx.card(
                        rx.vstack(
                            rx.text("Entradas", color="gray", size="2"),
                            rx.text(MilenarState.entradas_fmt, size="5", weight="bold", color="green"),
                        )
                    ),
                    rx.card(
                        rx.vstack(
                            rx.text("Gastos Comuns", color="gray", size="2"),
                            rx.text(MilenarState.gastos_fmt, size="5", weight="bold", color="red"),
                        )
                    ),
                    rx.card(
                        rx.vstack(
                            rx.text("Saldo Livre", color="gray", size="2"),
                            rx.text(MilenarState.saldo_fmt, size="5", weight="bold", color="blue"),
                            rx.badge(
                                rx.cond(MilenarState.saldo_remanescente >= 0, "No Azul 💙", "No Vermelho 🔴"),
                                color_scheme=rx.cond(MilenarState.saldo_remanescente >= 0, "blue", "red")
                            )
                        )
                    ),
                    columns="3",
                    spacing="4",
                    width="100%",
                    margin_bottom="6"
                ),

                # --- DIVISÃO MILENAR (TSEDACÁ + TRÊS TERÇOS) ---
                rx.cond(
                    MilenarState.saldo_remanescente > 0,
                    rx.vstack(
                        # Alerta de Tsedacá
                        rx.callout(
                            rx.vstack(
                                rx.text(f"🕊️ Tsedacá (Justiça Social - 10%): {MilenarState.tsedaca_fmt}", weight="bold", size="4"),
                                rx.text("Destine este valor para fazer o bem, apoiar projetos sociais ou ajudar na capacitação profissional de terceiros.", size="2")
                            ),
                            icon="heart",
                            color_scheme="amber",
                            width="100%",
                            margin_bottom="4"
                        ),

                        rx.heading("🎯 Divisão Estratégica dos Três Terços (Talmude)", size="4", margin_y="3"),

                        # 3 Colunas dos Terços
                        rx.grid(
                            rx.card(
                                rx.vstack(
                                    rx.text("🛡️ 1/3 em Terras", weight="bold", size="3"),
                                    rx.text(MilenarState.um_terco_fmt, size="6", weight="bold", color="blue"),
                                    rx.text("Foco: Segurança e Preservação", weight="bold", size="2"),
                                    rx.text("Sugestão: Fundos Imobiliários de Tijolo, Imóveis ou Renda Fixa IPCA+.", size="2", color="gray")
                                ),
                                border_top="4px solid #3b82f6"
                            ),
                            rx.card(
                                rx.vstack(
                                    rx.text("📈 1/3 em Negócios", weight="bold", size="3"),
                                    rx.text(MilenarState.um_terco_fmt, size="6", weight="bold", color="green"),
                                    rx.text("Foco: Multiplicação e Crescimento", weight="bold", size="2"),
                                    rx.text("Sugestão: Ações, novos projetos geradores de receita ou capacitação pessoal.", size="2", color="gray")
                                ),
                                border_top="4px solid #10b981"
                            ),
                            rx.card(
                                rx.vstack(
                                    rx.text("💰 1/3 em Mãos", weight="bold", size="3"),
                                    rx.text(MilenarState.um_terco_fmt, size="6", weight="bold", color="orange"),
                                    rx.text("Foco: Liquidez e Oportunidade", weight="bold", size="2"),
                                    rx.text("Sugestão: Tesouro Selic ou CDB 100% CDI com liquidez diária.", size="2", color="gray")
                                ),
                                border_top="4px solid #f59e0b"
                            ),
                            columns="3",
                            spacing="4",
                            width="100%",
                            margin_bottom="6"
                        ),

                        width="100%"
                    ),
                    rx.callout(
                        "O saldo remanescente em conta precisa ser positivo para aplicar o modelo milenar de investimentos.",
                        icon="alert_triangle",
                        color_scheme="red",
                        width="100%"
                    )
                ),

                width="100%",
                max_width="1200px",
                align="start",
                spacing="4"
            ),
            padding_x="2em",
            padding_y="2em",
            center_content=True,
            width="100%"
        ),
        width="100%",
        spacing="0",
        align="center"
    )