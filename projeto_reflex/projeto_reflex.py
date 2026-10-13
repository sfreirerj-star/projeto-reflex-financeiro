import reflex as rx
from projeto_reflex.states import FinanceState
from projeto_reflex.navegacao import barra_navegacao
from .pagina_lancamentos import pagina_lancamentos
from .pagina_raio_x_dividas import pagina_raio_x_dividas
from .pagina_gerenciar import pagina_gerenciar
from .pagina_investimentos import pagina_investimentos
from .pagina_aportes import pagina_aportes
from .pagina_desafio import pagina_desafio
from .pagina_dividendos import pagina_dividendos
from .pagina_relatorios import pagina_relatorios
from .pagina_reserva import pagina_reserva
from .pagina_milenar import pagina_milenar

def card_resumo(titulo: str, valor: str, cor_texto: str = "#1e293b") -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(titulo, font_size="0.75rem", color="#64748b", font_weight="600"),
            rx.text(valor, font_size={"base": "1rem", "md": "1.15rem"}, color=cor_texto, font_weight="bold", white_space="nowrap"),
            spacing="1",
            align_items="start",
        ),
        bg="white",
        padding="14px",
        border_radius="10px",
        box_shadow="0 2px 4px rgba(0,0,0,0.05)",
        border="1px solid #e2e8f0",
        width=["100%", "220px"],
        flex_grow="1",
    )

def dashboard_resumo_competencia() -> rx.Component:
    return rx.vstack(
        rx.flex(
            rx.heading("Resumo da Competência e Visualização Gráfica", font_size={"base": "1rem", "md": "1.2rem"}, color="#1e293b"),
            rx.spacer(),
            rx.hstack(
                rx.text("Competência:", font_size="0.9rem", color="#64748b"),
                rx.input(
                    value=FinanceState.competencia_selecionada,
                    on_change=FinanceState.set_competencia_selecionada,
                    placeholder="MM/AAAA",
                    max_length=7,
                    style={"width": "130px", "minWidth": "130px", "display": "inline-block"},
                ),
                align_items="center",
                wrap="wrap",
            ),
            width="100%",
            direction={"base": "column", "md": "row"},
            align_items={"base": "start", "md": "center"},
            spacing="2",
            margin_bottom="15px",
        ),

        # Cartões de Resumo com Flexbox e wrap para perfeita adaptação mobile
        rx.flex(
            card_resumo("Saldo Anterior", FinanceState.fmt_saldo_anterior),
            card_resumo("Entradas", FinanceState.fmt_entradas, "#16a34a"),
            card_resumo("Gastos Comuns", FinanceState.fmt_gastos, "#dc2626"),
            card_resumo("Aportes do Mês", FinanceState.fmt_aportes),
            card_resumo("Saldo Final / Remanescente", FinanceState.fmt_saldo_final, "#2563eb"),
            direction="row",
            wrap="wrap",
            spacing="3",
            width="100%",
        ),
        width="100%",
        margin_bottom="25px",
    )

def pagina_dashboard() -> rx.Component:
    return rx.vstack(
        barra_navegacao(),  # Utiliza o menu unificado e responsivo
        rx.container(
            rx.vstack(
                rx.heading("Controle Financeiro - Painel do Marcelo", font_size={"base": "1.2rem", "md": "1.5rem"}, color="#1e293b", margin_top="15px", margin_bottom="2px"),
                rx.text("Aplicativo unificado de créditos, débitos e investimentos.", color="#64748b", font_size="0.9rem", margin_bottom="15px"),
                rx.divider(mb="4"),
                
                dashboard_resumo_competencia(),
                
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
        on_mount=FinanceState.calcular_resumo_competencia,
    )

# INICIALIZAÇÃO DA APLICAÇÃO E REGISTRO DE ROTAS
app = rx.App()
app.add_page(pagina_dashboard, route="/")
app.add_page(pagina_aportes, route="/aportes")
app.add_page(pagina_desafio, route="/desafio", title="Desafio Reserva & Simulador")
app.add_page(pagina_milenar, route="/milenar", title="Alocação Milenar - Talmude")