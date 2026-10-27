import reflex as rx
import pandas as pd
from datetime import datetime
import database
import io

class RelatoriosState(rx.State):
    """Estado unificado para relatórios com tratamento 100% resiliente de datas."""
    competencia_selecionada: str = datetime.now().strftime("%m/%Y")
    
    # Filtros da Aba 1
    usar_filtro_comp: bool = True
    filtro_tipo: str = "Todos"
    filtro_categoria: str = "Todas"
    filtro_texto: str = ""

    # Projeções Aba 3
    proj_meses: int = 6

    def set_competencia_selecionada(self, valor: str):
        self.competencia_selecionada = valor

    def set_usar_filtro_comp(self, valor: bool):
        self.usar_filtro_comp = valor

    def set_filtro_tipo(self, valor: str):
        self.filtro_tipo = valor

    def set_filtro_categoria(self, valor: str):
        self.filtro_categoria = valor

    def set_filtro_texto(self, valor: str):
        self.filtro_texto = valor

    def set_proj_meses(self, valor: str):
        try:
            self.proj_meses = int(valor)
        except ValueError:
            self.proj_meses = 6

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
                dt = pd.to_datetime(df_l["data"], errors="coerce")
                comps.extend(dt.dt.strftime("%m/%Y").dropna().tolist())
        except Exception:
            pass
        return sorted(list(set(comps)), reverse=True)

    @rx.var
    def categorias_disponiveis(self) -> list[str]:
        cats = ["Todas"]
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df_l = pd.read_sql_query("SELECT DISTINCT categoria FROM lancamentos", conexao)
            conexao.close()
            if not df_l.empty and "categoria" in df_l.columns:
                limpas = df_l["categoria"].dropna().str.strip().tolist()
                cats.extend([c for c in limpas if c])
        except Exception:
            pass
        return sorted(list(set(cats)))

    @rx.var
    def df_lancamentos_raw(self) -> pd.DataFrame:
        """Carrega todos os lançamentos garantindo conversão universal de datas."""
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df = pd.read_sql_query("SELECT id, data, tipo, categoria, descricao, valor FROM lancamentos ORDER BY id DESC", conexao)
            conexao.close()
            if df.empty:
                return pd.DataFrame(columns=["id", "data", "tipo", "categoria", "descricao", "valor", "data_dt", "competencia"])
            
            # Converte datas de forma totalmente flexível (aceita YYYY-MM-DD e DD/MM/YYYY)
            dt_parsed = pd.to_datetime(df["data"], errors="coerce")
            
            # Se houver datas não reconhecidas, tenta parsear assumindo dia primeiro
            mask_nat = dt_parsed.isna()
            if mask_nat.any():
                dt_parsed.loc[mask_nat] = pd.to_datetime(df.loc[mask_nat, "data"], errors="coerce", dayfirst=True)

            df["data_dt"] = dt_parsed
            df["competencia"] = df["data_dt"].dt.strftime("%m/%Y")
            
            # Fallback para string caso alguma data venha nula na conversão
            df["competencia"] = df["competencia"].fillna(df["data"].astype(str).str.slice(3, 10))
            return df
        except Exception as e:
            print(f"Erro ao carregar raw relatorios: {e}")
            return pd.DataFrame(columns=["id", "data", "tipo", "categoria", "descricao", "valor", "data_dt", "competencia"])

    @rx.var
    def df_filtrado(self) -> pd.DataFrame:
        df = self.df_lancamentos_raw
        if df.empty:
            return df

        df_f = df.copy()
        
        # Filtro de competência flexível
        if self.usar_filtro_comp:
            df_f = df_f[df_f["competencia"] == self.competencia_selecionada]
        
        if self.filtro_tipo != "Todos":
            df_f = df_f[df_f["tipo"] == self.filtro_tipo]

        if self.filtro_categoria != "Todas":
            df_f = df_f[df_f["categoria"] == self.filtro_categoria]

        if self.filtro_texto.strip():
            mask = df_f["descricao"].astype(str).str.contains(self.filtro_texto.strip(), case=False, na=False)
            df_f = df_f[mask]

        return df_f

    @rx.var
    def lista_lancamentos_filtrados(self) -> list[dict]:
        df_f = self.df_filtrado
        if df_f.empty:
            return []

        resultado = []
        for _, row in df_f.iterrows():
            val = float(row["valor"] or 0.0)
            val_fmt = f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            dt_obj = row["data_dt"]
            data_fmt = dt_obj.strftime("%d/%m/%Y") if pd.notna(dt_obj) else str(row["data"])

            resultado.append({
                "id": int(row["id"]),
                "data": data_fmt,
                "tipo": str(row["tipo"]),
                "categoria": str(row["categoria"]),
                "descricao": str(row["descricao"] or ""),
                "valor": val_fmt,
            })
        return resultado

    @rx.var
    def total_filtrado_fmt(self) -> str:
        df_f = self.df_filtrado
        if df_f.empty:
            return "R$ 0,00"
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
        df_val["valor_num"] = pd.to_numeric(df_val["valor"], errors="coerce").fillna(0.0)
        df_val["tipo_clean"] = df_val["tipo"].astype(str).str.strip().str.lower()

        rec = df_val[df_val["tipo_clean"].isin(["receita", "crédito", "credito"])].groupby("ano_mes")["valor_num"].sum().reset_index(name="entradas")
        desp = df_val[df_val["tipo_clean"].isin(["despesa", "débito", "debito"])].groupby("ano_mes")["valor_num"].sum().reset_index(name="saidas")

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

    def baixar_csv(self):
        df_export = self.df_filtrado.copy()
        if df_export.empty:
            return rx.window_alert("Nenhum dado disponível para exportação.")
        
        cols = [c for c in ["id", "data", "tipo", "categoria", "descricao", "valor"] if c in df_export.columns]
        df_export = df_export[cols]
        
        content = df_export.to_csv(index=False, sep=";", encoding="utf-8-sig")
        return rx.download(
            data=content.encode("utf-8-sig"),
            filename=f"relatorio_lancamentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )

    def baixar_excel(self):
        df_export = self.df_filtrado.copy()
        if df_export.empty:
            return rx.window_alert("Nenhum dado disponível para exportação.")
        
        cols = [c for c in ["id", "data", "tipo", "categoria", "descricao", "valor"] if c in df_export.columns]
        df_export = df_export[cols]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_export.to_excel(writer, index=False, sheet_name="Lançamentos")
        
        output.seek(0)
        return rx.download(
            data=output.getvalue(),
            filename=f"relatorio_lancamentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        )


@rx.page(route="/relatorios", title="Relatórios e Consultas")
def pagina_relatorios() -> rx.Component:
    from .navegacao import barra_navegacao

    return rx.vstack(
        barra_navegacao(),
        rx.container(
            rx.vstack(
                rx.heading("📊 Relatórios, Consultas e Fechamento de Mês", font_size={"base": "1.2rem", "md": "1.5rem"}, color="#1e293b", margin_top="15px", margin_bottom="2px"),
                rx.text("Filtre seus lançamentos detalhadamente, exporte relatórios, acompanhe o fechamento mês a mês e projete seu saldo futuro.", color="#64748b", font_size="0.9rem", margin_bottom="15px"),
                rx.divider(mb="4"),

                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("🔍 Consulta, Filtros e Ações", value="tab1"),
                        rx.tabs.trigger("📅 Fechamento de Mês", value="tab2"),
                        rx.tabs.trigger("🔮 Projeção de Saldo Futuro", value="tab3"),
                    ),
                    
                    rx.tabs.content(
                        rx.vstack(
                            rx.heading(f"🔍 Filtrar Lançamentos (Competência Ativa: {RelatoriosState.competencia_selecionada})", font_size="1.2rem", color="#1e293b", mt="3", mb="3"),
                            
                            rx.grid(
                                rx.hstack(
                                    rx.checkbox(
                                        "Filtrar por Mês Ativo",
                                        checked=RelatoriosState.usar_filtro_comp,
                                        on_change=RelatoriosState.set_usar_filtro_comp,
                                    ),
                                    rx.cond(
                                        RelatoriosState.usar_filtro_comp,
                                        rx.select(
                                            RelatoriosState.competencias_disponiveis,
                                            value=RelatoriosState.competencia_selecionada,
                                            on_change=RelatoriosState.set_competencia_selecionada,
                                            size="1",
                                        ),
                                    ),
                                    align="center",
                                    spacing="2",
                                    wrap="wrap",
                                ),
                                rx.vstack(
                                    rx.text("Filtrar por Tipo", size="1", color="gray", weight="bold"),
                                    rx.select(["Todos", "Receita", "Despesa", "Investimento"], value=RelatoriosState.filtro_tipo, on_change=RelatoriosState.set_filtro_tipo, width="100%"),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("Filtrar por Categoria", size="1", color="gray", weight="bold"),
                                    rx.select(RelatoriosState.categorias_disponiveis, value=RelatoriosState.filtro_categoria, on_change=RelatoriosState.set_filtro_categoria, width="100%"),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("Buscar na Descrição (Palavra-chave)", size="1", color="gray", weight="bold"),
                                    rx.input(placeholder="Ex: Supermercado...", value=RelatoriosState.filtro_texto, on_change=RelatoriosState.set_filtro_texto, width="100%"),
                                    spacing="1",
                                ),
                                columns={"base": "1", "sm": "2", "md": "4"},
                                spacing="3",
                                width="100%",
                                mb="4",
                            ),

                            rx.cond(
                                RelatoriosState.lista_lancamentos_filtrados.length() > 0,
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
                                        size="2",
                                        width="100%",
                                    ),
                                    max_height="320px",
                                    overflow_y="auto",
                                    overflow_x="auto",
                                    width="100%",
                                    border="1px solid #e2e8f0",
                                    border_radius="8px",
                                    mb="4",
                                ),
                                rx.text("Nenhum lançamento encontrado com os filtros aplicados.", color="gray", mb="4"),
                            ),

                            rx.callout(
                                rx.hstack(
                                    rx.text("📊 Total dos lançamentos filtrados:", weight="bold", size="3"),
                                    rx.text(RelatoriosState.total_filtrado_fmt, weight="bold", size="4", color="blue"),
                                    spacing="2",
                                    wrap="wrap",
                                ),
                                color_scheme="blue",
                                width="100%",
                                mb="4",
                            ),

                            rx.flex(
                                rx.button("📥 Baixar em CSV", variant="soft", color_scheme="gray", on_click=RelatoriosState.baixar_csv),
                                rx.button("📊 Baixar em Excel (.xlsx)", variant="soft", color_scheme="green", on_click=RelatoriosState.baixar_excel),
                                rx.button("🖨️ Imprimir / PDF", color_scheme="red", on_click=rx.window_alert("Abre caixa de impressão do navegador.")),
                                direction="row",
                                wrap="wrap",
                                spacing="3",
                                width="100%",
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        value="tab1",
                    ),

                    rx.tabs.content(
                        rx.vstack(
                            rx.heading("📅 Fechamento de Mês (Saldo Remanescente)", font_size="1.2rem", color="#1e293b", mt="3", mb="3"),
                            rx.box(
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
                                max_height="350px",
                                overflow_y="auto",
                                overflow_x="auto",
                                width="100%",
                                border="1px solid #e2e8f0",
                                border_radius="8px",
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        value="tab2",
                    ),

                    rx.tabs.content(
                        rx.vstack(
                            rx.heading("🔮 Projeção de Saldo Futuro", font_size="1.2rem", color="#1e293b", mt="3", mb="2"),
                            rx.text("Projete a evolução do seu saldo com base na média dos últimos meses.", color="gray", size="2", mb="3"),
                            
                            rx.hstack(
                                rx.text("Meses de Projeção:", weight="bold"),
                                rx.select(["3", "6", "12", "24"], value=str(RelatoriosState.proj_meses), on_change=RelatoriosState.set_proj_meses),
                                align="center",
                                wrap="wrap",
                                mb="4",
                            ),

                            rx.callout(
                                "Com base na média da sua receita e despesa atual, o seu fluxo de caixa projetado mantém a sustentabilidade orçamental.",
                                color_scheme="green",
                                width="100%",
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        value="tab3",
                    ),

                    default_value="tab1",
                    width="100%",
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