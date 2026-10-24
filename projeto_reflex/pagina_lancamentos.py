import reflex as rx
from datetime import datetime
from .states import FinanceState

@rx.page(route="/lancamentos", title="Novo Lançamento")
def pagina_lancamentos() -> rx.Component:
    from .navegacao import barra_navegacao
    
    return rx.vstack(
        barra_navegacao(),
        rx.container(
            rx.vstack(
                rx.heading("📝 Novo Lançamento & Registro de Caixa", font_size={"base": "1.3rem", "md": "1.7rem"}, color="#1e293b", margin_top="15px", margin_bottom="2px"),
                rx.text("Registre as suas receitas e despesas do dia a dia com abatimento automático dos aportes de investimentos.", color="#64748b", font_size="0.9rem", margin_bottom="15px"),
                rx.divider(mb="4"),
                
                # Formulário Responsivo Conectado ao FinanceState Central
                rx.vstack(
                    rx.grid(
                        rx.vstack(
                            rx.text("Data (AAAA-MM-DD)", weight="bold", size="2"),
                            rx.input(value=FinanceState.data_lancamento, on_change=FinanceState.set_data_lancamento, width="100%"),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Categoria", weight="bold", size="2"),
                            rx.input(value=FinanceState.categoria, on_change=FinanceState.set_categoria, placeholder="Ex: Alimentação, Transporte...", width="100%"),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Descrição / Estabelecimento", weight="bold", size="2"),
                            rx.input(value=FinanceState.descricao, on_change=FinanceState.set_descricao, placeholder="Ex: Supermercado...", width="100%"),
                            spacing="1",
                        ),
                        columns={"base": "1", "md": "3"},
                        gap="4",
                        width="100%",
                    ),

                    rx.grid(
                        rx.vstack(
                            rx.text("Tipo", weight="bold", size="2"),
                            rx.select(["Despesa", "Receita", "Investimento"], value=FinanceState.tipo, on_change=FinanceState.set_tipo, width="100%"),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Valor (R$)", weight="bold", size="2"),
                            rx.input(value=FinanceState.valor, on_change=FinanceState.set_valor, placeholder="0.00", width="100%"),
                            spacing="1",
                        ),
                        rx.box(
                            rx.button("Salvar Lançamento", on_click=FinanceState.cadastrar_lancamento, color_scheme="blue", width="100%"),
                            width="100%",
                        ),
                        columns={"base": "1", "md": "3"},
                        gap="4",
                        width="100%",
                        align_items="end",
                        mt="4",
                    ),

                    padding={"base": "16px", "md": "24px"},
                    border="1px solid #e2e8f0",
                    border_radius="10px",
                    bg="#ffffff",
                    box_shadow="sm",
                    mb="6",
                    width="100%",
                ),

                rx.divider(mb="4"),

                # Histórico Unificado com a Página Gerenciar
                rx.heading("📋 Histórico de Lançamentos da Competência Atual", font_size="1.2rem", color="#1e293b", mb="3"),
                rx.cond(
                    FinanceState.lista_lancamentos.length() > 0,                   
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("ID"),
                                    rx.table.column_header_cell("Data"),
                                    rx.table.column_header_cell("Tipo"),
                                    rx.table.column_header_cell("Categoria"),
                                    rx.table.column_header_cell("Descrição"),
                                    rx.table.column_header_cell("Valor"),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(
                                    FinanceState.lista_lancamentos,
                                    lambda item: rx.table.row(
                                        rx.table.cell(item["id"]),
                                        rx.table.cell(item["data"]),
                                        rx.table.cell(item["tipo"]),
                                        rx.table.cell(item["categoria"]),
                                        rx.table.cell(item["descricao"]),
                                        rx.table.cell(item["valor"]),
                                    ),
                                )
                            ),
                            variant="surface",
                            size="3",
                            width="100%",
                        ),
                        max_height="260px",
                        overflow_y="auto",
                        overflow_x="auto",
                        width="100%",
                        border="1px solid #e2e8f0",
                        border_radius="8px",
                    ),
                    rx.text("Nenhum lançamento registrado nesta competência.", color="gray"),
                ),

                width="100%",
                align="start",
            ),
            width="100%",
            max_width="1200px",
            padding_x={"base": "1em", "md": "2em"},
            padding_top="0em",
            center_content=True,
        ),
        width="100%",
        spacing="0",
        align="center",
    )