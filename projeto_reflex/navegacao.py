import reflex as rx

def barra_navegacao() -> rx.Component:
    return rx.hstack(
        rx.heading("💰 Finanças", size="6", color="white"),
        rx.hstack(
            rx.link("Dashboard", href="/", color="white", _hover={"color": "lightblue"}),
            rx.link("Novo Lançamento", href="/lancamentos", color="white", _hover={"color": "lightblue"}),
            rx.link("Gerenciar", href="/gerenciar", color="white", _hover={"color": "lightblue"}),
            rx.link("Raio-X Dívidas", href="/raio-x-dividas", color="white", _hover={"color": "lightblue"}),
            rx.link("Investimentos", href="/investimentos", color="white", _hover={"color": "lightblue"}),
            rx.link("Relatórios", href="/relatorios", color="white", _hover={"color": "lightblue"}),
            rx.link("Reserva", href="/reserva", color="white", _hover={"color": "lightblue"}),
            rx.link("Dividendos", href="/dividendos", color="white", _hover={"color": "lightblue"}),
            rx.link("Milenar", href="/milenar", color="white", _hover={"color": "lightblue"}),  # <--- LINK ADICIONADO AQUI
            spacing="3"
        ),
        justify="between",
        align="center",
        width="100%",
        padding="1em",
        bg="blue",
        margin_bottom="2em",
    )