import reflex as rx
import pandas as pd
from datetime import datetime
import database

class LancamentoState(rx.State):
    """Estado específico para a página de lançamentos e resumo."""
    data: str = datetime.now().strftime("%d/%m/%Y")
    tipo: str = "Despesa"
    categoria: str = ""
    descricao: str = ""
    valor: str = ""
    
    def set_data(self, valor: str):
        self.data = valor

    def set_tipo(self, valor: str):
        self.tipo = valor

    def set_categoria(self, valor: str):
        self.categoria = valor

    def set_descricao(self, valor: str):
        self.descricao = valor

    def set_valor(self, valor: str):
        self.valor = valor

    def salvar_lancamento(self):
        """Função para salvar o lançamento na base de dados."""
        if not self.categoria.strip():
            return rx.window_alert("Por favor, preencha a categoria.")
        if not self.valor:
            return rx.window_alert("Por favor, preencha o valor.")
        try:
            datetime.strptime(self.data.strip(), "%d/%m/%Y")
            valor_float = float(self.valor.replace(",", "."))
            
            database.inicializar_banco()
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            cursor.execute(
                "INSERT INTO lancamentos (data, tipo, categoria, descricao, valor) VALUES (%s, %s, %s, %s, %s)",
                (self.data.strip(), self.tipo, self.categoria.strip(), self.descricao.strip(), valor_float)
            )
            conexao.commit()
            cursor.close()
            conexao.close()

            # Limpar campos principais após sucesso
            self.categoria = ""
            self.descricao = ""
            self.valor = ""
            return rx.window_alert("Lançamento guardado com sucesso!")
        except ValueError:
            return rx.window_alert("Data inválida. Utilize o formato DD/MM/AAAA.")
        except Exception as e:
            return rx.window_alert(f"Erro ao guardar: {e}")

    @rx.var
    def lista_lancamentos_mes(self) -> list[dict]:
        """Carrega o histórico de lançamentos do mês atual ordenado do mais recente para o mais antigo."""
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df = pd.read_sql_query("SELECT id, data, tipo, categoria, descricao, valor FROM lancamentos ORDER BY id DESC", conexao)
            conexao.close()

            if df.empty:
                return []

            dt = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
            df["competencia"] = dt.dt.strftime("%m/%Y")
            
            mes_atual = datetime.now().strftime("%m/%Y")
            df_mes = df[df["competencia"] == mes_atual]

            resultado = []
            for _, row in df_mes.iterrows():
                val_float = float(row['valor'])
                resultado.append({
                    "id": int(row["id"]),
                    "data": str(row["data"]),
                    "tipo": str(row["tipo"]),
                    "categoria": str(row["categoria"]),
                    "descricao": str(row["descricao"] or ""),
                    "valor": f"R$ {val_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                })
            return resultado
        except Exception:
            return []


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
                
                # Formulário Responsivo (Grid: 1 coluna no telemóvel, 3 no desktop)
                rx.vstack(
                    rx.grid(
                        rx.vstack(
                            rx.text("Data (DD/MM/AAAA)", weight="bold", size="2"),
                            rx.input(value=LancamentoState.data, on_change=LancamentoState.set_data, width="100%"),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Categoria", weight="bold", size="2"),
                            rx.input(value=LancamentoState.categoria, on_change=LancamentoState.set_categoria, placeholder="Ex: Alimentação, Transporte...", width="100%"),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Descrição / Estabelecimento", weight="bold", size="2"),
                            rx.input(value=LancamentoState.descricao, on_change=LancamentoState.set_descricao, placeholder="Ex: Supermercado...", width="100%"),
                            spacing="1",
                        ),
                        columns={"base": "1", "md": "3"},
                        gap="4",
                        width="100%",
                    ),

                    rx.grid(
                        rx.vstack(
                            rx.text("Tipo", weight="bold", size="2"),
                            rx.select(["Despesa", "Receita", "Investimento"], value=LancamentoState.tipo, on_change=LancamentoState.set_tipo, width="100%"),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Valor (R$)", weight="bold", size="2"),
                            rx.input(value=LancamentoState.valor, on_change=LancamentoState.set_valor, placeholder="0.00", width="100%"),
                            spacing="1",
                        ),
                        rx.box(
                            rx.button("Salvar Lançamento", on_click=LancamentoState.salvar_lancamento, color_scheme="blue", width="100%"),
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

                # Histórico com altura limitada e Rolagem Vertical/Horizontal
                rx.heading("📋 Histórico de Lançamentos da Competência Atual", font_size="1.2rem", color="#1e293b", mb="3"),
                rx.cond(
                    LancamentoState.lista_lancamentos_mes.length() > 0,
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
                                    LancamentoState.lista_lancamentos_mes,
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