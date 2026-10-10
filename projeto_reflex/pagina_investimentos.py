import reflex as rx
from projeto_reflex.states import FinanceState
from projeto_reflex.navegacao import barra_navegacao

@rx.page(route="/investimentos", on_load=FinanceState.carregar_dados_investimentos)
def pagina_investimentos() -> rx.Component:
    return rx.vstack(
        barra_navegacao(),
        rx.container(
            rx.vstack(
                rx.heading("Orientação de Investimentos", font_size="1.5rem", color="#1e293b", margin_top="15px", margin_bottom="2px"),
                rx.text("Acompanhamento de alocação de ativos e estratégias de investimento.", color="#64748b", font_size="0.9rem", margin_bottom="15px"),
                rx.divider(mb="4"),
                
                # Card de Resumo de Investimentos
                rx.hstack(
                    rx.card(
                        rx.vstack(
                            rx.text("Total Aplicado / Investido", font_size="sm", color="gray.500"),
                            rx.heading(f"R$ {FinanceState.total_aportado:,.2f}", size="6"),
                        ),
                        p="4",
                        bg="white",
                        border_radius="lg",
                        shadow="sm",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                    mb="6",
                ),

                # Tabela de Lançamentos de Investimento
                rx.heading("Histórico de Aportes e Ativos", font_size="1.2rem", color="#1e293b", mb="3"),
                rx.data_table(
                    data=FinanceState.df_aportes,
                    pagination=True,
                    search=True,
                    sort=True,
                    width="100%",
                ),
                
                spacing="4",
                align_items="start",
                width="100%",
            ),
            width="100%",
            max_width="1200px",
            padding_x="0em",
            padding_top="0em",
            center_content=True,
        ),
        width="100%",
        spacing="0",
        align="center",
        bg="gray.50",
        min_h="100vh",
    )