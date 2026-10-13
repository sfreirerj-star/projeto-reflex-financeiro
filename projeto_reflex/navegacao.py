import reflex as rx

def barra_navegacao() -> rx.Component:
    return rx.flex(
        rx.heading("💰 Finanças", size={"base": "5", "md": "6"}, color="white"),
        rx.flex(
            rx.link("Dashboard", href="/", color="white", _hover={"color": "lightblue"}, weight="bold"),
            rx.link("Novo Lançamento", href="/lancamentos", color="white", _hover={"color": "lightblue"}, weight="bold"),
            rx.link("Gerenciar", href="/gerenciar", color="white", _hover={"color": "lightblue"}, weight="bold"),
            rx.link("Raio-X Dívidas", href="/raio-x-dividas", color="white", _hover={"color": "lightblue"}, weight="bold"),
            rx.link("Investimentos", href="/investimentos", color="white", _hover={"color": "lightblue"}, weight="bold"),
            rx.link("Relatórios", href="/relatorios", color="white", _hover={"color": "lightblue"}, weight="bold"),
            rx.link("Reserva", href="/reserva", color="white", _hover={"color": "lightblue"}, weight="bold"),
            rx.link("Dividendos", href="/dividendos", color="white", _hover={"color": "lightblue"}, weight="bold"),
            rx.link("Milenar", href="/milenar", color="white", _hover={"color": "lightblue"}, weight="bold"),
            direction="row",
            wrap="wrap",
            spacing={"base": "2", "md": "4"},
            align="center",
        ),
        direction={"base": "column", "md": "row"},
        justify="between",
        align="center",
        width="100%",
        padding={"base": "0.8em 1em", "md": "1em 2em"},
        bg="blue",
        margin_bottom="2em",
        wrap="wrap",
    )