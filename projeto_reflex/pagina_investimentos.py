import reflex as rx
import pandas as pd
import database
from projeto_reflex.states import FinanceState
from .navegacao import barra_navegacao

class InvestimentosState(rx.State):
    refresh_trigger: int = 0

    id_selecionado: int = 0
    tabela_origem: str = "desafio_aportes"
    
    edit_data: str = ""
    edit_valor: str = ""
    edit_local: str = ""

    def carregar_dados_investimentos(self):
        self.refresh_trigger += 1

    def set_id_selecionado(self, valor: str):
        if not valor:
            self.cancelar_edicao()
            return
        try:
            partes = valor.split(" | ")
            id_str = partes[0].replace("ID:", "").strip()
            self.id_selecionado = int(id_str)
            self.tabela_origem = partes[1].strip()
            
            database.inicializar_banco()
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            
            tabela_bd = "lancamentos" if self.tabela_origem == "lancamentos" else ("desafio_aportes" if self.tabela_origem == "desafio_aportes" else "desafio_rendimentos")
            col_local = "descricao" if self.tabela_origem == "lancamentos" else "local_aplicacao"
            
            cursor.execute(f"SELECT data, valor, {col_local} FROM {tabela_bd} WHERE id = %s", (self.id_selecionado,))
            row = cursor.fetchone()
            cursor.close()
            conexao.close()
            
            if row:
                self.edit_data = str(row[0])
                self.edit_valor = f"{float(row[1]):.2f}"
                self.edit_local = str(row[2])
        except Exception as e:
            print(f"Erro ao selecionar registo: {e}")

    def cancelar_edicao(self):
        self.id_selecionado = 0
        self.edit_data = ""
        self.edit_valor = ""
        self.edit_local = ""

    def set_edit_data(self, v: str): self.edit_data = v
    def set_edit_valor(self, v: str): self.edit_valor = v
    def set_edit_local(self, v: str): self.edit_local = v

    def salvar_alteracao(self):
        if not self.id_selecionado:
            return rx.window_alert("Nenhum registo selecionado para edição.")
        try:
            val = float(self.edit_valor.replace(",", "."))
            database.inicializar_banco()
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            
            tabela_bd = "lancamentos" if self.tabela_origem == "lancamentos" else ("desafio_aportes" if self.tabela_origem == "desafio_aportes" else "desafio_rendimentos")
            col_local = "descricao" if self.tabela_origem == "lancamentos" else "local_aplicacao"
            
            cursor.execute(
                f"UPDATE {tabela_bd} SET data = %s, valor = %s, {col_local} = %s WHERE id = %s",
                (self.edit_data.strip(), val, self.edit_local.strip(), self.id_selecionado)
            )
            conexao.commit()
            cursor.close()
            conexao.close()
            
            self.cancelar_edicao()
            self.refresh_trigger += 1
            return rx.window_alert("Registo atualizado com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao atualizar: {e}")

    def excluir_registo(self):
        if not self.id_selecionado:
            return rx.window_alert("Nenhum registo selecionado.")
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            
            tabela_bd = "lancamentos" if self.tabela_origem == "lancamentos" else ("desafio_aportes" if self.tabela_origem == "desafio_aportes" else "desafio_rendimentos")
            
            cursor.execute(f"DELETE FROM {tabela_bd} WHERE id = %s", (self.id_selecionado,))
            conexao.commit()
            cursor.close()
            conexao.close()
            
            self.cancelar_edicao()
            self.refresh_trigger += 1
            return rx.window_alert("Registo excluído com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao excluir: {e}")

    @rx.var
    def df_investimentos_total(self) -> pd.DataFrame:
        _ = self.refresh_trigger
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            
            try:
                df_a = pd.read_sql_query("SELECT id, data, valor, local_aplicacao, 'desafio_aportes' as tabela FROM desafio_aportes", conexao)
            except:
                df_a = pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao", "tabela"])

            try:
                df_r = pd.read_sql_query("SELECT id, data, valor, local_aplicacao, 'desafio_rendimentos' as tabela FROM desafio_rendimentos", conexao)
            except:
                df_r = pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao", "tabela"])

            try:
                df_g = pd.read_sql_query("""
                    SELECT id, data, valor, COALESCE(descricao, categoria, 'Investimento') AS local_aplicacao, 'lancamentos' as tabela 
                    FROM lancamentos 
                    WHERE LOWER(tipo) IN ('investimento', 'investimentos', 'aporte', 'aportes') 
                       OR LOWER(categoria) IN ('investimento', 'investimentos', 'aporte', 'aportes')
                """, conexao)
            except:
                try:
                    df_g = pd.read_sql_query("SELECT id, data, valor, descricao AS local_aplicacao, 'lancamentos' as tabela FROM lancamentos", conexao)
                except:
                    df_g = pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao", "tabela"])

            conexao.close()
            
            df_base = pd.concat([df_a, df_g], ignore_index=True)
            if not df_base.empty:
                df_base["valor"] = pd.to_numeric(df_base["valor"], errors="coerce").fillna(0.0)
                # Ordena por ID decrescente para que o investimento mais recente fique no topo
                df_base = df_base.sort_values(by="id", ascending=False).reset_index(drop=True)
                
                # Incorpora os rendimentos diretamente na aplicação mais recente da instituição correspondente
                if not df_r.empty:
                    df_r["valor"] = pd.to_numeric(df_r["valor"], errors="coerce").fillna(0.0)
                    for _, rend in df_r.iterrows():
                        loc_rend = str(rend["local_aplicacao"]).strip().lower()
                        val_rend = float(rend["valor"])
                        
                        mask = df_base["local_aplicacao"].astype(str).str.strip().str.lower().str.contains(loc_rend[:5], na=False)
                        if mask.any():
                            idx = df_base[mask].index[0] # Pega o primeiro após a ordenação (o mais recente ID 37)
                            df_base.loc[idx, "valor"] += val_rend
                        else:
                            novo = pd.DataFrame([{"id": rend["id"], "data": rend["data"], "valor": val_rend, "local_aplicacao": rend["local_aplicacao"], "tabela": "desafio_rendimentos"}])
                            df_base = pd.concat([df_base, novo], ignore_index=True)

            if not df_base.empty:
                df_base = df_base.drop_duplicates(subset=["id", "tabela"], keep="first")
                df_base = df_base.sort_values(by="id", ascending=False)
            return df_base
        except Exception as e:
            print(f"Erro ao carregar investimentos: {e}")
            return pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao", "tabela"])

    @rx.var
    def total_liquido_investido(self) -> str:
        df = self.df_investimentos_total
        if df.empty or "valor" not in df.columns:
            return "R$ 0,00"
        total = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0).sum()
        return f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def lista_opcoes_select(self) -> list[str]:
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df_a = pd.read_sql_query("SELECT id, data, valor, local_aplicacao, 'desafio_aportes' as tabela FROM desafio_aportes", conexao)
            df_r = pd.read_sql_query("SELECT id, data, valor, local_aplicacao, 'desafio_rendimentos' as tabela FROM desafio_rendimentos", conexao)
            df_g = pd.read_sql_query("SELECT id, data, valor, COALESCE(descricao, categoria, 'Investimento') AS local_aplicacao, 'lancamentos' as tabela FROM lancamentos WHERE LOWER(tipo) IN ('investimento', 'investimentos', 'aporte', 'aportes')", conexao)
            conexao.close()
            df_all = pd.concat([df_a, df_r, df_g], ignore_index=True)
            if df_all.empty: return []
            itens = []
            for _, row in df_all.iterrows():
                val = float(row["valor"] or 0)
                itens.append(f"ID: {row['id']} | {row['tabela']} | {row['data']} | {row['local_aplicacao']} | R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            return itens
        except:
            return []

    @rx.var
    def lista_investimentos_exibicao(self) -> list[dict]:
        df = self.df_investimentos_total
        if df.empty: return []
        res = []
        for _, row in df.iterrows():
            val = float(row["valor"] or 0)
            res.append({
                "id": int(row["id"]),
                "tabela": str(row["tabela"]),
                "data": str(row["data"]),
                "local_aplicacao": str(row["local_aplicacao"]),
                "valor": f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            })
        return res

@rx.page(route="/investimentos", title="Orientação de Investimentos", on_load=InvestimentosState.carregar_dados_investimentos)
def pagina_investimentos() -> rx.Component:
    return rx.vstack(
        barra_navegacao(),
        rx.container(
            rx.vstack(
                rx.heading("🧭 Orientação e Gestão de Investimentos", font_size={"base": "1.3rem", "md": "1.5rem"}, color="#1e293b", margin_top="15px", margin_bottom="2px"),
                rx.text("Acompanhe e gerencie seus aportes, rendimentos e saldos por instituição.", color="#64748b", font_size="0.9rem", margin_bottom="15px"),
                rx.divider(mb="4"),
                
                # Card de Resumo
                rx.hstack(
                    rx.card(
                        rx.vstack(
                            rx.text("Total Aplicado / Investido (Com Rendimentos Incorporados)", font_size="sm", color="gray.500"),
                            rx.heading(InvestimentosState.total_liquido_investido, size={"base": "5", "md": "6"}),
                        ),
                        p="4", bg="white", border_radius="lg", shadow="sm", width="100%",
                    ),
                    spacing="4", width="100%", mb="6",
                ),

                # Módulo de Seleção para Edição / Exclusão
                rx.heading("✏️ Selecionar Registo para Editar ou Excluir", font_size="1.2rem", color="#1e293b", mb="2"),
                rx.flex(
                    rx.select(
                        InvestimentosState.lista_opcoes_select,
                        placeholder="Selecione um aporte ou rendimento...",
                        on_change=InvestimentosState.set_id_selecionado,
                        width="100%",
                    ),
                    rx.cond(
                        InvestimentosState.id_selecionado > 0,
                        rx.button("Cancelar", on_click=InvestimentosState.cancelar_edicao, color_scheme="gray", variant="soft"),
                    ),
                    direction={"base": "column", "sm": "row"}, spacing="3", align="center", width="100%", mb="4",
                ),

                # Área de Edição Ativa
                rx.cond(
                    InvestimentosState.id_selecionado > 0,
                    rx.vstack(
                        rx.text("Data (DD/MM/AAAA):", weight="bold", size="2"),
                        rx.input(value=InvestimentosState.edit_data, on_change=InvestimentosState.set_edit_data, width="100%"),

                        rx.text("Valor (R$):", weight="bold", size="2"),
                        rx.input(value=InvestimentosState.edit_valor, on_change=InvestimentosState.set_edit_valor, width="100%"),

                        rx.text("Instituição / Local:", weight="bold", size="2"),
                        rx.input(value=InvestimentosState.edit_local, on_change=InvestimentosState.set_edit_local, width="100%"),

                        rx.flex(
                            rx.button("💾 Salvar Alterações", on_click=InvestimentosState.salvar_alteracao, color_scheme="green"),
                            rx.button("🗑️ Excluir Registo", on_click=InvestimentosState.excluir_registo, color_scheme="red"),
                            spacing="4", mt="3", width="100%",
                        ),
                        spacing="3", padding="20px", border="1px solid #e2e8f0", border_radius="10px", bg="#fafafa", width="100%", mb="6",
                    ),
                ),

                rx.divider(mb="4"),

                # Tabela de Histórico
                rx.heading("📋 Histórico Geral de Investimentos Atualizados", font_size="1.2rem", color="#1e293b", mb="3"),
                rx.cond(
                    InvestimentosState.lista_investimentos_exibicao.length() > 0,
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("ID"),
                                    rx.table.column_header_cell("Tipo / Tabela"),
                                    rx.table.column_header_cell("Data"),
                                    rx.table.column_header_cell("Local / Aplicação"),
                                    rx.table.column_header_cell("Valor Atualizado"),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(
                                    InvestimentosState.lista_investimentos_exibicao,
                                    lambda item: rx.table.row(
                                        rx.table.cell(item["id"]),
                                        rx.table.cell(item["tabela"]),
                                        rx.table.cell(item["data"]),
                                        rx.table.cell(item["local_aplicacao"]),
                                        rx.table.cell(item["valor"]),
                                    ),
                                )
                            ),
                            variant="surface", size="3", width="100%",
                        ),
                        overflow_x="auto", width="100%", border="1px solid #e2e8f0", border_radius="8px", mb="6",
                    ),
                    rx.text("Nenhum registo encontrado.", color="gray", mb="6"),
                ),
                
                spacing="4", align_items="start", width="100%",
            ),
            width="100%", max_width="1200px", padding_x={"base": "1em", "md": "2em"}, padding_top="0em", center_content=True,
        ),
        width="100%", spacing="0", align="center", bg="gray.50", min_h="100vh",
    )