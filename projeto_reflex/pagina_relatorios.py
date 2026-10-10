import reflex as rx
import pandas as pd
from datetime import datetime
import database

class RelatoriosState(rx.State):
    """Estado para gerir relatórios, filtros, fechamento e projeções."""
    competencia_selecionada: str = datetime.now().strftime("%m/%Y")
    
    # Filtros da Aba 1
    usar_filtro_comp: bool = True
    filtro_tipo: str = "Todos"
    filtro_texto: str = ""

    # Projeções Aba 3
    proj_meses: int = 6

    # Setters necessários para os filtros
    def set_filtro_tipo(self, valor: str):
        self.filtro_tipo = valor

    def set_filtro_texto(self, valor: str):
        self.filtro_texto = valor

    @rx.var
    def competencias_disponiveis(self) -> list[str]:
        mes_atual = datetime.now().strftime("%m/%Y")
        comps = [mes_atual]
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df_l = pd.read_sql_query("SELECT data FROM lancamentos", conexao)
            conexao.close()
            if not df_l.empty and "data" in df_l.columns:
                dt = pd.to_datetime(df_l["data"], format="%d/%m/%Y", errors="coerce", dayfirst=True)
                comps.extend(dt.dt.strftime("%m/%Y").dropna().tolist())
        except Exception:
            pass
        return sorted(list(set(comps)), reverse=True)

    @rx.var
    def df_lancamentos_raw(self) -> pd.DataFrame:
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df = pd.read_sql_query("SELECT id, data, tipo, categoria, descricao, valor FROM lancamentos ORDER BY id DESC", conexao)
            conexao.close()
            if df.empty:
                return pd.DataFrame(columns=["id", "data", "tipo", "categoria", "descricao", "valor"])
            df["data_dt"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce", dayfirst=True)
            df["competencia"] = df["data_dt"].dt.strftime("%m/%Y")
            return df
        except Exception:
            return pd.DataFrame(columns=["id", "data", "tipo", "categoria", "descricao", "valor"])

    @rx.var
    def lista_lancamentos_filtrados(self) -> list[dict]:
        df = self.df_lancamentos_raw
        if df.empty:
            return []

        df_f = df.copy()
        if self.usar_filtro_comp:
            df_f = df_f[df_f["competencia"] == self.competencia_selecionada]
        
        if self.filtro_tipo != "Todos":
            df_f = df_f[df_f["tipo"] == self.filtro_tipo]

        if self.filtro_texto:
            mask = df_f["descricao"].str.contains(self.filtro_texto, case=False, na=False)
            df_f = df_f[mask]

        resultado = []
        for _, row in df_f.iterrows():
            val = float(row["valor"] or 0.0)
            val_fmt = f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            resultado.append({
                "id": int(row["id"]),
                "data": str(row["data"]),
                "tipo": str(row["tipo"]),
                "categoria": str(row["categoria"]),
                "descricao": str(row["descricao"] or ""),
                "valor": val_fmt,
            })
        return resultado

    @rx.var
    def total_filtrado_fmt(self) -> str:
        df = self.df_lancamentos_raw
        if df.empty:
            return "R$ 0,00"
        df_f = df.copy()
        if self.usar_filtro_comp:
            df_f = df_f[df_f["competencia"] == self.competencia_selecionada]
        if self.filtro_tipo != "Todos":
            df_f = df_f[df_f["tipo"] == self.filtro_tipo]
        if self.filtro_texto:
            df_f = df_f[df_f["descricao"].str.contains(self.filtro_texto, case=False, na=False)]
        
        total = pd.to_numeric(df_f["valor"], errors="coerce").sum()
        return f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def lista_fechamento_mensal(self) -> list[dict]:
        df = self.df_lancamentos_raw
        if df.empty or "data_dt" not in df.columns:
            return []
        
        df_val = df.dropna(subset=["data_dt"]).copy()
        if df_val.empty:
            return []

        df_val["ano_mes"] = df_val["data_dt"].dt.to_period("M")
        
        rec = df_val[df_val["tipo"] == "Receita"].groupby("ano_mes")["valor"].sum().reset_index(name="entradas")
        desp = df_val[df_val["tipo"] == "Despesa"].groupby("ano_mes")["valor"].sum().reset_index(name="saidas")

        fech = pd.merge(rec, desp, on="ano_mes", how="outer").fillna(0.0)
        fech = fech.sort_values(by="ano_mes", ascending=True).reset_index(drop=True)

        fech["resultado"] = fech["entradas"] - fech["saidas"]
        fech["acumulado"] = fech["resultado"].cumsum()

        tabela = []
        for _, row in fech.iterrows():
            mes_str = row["ano_mes"].strftime("%m/%Y")
            tabela.append({
                "mes": mes_str,
                "entradas": f"R$ {row['entradas']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "saidas": f"R$ {row['saidas']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "resultado": f"R$ {row['resultado']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "acumulado": f"R$ {row['acumulado']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            })
        return tabela


@rx.page(route="/relatorios", title="Relatórios e Consultas")
def pagina_relatorios() -> rx.Component:
    from .navegacao import barra_navegacao

    return rx.vstack(
        barra_navegacao(),
        rx.container(
            rx.vstack(
                rx.heading("📈 Relatórios, Consultas e Fechamento", font_size="1.5rem", color="#1e293b", margin_top="15px", margin_bottom="2px"),
                rx.text("Filtre lançamentos, acompanhe o fechamento mensal e analise o histórico financeiro.", color="#64748b", font_size="0.9rem", margin_bottom="15px"),
                rx.divider(mb="4"),

                # Abas Principais em Tabs do Reflex
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("🔍 Consulta & Filtros", value="tab1"),
                        rx.tabs.trigger("📅 Fechamento de Mês", value="tab2"),
                    ),
                    
                    # --- ABA 1: CONSULTA E FILTROS ---
                    rx.tabs.content(
                        rx.vstack(
                            rx.heading("Filtrar Lançamentos", font_size="1.2rem", color="#1e293b", mt="3", mb="3"),
                            rx.hstack(
                                rx.select(["Todos", "Receita", "Despesa"], value=RelatoriosState.filtro_tipo, on_change=RelatoriosState.set_filtro_tipo),
                                rx.input(placeholder="Buscar na descrição...", value=RelatoriosState.filtro_texto, on_change=RelatoriosState.set_filtro_texto, width="100%"),
                                width="100%",
                                mb="2",
                            ),
                            rx.text(rx.text("Total Filtrado: ", weight="bold"), RelatoriosState.total_filtrado_fmt, color="blue", mb="4"),

                            # Tabela de Resultados
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("ID"),
                                        rx.table.column_header_cell("Data"),
                                        rx.table.column_header_cell("Tipo"),
                                        rx.table.column_header_cell("Categoria"),
                                        rx.table.column_header_cell("Descrição"),
                                        rx.table.column_header_cell("Valor"),
                                    )
                                ),
                                rx.table.body(
                                    rx.foreach(
                                        RelatoriosState.lista_lancamentos_filtrados,
                                        lambda item: rx.table.row(
                                            rx.table.cell(item["id"]),
                                            rx.table.cell(item["data"]),
                                            rx.table.cell(item["tipo"]),
                                            rx.table.cell(item["categoria"]),
                                            rx.table.cell(item["descricao"]),
                                            rx.table.cell(item["valor"]),
                                        )
                                    )
                                ),
                                variant="surface",
                                size="3",
                                width="100%",
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        value="tab1",
                    ),

                    # --- ABA 2: FECHAMENTO MENSAL ---
                    rx.tabs.content(
                        rx.vstack(
                            rx.heading("Fechamento Mensal e Saldo Remanescente", font_size="1.2rem", color="#1e293b", mt="3", mb="3"),
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("Mês/Ano"),
                                        rx.table.column_header_cell("Entradas"),
                                        rx.table.column_header_cell("Saídas"),
                                        rx.table.column_header_cell("Resultado do Mês"),
                                        rx.table.column_header_cell("Saldo Acumulado"),
                                    )
                                ),
                                rx.table.body(
                                    rx.foreach(
                                        RelatoriosState.lista_fechamento_mensal,
                                        lambda item: rx.table.row(
                                            rx.table.cell(item["mes"]),
                                            rx.table.cell(item["entradas"]),
                                            rx.table.cell(item["saidas"]),
                                            rx.table.cell(item["resultado"]),
                                            rx.table.cell(item["acumulado"]),
                                        )
                                    )
                                ),
                                variant="surface",
                                size="3",
                                width="100%",
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        value="tab2",
                    ),
                    default_value="tab1",
                    width="100%",
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