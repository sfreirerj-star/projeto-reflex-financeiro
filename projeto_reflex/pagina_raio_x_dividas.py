import reflex as rx
from .states import FinanceState
from .navegacao import barra_navegacao

@rx.page(route="/raio-x-dividas", title="Raio-X de Dívidas", on_load=FinanceState.carregar_dados)
def pagina_raio_x_dividas() -> rx.Component:
    return rx.vstack(
        barra_navegacao(),  # Menu azul no topo
        rx.container(
            rx.vstack(
                rx.heading("⚠️ Gerenciamento de Dívidas e Parcelamentos (Raio-X)", font_size="1.5rem", color="#1e293b", margin_top="15px", margin_bottom="2px"),
                rx.text("Acompanhe os seus passivos, prazos e controle de pagamentos.", color="#64748b", font_size="0.9rem", margin_bottom="15px"),
                rx.divider(mb="4"),

                # Formulário de Cadastro em Grid Estruturado
                rx.vstack(
                    rx.heading("Cadastrar Novo Parcelamento / Dívida", font_size="1.2rem", color="#1e293b", mb="3"),
                    
                    # Linha 1: Credor / Nome da Dívida
                    rx.vstack(
                        rx.text("Credor / Nome da Dívida (Ex: Carnê Casas Bahia)", weight="bold", size="2"),
                        rx.input(
                            value=FinanceState.novo_credor, 
                            on_change=FinanceState.set_novo_credor, 
                            placeholder="Ex: Cartão de Crédito, Financiamento...", 
                            width="100%"
                        ),
                        spacing="1",
                        width="100%",
                        mb="3",
                    ),

                    # Linha 2: 4 Colunas (Valor Total, Total Parcelas, Valor Parcela, Dia Vencimento)
                    rx.grid(
                        rx.vstack(
                            rx.text("Valor Total (R$)", weight="bold", size="2"),
                            rx.input(value=FinanceState.novo_valor_total, on_change=FinanceState.set_novo_valor_total, placeholder="0.00", width="100%"),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Total de Parcelas", weight="bold", size="2"),
                            rx.input(value=FinanceState.novo_total_parcelas, on_change=FinanceState.set_novo_total_parcelas, placeholder="1", width="100%"),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Valor da Parcela (R$)", weight="bold", size="2"),
                            rx.input(value=FinanceState.novo_valor_parcela, on_change=FinanceState.set_novo_valor_parcela, placeholder="0.00", width="100%"),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Dia de Vencimento", weight="bold", size="2"),
                            rx.input(value=FinanceState.novo_dia_vencimento, on_change=FinanceState.set_novo_dia_vencimento, placeholder="15", width="100%"),
                            spacing="1",
                        ),
                        columns="4",
                        gap="4",
                        width="100%",
                        mb="3",
                    ),

                    # Linha 3: Status e Botão Cadastrar (Alinhamento Perfeito)
                    rx.grid(
                        rx.vstack(
                            rx.text("Status", weight="bold", size="2"),
                            rx.select(["Pendente", "Quitada"], value=FinanceState.novo_status, on_change=FinanceState.set_novo_status, width="100%"),
                            spacing="1",
                        ),
                        rx.box(
                            rx.button("Cadastrar Dívida", on_click=FinanceState.cadastrar_divida, color_scheme="blue", width="100%"),
                            width="100%",
                        ),
                        columns="2",
                        gap="4",
                        width="100%",
                        align_items="end",  # <-- Alinha a base inferior do botão com o campo Select
                    ),

                    padding="24px",
                    border="1px solid #e2e8f0",
                    border_radius="10px",
                    bg="#ffffff",
                    box_shadow="sm",
                    mb="6",
                    width="100%",
                ),

                rx.divider(mb="4"),

                # Seção de Edição / Gerenciamento de Dívida Existente
                rx.heading("✏️ Gerenciar Dívida Existente", font_size="1.2rem", color="#1e293b", mb="3"),
                rx.select(
                    FinanceState.lista_resumo_dividas,
                    placeholder="Selecione uma dívida para editar...",
                    on_change=lambda val: FinanceState.selecionar_divida(val.split(" | ")[0].replace("ID: ", "")),
                    width="100%",
                    mb="4",
                ),

                rx.cond(
                    FinanceState.id_selecionado > 0,
                    rx.vstack(
                        rx.grid(
                            rx.vstack(
                                rx.text("Credor", weight="bold", size="2"),
                                rx.input(value=FinanceState.edit_credor, on_change=FinanceState.set_edit_credor, width="100%"),
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("Valor Total (R$)", weight="bold", size="2"),
                                rx.input(value=FinanceState.edit_valor_total, on_change=FinanceState.set_edit_valor_total, width="100%"),
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("Total Parcelas", weight="bold", size="2"),
                                rx.input(value=FinanceState.edit_total_parcelas, on_change=FinanceState.set_edit_total_parcelas, width="100%"),
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("Valor Parcela (R$)", weight="bold", size="2"),
                                rx.input(value=FinanceState.edit_valor_parcela, on_change=FinanceState.set_edit_valor_parcela, width="100%"),
                                spacing="1",
                            ),
                            columns="4",
                            gap="4",
                            width="100%",
                            mb="3",
                        ),
                        rx.grid(
                            rx.vstack(
                                rx.text("Dia Vencimento", weight="bold", size="2"),
                                rx.input(value=FinanceState.edit_dia_vencimento, on_change=FinanceState.set_edit_dia_vencimento, width="100%"),
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("Status", weight="bold", size="2"),
                                rx.select(["Pendente", "Quitada"], value=FinanceState.edit_status, on_change=FinanceState.set_edit_status, width="100%"),
                                spacing="1",
                            ),
                            rx.hstack(
                                rx.button("Salvar Alterações", on_click=FinanceState.salvar_edicao, color_scheme="green", width="50%"),
                                rx.button("Excluir Dívida", on_click=FinanceState.excluir_divida, color_scheme="red", width="50%"),
                                width="100%",
                            ),
                            columns="3",
                            gap="4",
                            width="100%",
                            align_items="end",
                        ),
                        spacing="3",
                        padding="24px",
                        border="1px solid #e2e8f0",
                        border_radius="10px",
                        bg="#fafafa",
                        width="100%",
                        mb="6",
                    ),
                    rx.text("Selecione uma dívida acima para carregar os dados de alteração.", color="gray", mb="6"),
                ),
                width="100%",
                align="start",
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
    )