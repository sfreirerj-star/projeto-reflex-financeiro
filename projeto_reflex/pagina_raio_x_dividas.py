import reflex as rx
import pandas as pd
import database
from datetime import datetime
from .states import FinanceState


class RaioXDividasState(rx.State):
    """Estado específico para gerir cálculos, indicadores e formulários do Raio-X de Dívidas."""

    @rx.var
    def df_dividas(self) -> pd.DataFrame:
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df = pd.read_sql_query(
                "SELECT id, credor, valor_total, total_parcelas, valor_parcela, dia_vencimento, status FROM dividas ORDER BY id DESC",
                conexao,
            )
            conexao.close()
            return df
        except Exception:
            return pd.DataFrame(
                columns=[
                    "id",
                    "credor",
                    "valor_total",
                    "total_parcelas",
                    "valor_parcela",
                    "dia_vencimento",
                    "status",
                ]
            )

    @rx.var
    def total_dividas_pendentes(self) -> str:
        df = self.df_dividas
        if df.empty:
            return "R$ 0,00"
        df_pendentes = df[df["status"] == "Pendente"]
        if df_pendentes.empty:
            return "R$ 0,00"

        soma = pd.to_numeric(df_pendentes["valor_total"], errors="coerce").sum()
        return (
            f"R$ {soma:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    @rx.var
    def prazo_estimado_quitacao(self) -> str:
        df = self.df_dividas
        if df.empty:
            return "Sem dívidas pendentes"

        df_pendentes = df[df["status"] == "Pendente"]
        if df_pendentes.empty:
            return "Sem dívidas pendentes"

        max_parc = pd.to_numeric(
            df_pendentes["total_parcelas"], errors="coerce"
        ).max()
        if pd.isna(max_parc) or max_parc < 1:
            max_parc = 1

        hoje = datetime.now()
        mes_futuro = hoje.month + int(max_parc)
        ano_futuro = hoje.year + (mes_futuro // 12)
        mes_futuro = mes_futuro % 12
        if mes_futuro == 0:
            mes_futuro = 12
            ano_futuro -= 1

        return f"Aprox. {int(max_parc)} meses ({mes_futuro:02d}/{ano_futuro})"

    @rx.var
    def lista_dividas_exibicao(self) -> list[dict]:
        df = self.df_dividas
        if df.empty:
            return []

        resultado = []
        for _, row in df.iterrows():
            v_total = float(row["valor_total"] or 0.0)
            v_parc = float(row["valor_parcela"] or 0.0)
            resultado.append({
                "id": int(row["id"]),
                "credor": str(row["credor"] or ""),
                "valor_total": (
                    f"R$ {v_total:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                ),
                "total_parcelas": int(row["total_parcelas"] or 1),
                "valor_parcela": (
                    f"R$ {v_parc:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                ),
                "dia_vencimento": int(row["dia_vencimento"] or 15),
                "status": str(row["status"] or "Pendente"),
            })
        return resultado


@rx.page(route="/dividas", title="Raio-X de Dívidas")
def pagina_raio_x_dividas() -> rx.Component:
    from .navegacao import barra_navegacao

    return rx.vstack(
        barra_navegacao(),  # Menu azul superior padronizado
        rx.container(
            rx.vstack(
                rx.heading(
                    "⚠️ Gerenciamento de Dívidas e Parcelamentos (Raio-X)",
                    font_size="1.5rem",
                    color="#1e293b",
                    margin_top="15px",
                    margin_bottom="2px",
                ),
                rx.text(
                    "Acompanhe os seus passivos, prazos e controle de pagamentos.",
                    color="#64748b",
                    font_size="0.9rem",
                    margin_bottom="15px",
                ),
                rx.divider(mb="4"),
                # --- INDICADORES GERAIS (CARDS) ---
                rx.heading(
                    "📊 Indicadores Gerais das Dívidas",
                    font_size="1.2rem",
                    color="#1e293b",
                    mb="3",
                ),
                rx.grid(
                    rx.card(
                        rx.vstack(
                            rx.text(
                                "💰 Valor Total das Dívidas Pendentes",
                                color="gray",
                                size="2",
                            ),
                            rx.text(
                                RaioXDividasState.total_dividas_pendentes,
                                size="6",
                                weight="bold",
                                color="red",
                            ),
                        ),
                        width="100%",
                    ),
                    rx.card(
                        rx.vstack(
                            rx.text(
                                "⏳ Prazo Estimado para Quitação Total",
                                color="gray",
                                size="2",
                            ),
                            rx.text(
                                RaioXDividasState.prazo_estimado_quitacao,
                                size="6",
                                weight="bold",
                                color="blue",
                            ),
                        ),
                        width="100%",
                    ),
                    columns="2",
                    spacing="4",
                    width="100%",
                    mb="6",
                ),
                # --- FORMULÁRIO DE CADASTRO DE NOVA DÍVIDA ---
                rx.vstack(
                    rx.heading(
                        "Cadastrar Novo Parcelamento / Dívida",
                        font_size="1.2rem",
                        color="#1e293b",
                        mb="3",
                    ),
                    rx.vstack(
                        rx.text(
                            "Credor / Nome da Dívida (Ex: Carnê Casas Bahia)",
                            weight="bold",
                            size="2",
                        ),
                        rx.input(
                            value=FinanceState.novo_credor,
                            on_change=FinanceState.set_novo_credor,
                            placeholder="Ex: Cartão de Crédito, Financiamento...",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                        mb="3",
                    ),
                    rx.grid(
                        rx.vstack(
                            rx.text("Valor Total (R$)", weight="bold", size="2"),
                            rx.input(
                                value=FinanceState.novo_valor_total,
                                on_change=FinanceState.set_novo_valor_total,
                                placeholder="0.00",
                                width="100%",
                            ),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text(
                                "Total de Parcelas", weight="bold", size="2"
                            ),
                            rx.input(
                                value=FinanceState.novo_total_parcelas,
                                on_change=FinanceState.set_novo_total_parcelas,
                                placeholder="1",
                                width="100%",
                            ),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text(
                                "Valor da Parcela (R$)", weight="bold", size="2"
                            ),
                            rx.input(
                                value=FinanceState.novo_valor_parcela,
                                on_change=FinanceState.set_novo_valor_parcela,
                                placeholder="0.00",
                                width="100%",
                            ),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text(
                                "Dia de Vencimento", weight="bold", size="2"
                            ),
                            rx.input(
                                value=FinanceState.novo_dia_vencimento,
                                on_change=FinanceState.set_novo_dia_vencimento,
                                placeholder="15",
                                width="100%",
                            ),
                            spacing="1",
                        ),
                        columns="4",
                        gap="4",
                        width="100%",
                        mb="3",
                    ),
                    rx.grid(
                        rx.vstack(
                            rx.text("Status", weight="bold", size="2"),
                            rx.select(
                                ["Pendente", "Quitada"],
                                value=FinanceState.novo_status,
                                on_change=FinanceState.set_novo_status,
                                width="100%",
                            ),
                            spacing="1",
                        ),
                        rx.box(
                            rx.button(
                                "Cadastrar Dívida",
                                on_click=FinanceState.cadastrar_divida,
                                color_scheme="blue",
                                width="100%",
                            ),
                            width="100%",
                        ),
                        columns="2",
                        gap="4",
                        width="100%",
                        align_items="end",
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
                # --- TABELA DE DÍVIDAS COM ROLAGEM VERTICAL ---
                rx.heading(
                    "Suas Dívidas Ativas e Parcelamentos",
                    font_size="1.2rem",
                    color="#1e293b",
                    mb="3",
                ),
                rx.cond(
                    RaioXDividasState.lista_dividas_exibicao.length() > 0,
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("ID"),
                                    rx.table.column_header_cell("Credor"),
                                    rx.table.column_header_cell("Valor Total"),
                                    rx.table.column_header_cell("Parcelas"),
                                    rx.table.column_header_cell("Valor Parcela"),
                                    rx.table.column_header_cell("Vencimento"),
                                    rx.table.column_header_cell("Status"),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(
                                    RaioXDividasState.lista_dividas_exibicao,
                                    lambda item: rx.table.row(
                                        rx.table.cell(item["id"]),
                                        rx.table.cell(item["credor"]),
                                        rx.table.cell(item["valor_total"]),
                                        rx.table.cell(item["total_parcelas"]),
                                        rx.table.cell(item["valor_parcela"]),
                                        rx.table.cell(item["dia_vencimento"]),
                                        rx.table.cell(item["status"]),
                                    ),
                                )
                            ),
                            variant="surface",
                            size="2",
                            width="100%",
                        ),
                        max_height="320px",  # Altura controlada com barra de rolagem vertical
                        overflow_y="auto",
                        width="100%",
                        border="1px solid #e2e8f0",
                        border_radius="8px",
                        mb="6",
                    ),
                    rx.text(
                        "Nenhuma dívida cadastrada no momento.",
                        color="gray",
                        mb="6",
                    ),
                ),
                rx.divider(mb="4"),
                # --- SEÇÃO DE GERENCIAMENTO / EDIÇÃO ---
                rx.heading(
                    "✏️ Editar ou Excluir Dívida",
                    font_size="1.2rem",
                    color="#1e293b",
                    mb="3",
                ),
                rx.select(
                    FinanceState.lista_resumo_dividas,
                    placeholder="Selecione uma dívida para gerenciar...",
                    on_change=FinanceState.selecionar_divida,
                    width="100%",
                    mb="4",
                ),
                rx.cond(
                    FinanceState.id_selecionado > 0,
                    rx.vstack(
                        rx.grid(
                            rx.vstack(
                                rx.text("Credor", weight="bold", size="2"),
                                rx.input(
                                    value=FinanceState.edit_credor,
                                    on_change=FinanceState.set_edit_credor,
                                    width="100%",
                                ),
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text(
                                    "Valor Total (R$)", weight="bold", size="2"
                                ),
                                rx.input(
                                    value=FinanceState.edit_valor_total,
                                    on_change=FinanceState.set_edit_valor_total,
                                    width="100%",
                                ),
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text(
                                    "Total Parcelas", weight="bold", size="2"
                                ),
                                rx.input(
                                    value=FinanceState.edit_total_parcelas,
                                    on_change=FinanceState.set_edit_total_parcelas,
                                    width="100%",
                                ),
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text(
                                    "Valor Parcela (R$)",
                                    weight="bold",
                                    size="2",
                                ),
                                rx.input(
                                    value=FinanceState.edit_valor_parcela,
                                    on_change=FinanceState.set_edit_valor_parcela,
                                    width="100%",
                                ),
                                spacing="1",
                            ),
                            columns="4",
                            gap="4",
                            width="100%",
                            mb="3",
                        ),
                        rx.grid(
                            rx.vstack(
                                rx.text(
                                    "Dia Vencimento", weight="bold", size="2"
                                ),
                                rx.input(
                                    value=FinanceState.edit_dia_vencimento,
                                    on_change=FinanceState.set_edit_dia_vencimento,
                                    width="100%",
                                ),
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("Status", weight="bold", size="2"),
                                rx.select(
                                    ["Pendente", "Quitada"],
                                    value=FinanceState.edit_status,
                                    on_change=FinanceState.set_edit_status,
                                    width="100%",
                                ),
                                spacing="1",
                            ),
                            rx.hstack(
                                rx.button(
                                    "Salvar Alterações",
                                    on_click=FinanceState.salvar_edicao,
                                    color_scheme="green",
                                    width="50%",
                                ),
                                rx.button(
                                    "Excluir Dívida",
                                    on_click=FinanceState.excluir_divida,
                                    color_scheme="red",
                                    width="50%",
                                ),
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
                    rx.text(
                        "Selecione uma dívida acima para carregar os dados de alteração.",
                        color="gray",
                        mb="6",
                    ),
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