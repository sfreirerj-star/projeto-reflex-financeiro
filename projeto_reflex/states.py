import reflex as rx
import pandas as pd
import database
from datetime import datetime
from database import obter_conexao

class FinanceState(rx.State):
    # Competência e Totais do Dashboard
    competencia_selecionada: str = "10/2026"
    fmt_saldo_anterior: str = "R$ 0,00"
    fmt_entradas: str = "R$ 0,00"
    fmt_gastos: str = "R$ 0,00"
    fmt_aportes: str = "R$ 0,00"
    fmt_saldo_final: str = "R$ 0,00"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        database.inicializar_banco()
        self.calcular_resumo_competencia()

    def carregar_dados(self):
        """Método seguro para atualizar os dados do Dashboard."""
        self.calcular_resumo_competencia()

    # Variáveis de perfil e aportes
    escolha_perfil: str = "Conservador"
    algum_valor: str = ""
    data_aporte: str = ""
    valor_aporte: str = ""
    
    # Campos de Lançamentos
    descricao: str = ""
    valor: str = ""
    categoria: str = ""
    tipo: str = "Receita"
    data_lancamento: str = datetime.now().strftime("%Y-%m-%d")
    
    # Filtros e Pesquisa
    pesquisa: str = ""
    filtro_status: str = "Todos"    
    filtro_tipo: str = "Todos"
    
    # Variáveis para Gestão de Dívidas (essenciais para o Raio-X)
    novo_credor: str = ""
    novo_valor_total: str = ""
    novo_total_parcelas: str = "1"
    novo_valor_parcela: str = ""
    novo_dia_vencimento: str = "15"
    novo_status: str = "Pendente"
    local_selecionado: str = ""
    
    id_selecionado: int = 0
    edit_credor: str = ""
    edit_valor_total: str = ""
    edit_total_parcelas: str = "1"
    edit_valor_parcela: str = ""
    edit_dia_vencimento: str = "15"
    edit_status: str = "Pendente"
    
    # ==========================================
    # SETTERS EXPLÍCITOS
    # ==========================================
    def set_escolha_perfil(self, valor: str) -> None:
        self.escolha_perfil = valor

    def set_algum_valor(self, valor: str):
        self.algum_valor = valor

    def set_data_aporte(self, valor: str):
        self.data_aporte = valor

    def set_valor_aporte(self, valor: str):
        self.valor_aporte = valor

    def set_descricao(self, valor: str):
        self.descricao = valor

    def set_valor(self, valor: str): 
        self.valor = valor

    def set_categoria(self, valor: str):
        self.categoria = valor

    def set_tipo(self, valor: str): 
        self.tipo = valor

    def set_data_lancamento(self, valor: str):
        self.data_lancamento = valor

    def set_pesquisa(self, valor: str):
        self.pesquisa = valor

    def set_filtro_status(self, valor: str):
        self.filtro_status = valor 

    def set_filtro_tipo(self, valor: str):
        self.filtro_tipo = valor

    def set_novo_credor(self, valor: str):
        self.novo_credor = valor

    def set_novo_valor_total(self, valor: str):
        self.novo_valor_total = valor

    def set_novo_total_parcelas(self, valor: str):
        self.novo_total_parcelas = valor

    def set_novo_valor_parcela(self, valor: str):
        self.novo_valor_parcela = valor

    def set_novo_dia_vencimento(self, valor: str):
        self.novo_dia_vencimento = valor

    def set_novo_status(self, valor: str):
        self.novo_status = valor

    def set_local_selecionado(self, valor: str):
        self.local_selecionado = valor

    def set_edit_credor(self, valor: str):
        self.edit_credor = valor

    def set_edit_valor_total(self, valor: str):
        self.edit_valor_total = valor

    def set_edit_total_parcelas(self, valor: str):
        self.edit_total_parcelas = valor

    def set_edit_valor_parcela(self, valor: str):
        self.edit_valor_parcela = valor

    def set_edit_dia_vencimento(self, valor: str):
        self.edit_dia_vencimento = valor

    def set_edit_status(self, valor: str):
        self.edit_status = valor

    # ==========================================
    # FUNÇÕES DE LANÇAMENTOS FINANCEIROS
    # ==========================================
    def cadastrar_lancamento(self):
        """Regista um novo movimento na base de dados."""
        if not self.descricao.strip():
            return rx.window_alert("Por favor, preencha a descrição.")
        if not self.valor:
            return rx.window_alert("Por favor, preencha o valor.")
        try:
            val = float(self.valor.replace(",", "."))
            data_reg = self.data_lancamento if self.data_lancamento else datetime.now().strftime("%Y-%m-%d")

            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            
            cursor.execute(
                """
                INSERT INTO lancamentos (data, tipo, categoria, descricao, valor)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (data_reg, self.tipo, self.categoria.strip(), self.descricao.strip(), val)
            )

            if self.tipo.strip().lower() in ["investimento", "investimentos"]:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS desafio_aportes (
                        id SERIAL PRIMARY KEY,
                        data TEXT NOT NULL,
                        valor NUMERIC(10,2) NOT NULL,
                        local_aplicacao TEXT NOT NULL
                    )
                """)
                try:
                    dt_obj = datetime.strptime(data_reg, "%Y-%m-%d")
                    data_formatada = dt_obj.strftime("%d/%m/%Y")
                except ValueError:
                    data_formatada = data_reg

                cursor.execute(
                    "INSERT INTO desafio_aportes (data, valor, local_aplicacao) VALUES (%s, %s, %s)",
                    (data_formatada, val, self.descricao.strip())
                )

            conexao.commit()
            cursor.close()
            conexao.close()

            self.descricao = ""
            self.valor = ""
            self.categoria = ""
            self.calcular_resumo_competencia()
            return rx.window_alert("Lançamento cadastrado com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao salvar lançamento: {e}")

    def excluir_lancamento(self, id_lancamento: int):
        """Remove um lançamento do banco de dados e recalcula o histórico."""
        try:
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM lancamentos WHERE id = %s", (int(id_lancamento),))
            conexao.commit()
            cursor.close()
            conexao.close()

            self.calcular_resumo_competencia()
            return rx.window_alert("Lançamento excluído com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao excluir lançamento: {e}")

    def alterar_tipo_lancamento(self, id_lancamento: int, novo_tipo: str):
        """Altera rapidamente o tipo do lançamento (ex: de Investimento para Despesa)."""
        try:
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            cursor.execute("UPDATE lancamentos SET tipo = %s WHERE id = %s", (novo_tipo, int(id_lancamento)))
            conexao.commit()
            cursor.close()
            conexao.close()

            self.calcular_resumo_competencia()
            return rx.window_alert(f"Tipo alterado para {novo_tipo} com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao alterar tipo: {e}")

    def selecionar_lancamento(self, id_str: str):
        try:
            self.id_selecionado = int(id_str)
            conexao = obter_conexao()
            df = pd.read_sql_query("SELECT * FROM lancamentos WHERE id = %s", conexao, params=(self.id_selecionado,))
            conexao.close()

            if not df.empty:
                row = df.iloc[0]
                self.data_lancamento = str(row["data"])
                self.tipo = str(row["tipo"])
                self.categoria = str(row["categoria"])
                self.descricao = str(row["descricao"])
                self.valor = str(row["valor"])
        except Exception as e:
            print(f"Erro ao selecionar lançamento: {e}")

    def salvar_alteracoes(self):
        if not self.id_selecionado:
            return rx.window_alert("Selecione um lançamento para editar.")
        try:
            val_limpo = abs(float(self.valor.replace(",", "."))) if self.valor else 0.0
            
            conexao = obter_conexao()
            cursor = conexao.cursor()
            cursor.execute(
                """
                UPDATE lancamentos 
                SET data = %s, tipo = %s, categoria = %s, descricao = %s, valor = %s 
                WHERE id = %s
                """,
                (self.data_lancamento.strip(), self.tipo.strip(), self.categoria.strip(), self.descricao.strip(), val_limpo, int(self.id_selecionado))
            )
            conexao.commit()
            cursor.close()
            conexao.close()

            self.id_selecionado = 0
            self.descricao = ""
            self.valor = ""
            self.categoria = ""
            
            self.calcular_resumo_competencia()
            return rx.window_alert("Lançamento atualizado com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao atualizar lançamento: {e}")

    @rx.var
    def lista_lancamentos(self) -> list[dict]:
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df = pd.read_sql_query("SELECT id, data, tipo, categoria, descricao, valor FROM lancamentos ORDER BY id DESC", conexao)
            conexao.close()
            
            if df.empty:
                return []

            return df.to_dict(orient="records")
        except Exception as e:
            print(f"Erro ao carregar lançamentos: {e}")
            return []

    # ==========================================
    # FUNÇÕES DE GESTÃO DE DÍVIDAS
    # ==========================================
    def cadastrar_divida(self):
        if not self.novo_credor.strip():
            return rx.window_alert("Por favor, preencha o nome do credor.")
        try:
            v_total = float(self.novo_valor_total.replace(",", "."))
            t_parc = int(self.novo_total_parcelas)
            v_parc = float(self.novo_valor_parcela.replace(",", ".")) if self.novo_valor_parcela else 0.0
            dia_v = int(self.novo_dia_vencimento)
            status_atual = self.novo_status if self.novo_status else "Pendente"

            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            cursor.execute(
                "INSERT INTO dividas (credor, valor_total, total_parcelas, valor_parcela, dia_vencimento, status) VALUES (%s, %s, %s, %s, %s, %s)",
                (self.novo_credor, v_total, t_parc, v_parc, dia_v, status_atual)
            )
            conexao.commit()
            cursor.close()
            conexao.close()

            self.novo_credor = ""
            self.novo_valor_total = ""
            self.novo_total_parcelas = "1"
            self.novo_valor_parcela = ""
            self.novo_dia_vencimento = "15"

            return rx.window_alert("Dívida cadastrada com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao salvar dívida: {e}")

    def selecionar_divida(self, id_str: str):
        if not id_str:
            self.id_selecionado = 0
            return
        try:
            # Tratamento robusto para extrair ID de strings formatadas
            if "|" in id_str:
                id_str = id_str.split("|")[0].replace("ID:", "").strip()
            elif "-" in id_str:
                id_str = id_str.split("-")[0].strip()
            
            self.id_selecionado = int(id_str)
            conexao = database.obter_conexao()
            df = pd.read_sql_query("SELECT * FROM dividas WHERE id = %s", conexao, params=(self.id_selecionado,))
            conexao.close()

            if not df.empty:
                row = df.iloc[0]
                self.edit_credor = str(row["credor"] or "")
                self.edit_valor_total = str(row["valor_total"] or "0.0")
                self.edit_total_parcelas = str(row["total_parcelas"] or "1")
                self.edit_valor_parcela = str(row["valor_parcela"] or "0.0")
                self.edit_dia_vencimento = str(row["dia_vencimento"] or "15")
                self.edit_status = str(row["status"] or "Pendente")
        except Exception as e:
            print(f"Erro ao selecionar dívida: {e}")

    dividas_opcoes: list[str] = []

    def carregar_dividas(self):
        try:
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            cursor.execute("SELECT id, credor FROM dividas ORDER BY id DESC")
            resultados = cursor.fetchall()
            cursor.close()
            conexao.close()
            
            self.dividas_opcoes = [f"{row[0]} - {row[1]}" for row in resultados]
        except Exception as e:
            print(f"Erro ao carregar dívidas: {e}")
            self.dividas_opcoes = []

    def salvar_edicao(self):
        if not self.id_selecionado:
            return rx.window_alert("Nenhuma dívida selecionada.")
        try:
            v_total = float(self.edit_valor_total.replace(",", "."))
            t_parc = int(self.edit_total_parcelas)
            v_parc = float(self.edit_valor_parcela.replace(",", ".")) if self.edit_valor_parcela else 0.0
            dia_v = int(self.edit_dia_vencimento)

            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            cursor.execute(
                """
                UPDATE dividas 
                SET credor = %s, valor_total = %s, total_parcelas = %s, valor_parcela = %s, dia_vencimento = %s, status = %s
                WHERE id = %s
                """,
                (self.edit_credor.strip(), v_total, t_parc, v_parc, dia_v, self.edit_status, self.id_selecionado)
            )
            conexao.commit()
            cursor.close()
            conexao.close()
            return rx.window_alert("Dívida atualizada com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao atualizar dívida: {e}")

    def excluir_divida(self):
        if not self.id_selecionado:
            return rx.window_alert("Nenhuma dívida selecionada.")
        try:
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM dividas WHERE id = %s", (self.id_selecionado,))
            conexao.commit()
            cursor.close()
            conexao.close()
            self.id_selecionado = 0
            return rx.window_alert("Dívida excluída com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao excluir: {e}")

    @rx.var
    def lista_resumo_dividas(self) -> list[str]:
        try:
            conexao = database.obter_conexao()
            df = pd.read_sql_query("SELECT id, credor FROM dividas ORDER BY id DESC", conexao)
            conexao.close()
            if df.empty:
                return []
            return [f"ID: {row['id']} | {row['credor']}" for _, row in df.iterrows()]
        except Exception:
            return []

    def set_competencia_selecionada(self, nova_competencia: str):
        self.competencia_selecionada = nova_competencia
        self.calcular_resumo_competencia()

    def calcular_resumo_competencia(self) -> None:
        """Calcula os totais da competência selecionada."""
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df = pd.read_sql_query("SELECT data, tipo, valor FROM lancamentos", conexao)
            conexao.close()

            if df.empty:
                self.fmt_entradas = "R$ 0,00"
                self.fmt_gastos = "R$ 0,00"
                self.fmt_aportes = "R$ 0,00"
                self.fmt_saldo_final = "R$ 0,00"
                self.fmt_saldo_anterior = "R$ 97,87"
                return

            df['data_limpa'] = df['data'].astype(str).str.strip()
            df['data_dt'] = pd.to_datetime(df['data_limpa'], dayfirst=True, errors='coerce')
            df['competencia'] = df['data_dt'].dt.strftime('%m/%Y')

            comp_sel = str(self.competencia_selecionada).strip()
            if len(comp_sel) < 7:
                comp_sel = "10/2026"

            df_comp = df[df['competencia'] == comp_sel]

            if df_comp.empty:
                self.fmt_entradas = "R$ 0,00"
                self.fmt_gastos = "R$ 0,00"
                self.fmt_aportes = "R$ 0,00"
                self.fmt_saldo_final = "R$ 0,00"
                self.fmt_saldo_anterior = "R$ 97,87"
                return

            df_comp['valor_num'] = pd.to_numeric(df_comp['valor'], errors='coerce').fillna(0.0)
            df_comp['tipo_norm'] = df_comp['tipo'].astype(str).str.strip().str.lower()

            is_receita = df_comp['tipo_norm'].isin(['receita', 'salario', 'salário'])
            is_investimento = df_comp['tipo_norm'].isin(['investimento', 'investimentos', 'aporte', 'aplicacao', 'aplicação'])
            is_gasto = ~(is_receita | is_investimento)

            total_ent = float(df_comp[is_receita]['valor_num'].sum())
            total_gas = float(df_comp[is_gasto]['valor_num'].sum())
            total_aportes = float(df_comp[is_investimento]['valor_num'].sum())
            
            self.fmt_entradas = f"R$ {total_ent:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.fmt_gastos = f"R$ {total_gas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.fmt_aportes = f"R$ {total_aportes:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            saldo_final = total_ent - total_gas
            self.fmt_saldo_final = f"R$ {saldo_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.fmt_saldo_anterior = "R$ 97,87"

        except Exception as e:
            print(f"Erro ao calcular resumo da competencia: {e}")
            self.fmt_entradas = "R$ 0,00"
            self.fmt_gastos = "R$ 0,00"
            self.fmt_aportes = "R$ 0,00"
            self.fmt_saldo_final = "R$ 0,00"
            self.fmt_saldo_anterior = "R$ 97,87"

    # =========================================================================
    # GESTÃO DO DESAFIO RESERVA E APORTES
    # =========================================================================
    escolha_perfil: str = "1 Plantão CPROEIS (R$ 532,00 / mês)"
    meses_totais: int = 12
    meta_manual: float = 532.00
    
    data_aporte: str = datetime.now().strftime("%d/%m/%Y")
    valor_aporte: float = 532.00
    local_selecionado: str = "Banco Itaú"
    local_outro: str = ""

    data_resgate: str = datetime.now().strftime("%d/%m/%Y")
    valor_resgate: float = 100.00
    local_origem_sel: str = "Banco Itaú"
    origem_personalizada: str = ""
    motivo_resgate: str = ""

    id_resgate_excluir: int = 0

    def garantir_tabelas(self):
        try:
            conexao = obter_conexao()
            cursor = conexao.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS desafio_aportes (
                    id SERIAL PRIMARY KEY,
                    data TEXT NOT NULL,
                    valor NUMERIC(10,2) NOT NULL,
                    local_aplicacao TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS desafio_resgates (
                    id SERIAL PRIMARY KEY,
                    data TEXT NOT NULL,
                    valor NUMERIC(10,2) NOT NULL,
                    local_origem TEXT NOT NULL,
                    motivo TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dividas (
                    id SERIAL PRIMARY KEY,
                    credor VARCHAR(255),
                    valor_total NUMERIC,
                    total_parcelas INTEGER,
                    valor_parcela NUMERIC,
                    dia_vencimento INTEGER,
                    status VARCHAR(50)
                );
            """)
            conexao.commit()
            cursor.close()
            conexao.close()
        except Exception as e:
            print(f"Erro ao garantir tabelas: {e}")

    @rx.var
    def meta_mensal_base(self) -> float:
        opcoes = {
            "Personalizado (Definir manual)": self.meta_manual,
            "1 Plantão CPROEIS (R$ 532,00 / mês)": 532.00,
            "Conservador (R$ 300,00 / mês)": 300.00,
            "Intermediário (R$ 800,00 / mês)": 800.00,
            "Agressivo (R$ 1.000,00 / mês)": 1000.00,
        }
        return opcoes.get(self.escolha_perfil, self.meta_manual)

    @rx.var
    def meta_total(self) -> float:
        return self.meta_mensal_base * self.meses_totais

    @rx.var
    def df_aportes(self) -> pd.DataFrame:
        self.garantir_tabelas()
        try:
            conexao = obter_conexao()
            df = pd.read_sql_query("SELECT id, data, valor, local_aplicacao FROM desafio_aportes ORDER BY id DESC", conexao)
            conexao.close()

            if not df.empty:
                df["valor_num"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
                return df
            
            conexao = obter_conexao()
            query = """
                SELECT id, data, valor, descricao AS local_aplicacao 
                FROM lancamentos 
                WHERE LOWER(tipo) IN ('investimento', 'investimentos')
                ORDER BY id DESC
            """
            df = pd.read_sql_query(query, conexao)
            conexao.close()

            if not df.empty:
                df["valor_num"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
                return df

            return pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao", "valor_num"])
        except Exception as e:
            print(f"Erro ao carregar df_aportes: {e}")
            return pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao", "valor_num"])

    @rx.var
    def df_resgates(self) -> pd.DataFrame:
        self.garantir_tabelas()
        try:
            conexao = obter_conexao()
            df = pd.read_sql_query("SELECT id, data, valor, local_origem, motivo FROM desafio_resgates ORDER BY id DESC", conexao)
            conexao.close()
            if not df.empty:
                df["valor_num"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
            return df
        except Exception:
            return pd.DataFrame(columns=["id", "data", "valor", "local_origem", "motivo", "valor_num"])

    @rx.var
    def total_aportado(self) -> float:
        df = self.df_aportes
        return float(df["valor_num"].sum()) if not df.empty and "valor_num" in df.columns else 0.0

    @rx.var
    def total_resgatado(self) -> float:
        df = self.df_resgates
        return float(df["valor_num"].sum()) if not df.empty and "valor_num" in df.columns else 0.0

    @rx.var
    def total_guardado(self) -> float:
        return self.total_aportado - self.total_resgatado

    @rx.var
    def progresso_perc(self) -> float:
        if self.meta_total > 0:
            return min(self.total_guardado / self.meta_total, 1.0)
        return 0.0

    def salvar_aporte(self):
        local_final = self.local_outro.strip() if self.local_selecionado == "Outro (Personalizado)" and self.local_outro.strip() else self.local_selecionado
        try:
            datetime.strptime(self.data_aporte.strip(), "%d/%m/%Y")
            conexao = obter_conexao()
            cursor = conexao.cursor()
            cursor.execute("INSERT INTO desafio_aportes (data, valor, local_aplicacao) VALUES (%s, %s, %s)", (self.data_aporte.strip(), self.valor_aporte, local_final))
            conexao.commit()
            cursor.close()
            conexao.close()
            return rx.window_alert("Aporte registrado com sucesso!")
        except ValueError:
            return rx.window_alert("Data inválida. Utilize o formato DD/MM/AAAA.")
        except Exception as e:
            return rx.window_alert(f"Erro ao salvar: {e}")

    def salvar_resgate(self):
        origem_final = self.origem_personalizada.strip() if self.local_origem_sel == "Outro (Personalizado)" and self.origem_personalizada.strip() else self.local_origem_sel
        try:
            datetime.strptime(self.data_resgate.strip(), "%d/%m/%Y")
            conexao = obter_conexao()
            cursor = conexao.cursor()
            cursor.execute("INSERT INTO desafio_resgates (data, valor, local_origem, motivo) VALUES (%s, %s, %s, %s)", (self.data_resgate.strip(), self.valor_resgate, origem_final, self.motivo_resgate.strip()))
            conexao.commit()
            cursor.close()
            conexao.close()
            return rx.window_alert("Resgate registrado com sucesso!")
        except ValueError:
            return rx.window_alert("Data inválida. Utilize o formato DD/MM/AAAA.")
        except Exception as e:
            return rx.window_alert(f"Erro ao salvar resgate: {e}")

    def excluir_aporte(self, id_lancamento: int):
        try:
            conexao = obter_conexao()
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM desafio_aportes WHERE id = %s", (int(id_lancamento),))
            conexao.commit()
            cursor.close()
            conexao.close()
            return rx.window_alert("Lançamento excluído com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao excluir: {e}")

    aportes: list[dict] = []
    
    def carregar_dados_investimentos(self):
        try:
            df = self.df_aportes
            self.aportes = df.to_dict("records") if not df.empty else []
            self.total_aportado = float(df["valor_num"].sum()) if not df.empty and "valor_num" in df.columns else 0.0
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")

class DiagnosticoState(rx.State):
    competencia_selecionada: str = datetime.now().strftime("%m/%Y")
    competencias_disponiveis: list[str] = [datetime.now().strftime("%m/%Y")]
    
    fmt_receitas: str = "R$ 0,00"
    fmt_despesas: str = "R$ 0,00"
    fmt_saldo: str = "R$ 0,00"
    status_saude: str = "Normal"

    def set_competencia_selecionada(self, valor: str):
        self.competencia_selecionada = valor

    def carregar_dados(self):
        pass