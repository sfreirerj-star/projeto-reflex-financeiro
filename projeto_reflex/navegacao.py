import reflex as rx

def menu_item(texto: str, url: str) -> rx.Component:
    """Componente auxiliar para renderizar cada botão de navegação."""
    return rx.link(
        rx.button(
            texto,
            variant="ghost",
            size="2",
            style={
                "color": "white",
                "padding_x": "10px",
                "padding_y": "6px",
                "font_weight": "500",
                "font_size": "14px",
                "white_space": "nowrap",
                "_hover": {
                    "background_color": "rgba(255, 255, 255, 0.2)",
                },
            },
        ),
        href=url,
    )

def barra_navegacao() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Título do App
            rx.hstack(
                rx.heading(
                    "💰 Finanças",
                    size="5",
                    color="white",
                    weight="bold",
                ),
                width="100%",
                justify="start",
                padding_bottom="4px",
            ),
            # Container de Links/Botões com rolagem horizontal e wrap flexível
            rx.hstack(
                menu_item("Dashboard", "/"),
                menu_item("Novo Lançamento", "/lancamentos"),
                menu_item("Gerenciar", "/gerenciar"),
                menu_item("Raio-X Dívidas", "/dividas"),
                menu_item("Desafio", "/milenar"),
                menu_item("Investimentos", "/investimentos"),
                menu_item("Relatórios", "/relatorios"),
                menu_item("Reserva", "/reserva"),
                menu_item("Dividendos", "/dividendos"),
                menu_item("Milenar", "/milenar"),
                spacing="2",
                wrap="wrap",
                width="100%",
                style={
                    "overflow_x": "auto",
                    "padding_bottom": "6px",
                },
            ),
            spacing="2",
            width="100%",
            max_width="1200px",
            margin_x="auto",
        ),
        background_color="#0033FF",
        padding_x=["12px", "24px"],
        padding_y="12px",
        width="100%",
        box_shadow="0 2px 8px rgba(0,0,0,0.15)",
    )