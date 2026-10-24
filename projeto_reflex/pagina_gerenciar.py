import reflex as rx
import pandas as pd
from datetime import datetime
import database

class GerenciarState(rx.State):
    """Estado para gerir, editar e excluir lançamentos e dívidas."""
    
    # Gatilho para forçar a atualização imediata das listas e tabelas
    refresh_trigger: int = 0
    
    competencia_selecionada: str = datetime.now().strftime("%m/%Y")
    id_selecionado: int = 0
    
    # Campos do formulário de edição
    categoria_edit: str = ""
    descricao_edit: str = ""
    valor_edit: str = ""
    data_edit: str = ""
    tipo_atual: str = ""

    def set_competencia_selecionada(self, nova_competencia: str):
        self.competencia_selecionada = nova_competencia
        self.cancelar_selecao()

    def set_tipo_atual(self, valor: str):
        self.tipo_atual = valor

    def set_categoria_edit(self, valor: str):
        self.categoria_edit = valor

    def set_descricao_edit(self, valor: str):
        self.descricao_edit = valor

    def set_valor_edit(self, valor: str):
        self.valor_edit = valor

    def set_data_edit(self, valor: str):
        self.data_edit = valor

    def cancelar_selecao(self):
        self.id_selecionado = 0
        self.categoria_edit = ""
        self.descricao_edit = ""
        self.valor_edit = ""
        self.data_edit = ""
        self.tipo_atual = ""

    @rx.var
    def competencias_disponiveis(self) -> list[str]:
        _ = self.refresh_trigger
        mes_atual = datetime.now().strftime("%m/%Y")
        comps = [mes_atual]
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df_l = pd.read_sql_query("SELECT data FROM lancamentos", conexao)
            df_a = pd.read_sql_query("SELECT data FROM desafio_aportes", conexao)
            conexao.close()

            for df_item in [df_l, df_a]:
                if not df_item.empty and "data" in df_item.columns:
                    dt = pd.to_datetime(df_item["data"], format="%d/%m/%Y", errors="coerce", dayfirst=True)
                    comps.extend(dt.dt.strftime("%m/%Y").dropna().tolist())
        except Exception:
            pass
        
        return sorted(list(set(comps)), reverse=True)

    @rx.var
    def lista_lancamentos_mes(self) -> list[dict]:
        """Retorna os lançamentos manuais filtrados pela competência selecionada."""
        _ = self.refresh_trigger
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df = pd.read_sql_query("SELECT id, data, tipo, categoria, descricao, valor FROM lancamentos ORDER BY id DESC", conexao)
            conexao.close()

            if df.empty:
                return []

            dt = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce", dayfirst=True)
            df["competencia"] = dt.dt.strftime("%m/%Y")
            
            df_mes = df[df["competencia"] == self.competencia_selecionada]
            
            resultado = []
            for _, row in df_mes.iterrows():
                desc = row["descricao"]
                desc_str = "" if pd.isna(desc) else str(desc)
                val_float = float(row['valor'])
                resultado.append({
                    "id": int(row["id"]),
                    "data": str(row["data"]),
                    "tipo": str(row["tipo"]),
                    "categoria": str(row["categoria"]),
                    "descricao": desc_str,
                    "valor": f"R$ {val_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                })
            return resultado
        except Exception:
            return []

    @rx.var
    def itens_select_lancamentos(self) -> list[str]:
        _ = self.refresh_trigger
        itens = []
        for l in self.lista_lancamentos_mes:
            itens.append(f"{l['id']} - {l['data']} | {l['tipo']} | {l['categoria']} | {l['valor']}")
        return itens

    def selecionar_lancamento(self, selecao: str):
        if not selecao:
            return
        try:
            id_str = selecao.split(" - ")[0].strip()
            id_num = int(id_str)
            self.id_selecionado = id_num
            
            database.inicializar_banco()
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            cursor.execute("SELECT tipo, categoria, descricao, valor, data FROM lancamentos WHERE id = %s", (id_num,))
            row = cursor.fetchone()
            conexao.close()
            
            if row:
                self.tipo_atual = str(row[0] or "")
                self.categoria_edit = str(row[1] or "")
                self.descricao_edit = str(row[2] or "")
                self.valor_edit = str(row[3] or "0.0")
                self.data_edit = str(row[4] or "")
        except Exception as e:
            print(f"Erro ao selecionar: {e}")

    def salvar_alteracoes(self):
        if not self.id_selecionado:
            return rx.window_alert("Selecione um lançamento para editar.")
        try:
            datetime.strptime(self.data_edit.strip(), "%d/%m/%Y")
            val_limpo = abs(float(self.valor_edit.replace(",", ".")))
            
            database.inicializar_banco()
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            cursor.execute(
                "UPDATE lancamentos SET tipo = %s, data = %s, categoria = %s, descricao = %s, valor = %s WHERE id = %s",
                (self.tipo_atual.strip(), self.data_edit.strip(), self.categoria_edit.strip(), self.descricao_edit.strip(), val_limpo, self.id_selecionado)
            )
            conexao.commit()
            cursor.close()
            conexao.close()
            
            self.cancelar_selecao()
            self.refresh_trigger += 1  # <-- Atualiza instantaneamente a tabela e o seletor
            return rx.window_alert("Lançamento atualizado com sucesso!")
        except ValueError:
            return rx.window_alert("Data inválida. Utilize o formato DD/MM/AAAA.")
        except Exception as e:
            return rx.window_alert(f"Erro ao atualizar: {e}")
        
    def excluir_lancamento(self):
        if not self.id_selecionado:
            return rx.window_alert("Nenhum lançamento selecionado.")
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM lancamentos WHERE id = %s", (self.id_selecionado,))
            conexao.commit()
            cursor.close()
            conexao.close()
            
            self.cancelar_selecao()
            self.refresh_trigger += 1  # <-- Atualiza instantaneamente a tabela e o seletor
            return rx.window_alert("Lançamento excluído com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao excluir: {e}")


@rx.page(route="/gerenciar", title="Gerenciar Lançamentos")
def pagina_gerenciar() -> rx.Component:
    from .navegacao import barra_navegacao

    return rx.vstack(
        barra_navegacao(),
        rx.container(
            rx.vstack(
                rx.heading("✏️ Gerenciar, Editar ou Excluir Lançamentos", font_size={"base": "1.3rem", "md": "1.5rem"}, color="#1e293b", margin_top="15px", margin_bottom="2px"),
                rx.text("Gerencie e corrija os seus lançamentos manuais diretamente.", color="#64748b", font_size="0.9rem", margin_bottom="15px"),
                rx.divider(mb="4"),

                # Filtro de Competência Responsivo
                rx.hstack(
                    rx.text("Mês/Ano de Referência:", weight="bold"),
                    rx.select(
                        GerenciarState.competencias_disponiveis,
                        value=GerenciarState.competencia_selecionada,
                        on_change=GerenciarState.set_competencia_selecionada,
                    ),
                    align="center",
                    wrap="wrap",
                    mb="4",
                ),

                rx.divider(mb="4"),

                # Seleção de lançamento para editar
                rx.heading("🔄 Selecionar Lançamento para Edição ou Correção", font_size="1.2rem", color="#1e293b", mb="3"),
                rx.flex(
                    rx.select(
                        GerenciarState.itens_select_lancamentos,
                        placeholder="Selecione um lançamento...",
                        on_change=GerenciarState.selecionar_lancamento,
                        width="100%",
                    ),
                    rx.cond(
                        GerenciarState.id_selecionado > 0,
                        rx.button("Cancelar", on_click=GerenciarState.cancelar_selecao, color_scheme="gray", variant="soft"),
                    ),
                    direction={"base": "column", "sm": "row"},
                    spacing="3",
                    align="center",
                    width="100%",
                    mb="4",
                ),

                # Área de Edição / Alteração de Tipo / Exclusão
                rx.cond(
                    GerenciarState.id_selecionado > 0,
                    rx.vstack(
                        rx.text("Tipo do Lançamento:", weight="bold", size="2"),
                        rx.select(
                            ["Despesa", "Receita", "Investimento"],
                            value=GerenciarState.tipo_atual,
                            on_change=GerenciarState.set_tipo_atual,
                            width="100%",
                        ),
                        
                        rx.text("Categoria:", weight="bold", size="2"),
                        rx.input(
                            value=GerenciarState.categoria_edit, 
                            on_change=GerenciarState.set_categoria_edit,
                            width="100%",
                        ),

                        rx.text("Descrição:", weight="bold", size="2"),
                        rx.input(
                            value=GerenciarState.descricao_edit, 
                            on_change=GerenciarState.set_descricao_edit,
                            width="100%",
                        ),

                        rx.text("Valor (R$):", weight="bold", size="2"),
                        rx.input(
                            value=GerenciarState.valor_edit, 
                            on_change=GerenciarState.set_valor_edit,
                            width="100%",
                        ),

                        rx.text("Data (DD/MM/AAAA):", weight="bold", size="2"),
                        rx.input(
                            value=GerenciarState.data_edit, 
                            on_change=GerenciarState.set_data_edit,
                            width="100%",
                        ),

                        rx.flex(
                            rx.button("Salvar Alterações", on_click=GerenciarState.salvar_alteracoes, color_scheme="green"),
                            rx.button("Excluir Lançamento", on_click=GerenciarState.excluir_lancamento, color_scheme="red"),
                            direction={"base": "column", "sm": "row"},
                            spacing="4",
                            width="100%",
                            mt="3",
                        ),
                        spacing="3",
                        padding={"base": "16px", "md": "24px"},
                        border="1px solid #e2e8f0",
                        border_radius="10px",
                        bg="#fafafa",
                        width="100%",
                        mb="6",
                    ),
                ),

                rx.divider(mb="4"),

                # Tabela Restrita com Rolagem Vertical e Horizontal para Mobile
                rx.heading("📋 Lançamentos do Mês Selecionado", font_size="1.2rem", color="#1e293b", mb="3"),
                rx.cond(
                    GerenciarState.lista_lancamentos_mes.length() > 0,
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
                                    GerenciarState.lista_lancamentos_mes,
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
                        mb="6",
                    ),
                    rx.text("Nenhum lançamento encontrado para esta competência.", color="gray", mb="6"),
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