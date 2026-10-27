import reflex as rx
import pandas as pd
import database
from datetime import datetime
from database import obter_conexao

class FinanceState(rx.State):
    # Competência e Totais do Dashboard
    competencia_selecionada: str = datetime.now().strftime("%m/%Y")
    fmt_saldo_anterior: str = "R$ 0,00"
    fmt_entradas: str = "R$ 0,00"
    fmt_gastos: str = "R$ 0,00"
    fmt_aportes: str = "R$ 0,00"
    fmt_saldo_final: str = "R$ 0,00"
    
    # Gatilho para forçar a atualização imediata das tabelas
    refresh_trigger: int = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        database.inicializar_banco()
        self.garantir_tabelas()
        self.corrigir_tipos_resgates_automatico()
        self.calcular_resumo_competencia()

    def corrigir_tipos_resgates_automatico(self):
        """Corrige automaticamente qualquer resgate que tenha ficado com tipo incorreto na tabela de lançamentos."""
        try:
            conexao = obter_conexao()
            cursor = conexao.cursor()
            cursor.execute("""
                UPDATE lancamentos 
                SET tipo = 'Resgate' 
                WHERE LOWER(categoria) = 'resgate' AND LOWER(tipo) != 'resgate';
            """)
            conexao.commit()
            cursor.close()
            conexao.close()
        except Exception as e:
            print(f"Erro ao corrigir tipos de resgates: {e}")

    def limpar_resgates_duplicados(self):
        """Remove automaticamente lançamentos duplicados de resgate para corrigir o saldo."""
        try:
            conexao = obter_conexao()
            cursor = conexao.cursor()
            
            cursor.execute("""
                DELETE FROM lancamentos 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM lancamentos 
                    WHERE LOWER(categoria) = 'resgate' 
                    GROUP BY data, valor, descricao
                ) 
                AND LOWER(categoria) = 'resgate';
            """)
            
            conexao.commit()
            cursor.close()
            conexao.close()
        except Exception as e:
            print(f"Erro ao limpar resgates duplicados: {e}")
    
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

    # --- CAMPOS DE RENDIMENTOS ---
    data_rendimento: str = datetime.now().strftime("%d/%m/%Y")
    valor_rendimento: str = ""
    local_rendimento: str = "Banco Itaú"

    def set_data_rendimento(self, valor: str): self.data_rendimento = valor
    def set_valor_rendimento(self, valor: str): self.valor_rendimento = valor
    def set_local_rendimento(self, valor: str): self.local_rendimento = valor

    def salvar_rendimento(self):
        if not self.valor_rendimento:
            return rx.window_alert("Por favor, preencha o valor do rendimento.")
        try:
            val = float(self.valor_rendimento.replace(",", "."))
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS desafio_rendimentos (
                    id SERIAL PRIMARY KEY,
                    data TEXT NOT NULL,
                    valor NUMERIC(10,2) NOT NULL,
                    local_aplicacao TEXT NOT NULL
                )
            """)
            
            cursor.execute(
                "INSERT INTO desafio_rendimentos (data, valor, local_aplicacao) VALUES (%s, %s, %s)",
                (self.data_rendimento.strip(), val, self.local_rendimento)
            )
            conexao.commit()
            cursor.close()
            conexao.close()

            self.valor_rendimento = ""
            self.refresh_trigger += 1
            self.calcular_resumo_competencia()
            return rx.window_alert("Rendimento registrado com sucesso!")
        except ValueError:
            return rx.window_alert("Data inválida. Utilize o formato DD/MM/AAAA.")
        except Exception as e:
            return rx.window_alert(f"Erro ao salvar rendimento: {e}")
    
    # SETTERS EXPLÍCITOS
    def set_escolha_perfil(self, valor: str): self.escolha_perfil = valor
    def set_algum_valor(self, valor: str): self.algum_valor = valor
    def set_data_aporte(self, valor: str): self.data_aporte = valor
    def set_valor_aporte(self, valor: str): self.valor_aporte = valor
    def set_descricao(self, valor: str): self.descricao = valor
    def set_valor(self, valor: str): self.valor = valor
    def set_categoria(self, valor: str): self.categoria = valor
    def set_tipo(self, valor: str): self.tipo = valor
    def set_data_lancamento(self, valor: str): self.data_lancamento = valor
    def set_pesquisa(self, valor: str): self.pesquisa = valor
    def set_filtro_status(self, valor: str): self.filtro_status = valor 
    def set_filtro_tipo(self, valor: str): self.filtro_tipo = valor
    def set_novo_credor(self, valor: str): self.novo_credor = valor
    def set_novo_valor_total(self, valor: str): self.novo_valor_total = valor
    def set_novo_total_parcelas(self, valor: str): self.novo_total_parcelas = valor
    def set_novo_valor_parcela(self, valor: str): self.novo_valor_parcela = valor
    def set_novo_dia_vencimento(self, valor: str): self.novo_dia_vencimento = valor
    def set_novo_status(self, valor: str): self.novo_status = valor
    def set_local_selecionado(self, valor: str): self.local_selecionado = valor
    def set_edit_credor(self, valor: str): self.edit_credor = valor
    def set_edit_valor_total(self, valor: str): self.edit_valor_total = valor
    def set_edit_total_parcelas(self, valor: str): self.edit_total_parcelas = valor
    def set_edit_valor_parcela(self, valor: str): self.edit_valor_parcela = valor
    def set_edit_dia_vencimento(self, valor: str): self.edit_dia_vencimento = valor
    def set_edit_status(self, valor: str): self.edit_status = valor

    # LANÇAMENTOS
    def cadastrar_lancamento(self):
        if not self.descricao.strip():
            return rx.window_alert("Por favor, preencha a descrição.")
        if not self.valor:
            return rx.window_alert("Por favor, preencha o valor.")
        try:
            val = float(self.valor.replace(",", "."))
            
            data_raw = self.data_lancamento.strip() if self.data_lancamento else datetime.now().strftime("%Y-%m-%d")
            dt_obj = pd.to_datetime(data_raw, errors="coerce")
            data_reg = dt_obj.strftime("%Y-%m-%d") if pd.notna(dt_obj) else data_raw

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
                cursor.execute(
                    "INSERT INTO desafio_aportes (data, valor, local_aplicacao) VALUES (%s, %s, %s)",
                    (data_reg, val, self.descricao.strip())
                )

            conexao.commit()
            cursor.close()
            conexao.close()

            self.descricao = ""
            self.valor = ""
            self.categoria = ""
            self.refresh_trigger += 1
            self.calcular_resumo_competencia()
            return rx.window_alert("Lançamento cadastrado com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao salvar lançamento: {e}")

    def excluir_lancamento(self, id_lancamento: int):
        try:
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM lancamentos WHERE id = %s", (int(id_lancamento),))
            conexao.commit()
            cursor.close()
            conexao.close()

            self.refresh_trigger += 1
            self.calcular_resumo_competencia()
            return rx.window_alert("Lançamento excluído com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao excluir lançamento: {e}")

    def alterar_tipo_lancamento(self, id_lancamento: int, novo_tipo: str):
        try:
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            cursor.execute("UPDATE lancamentos SET tipo = %s WHERE id = %s", (novo_tipo, int(id_lancamento)))
            conexao.commit()
            cursor.close()
            conexao.close()

            self.refresh_trigger += 1
            self.calcular_resumo_competencia()
            return rx.window_alert(f"Tipo alterado para {novo_tipo} com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao alterar tipo: {e}")

    # =========================================================================
    # LISTAGEM DE LANÇAMENTOS UNIFICADA
    # =========================================================================
    @rx.var
    def lista_lancamentos(self) -> list[dict]:
        _ = self.refresh_trigger
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df = pd.read_sql_query("SELECT id, data, tipo, categoria, descricao, valor FROM lancamentos ORDER BY id DESC", conexao)
            conexao.close()

            if df.empty:
                return []
            
            resultado = []
            for _, row in df.iterrows():
                desc = row["descricao"]
                desc_str = "" if pd.isna(desc) else str(desc)
                val_float = float(row['valor'] or 0.0)
                val_fmt = f"R$ {val_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                
                data_raw = str(row["data"])
                dt_obj = pd.to_datetime(data_raw, errors="coerce")
                data_fmt = dt_obj.strftime("%d/%m/%Y") if pd.notna(dt_obj) else data_raw

                resultado.append({
                    "id": int(row["id"]),
                    "data": data_fmt,
                    "tipo": str(row["tipo"]),
                    "categoria": str(row["categoria"]),
                    "descricao": desc_str,
                    "valor": val_fmt,
                })
            return resultado
        except Exception as e:
            print(f"Erro ao carregar lista unificada: {e}")
            return []

    @rx.var
    def lista_lancamentos_mes(self) -> list[dict]:
        return self.lista_lancamentos

    # DÍVIDAS
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
            self.refresh_trigger += 1

            return rx.window_alert("Dívida cadastrada com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao salvar dívida: {e}")

    def selecionar_divida(self, id_str: str):
        if not id_str:
            self.id_selecionado = 0
            return
        try:
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
            self.refresh_trigger += 1
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
            self.refresh_trigger += 1
            return rx.window_alert("Dívida excluída com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao excluir: {e}")

    @rx.var
    def lista_resumo_dividas(self) -> list[str]:
        _ = self.refresh_trigger
        try:
            conexao = database.obter_conexao()
            df = pd.read_sql_query("SELECT id, credor FROM dividas ORDER BY id DESC", conexao)
            conexao.close()
            if df.empty:
                return []
            return [f"ID: {row['id']} | {row['credor']}" for _, row in df.iterrows()]
        except Exception:
            return []

    # ==========================================
    # MOTOR DE CÁLCULO DE COMPETÊNCIA
    # ==========================================
    def set_competencia_selecionada(self, nova_competencia: str):
        self.competencia_selecionada = nova_competencia
        self.calcular_resumo_competencia()

    def calcular_resumo_competencia(self) -> None:
        """Calcula receitas, despesas, aportes e resgates unificando perfeitamente a liquidez."""
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()

            try:
                df_lancamentos = pd.read_sql_query("SELECT * FROM lancamentos", conexao)
            except Exception:
                df_lancamentos = pd.DataFrame(columns=["data", "tipo", "categoria", "descricao", "valor"])

            try:
                df_resgates = pd.read_sql_query("SELECT id, data, valor, local_origem, motivo FROM desafio_resgates", conexao)
            except Exception:
                df_resgates = pd.DataFrame(columns=["id", "data", "valor", "local_origem", "motivo"])

            conexao.close()

            def extrair_comp(data_val):
                if pd.isna(data_val) or data_val is None:
                    return "Indefinido", "9999-99"
                try:
                    if isinstance(data_val, (pd.Timestamp, datetime)):
                        return data_val.strftime("%m/%Y"), data_val.strftime("%Y-%m")
                    data_str = str(data_val).strip()
                    dt = pd.to_datetime(data_str, format="%Y-%m-%d", errors="coerce")
                    if pd.isna(dt):
                        dt = pd.to_datetime(data_str, format="%d/%m/%Y", errors="coerce")
                    if pd.isna(dt):
                        dt = pd.to_datetime(data_str, errors="coerce")
                    if pd.notna(dt):
                        return dt.strftime("%m/%Y"), dt.strftime("%Y-%m")
                except Exception:
                    pass
                return "Indefinido", "9999-99"

            if not df_lancamentos.empty and "valor" in df_lancamentos.columns:
                df_lancamentos["valor"] = pd.to_numeric(df_lancamentos["valor"], errors="coerce").fillna(0.0)
                df_lancamentos["tipo_clean"] = df_lancamentos["tipo"].astype(str).str.strip().str.lower()
                df_lancamentos["cat_clean"] = df_lancamentos["categoria"].astype(str).str.strip().str.lower()
                res_lanc = df_lancamentos["data"].apply(extrair_comp)
                df_lancamentos["competencia"] = [x[0] for x in res_lanc]
            else:
                df_lancamentos["tipo_clean"] = ""
                df_lancamentos["cat_clean"] = ""
                df_lancamentos["competencia"] = "Indefinido"

            comp_sel = str(self.competencia_selecionada).strip()
            df_lanc_mes = df_lancamentos[df_lancamentos["competencia"] == comp_sel] if not df_lancamentos.empty else pd.DataFrame()

            total_receitas_mes = (
                df_lanc_mes[
                    df_lanc_mes["tipo_clean"].isin(["receita", "crédito", "credito", "entrada"]) 
                    & (~df_lanc_mes["cat_clean"].isin(["resgate", "resgates"]))
                    & (~df_lanc_mes["tipo_clean"].isin(["resgate", "resgates"]))
                    & (~df_lanc_mes["tipo_clean"].isin(["investimento", "investimentos", "aporte", "aportes"]))
                ]["valor"].sum()
                if not df_lanc_mes.empty else 0.0
            )

            total_gastos_mes = (
                df_lanc_mes[
                    df_lanc_mes["tipo_clean"].isin(["despesa", "débito", "debito", "saida"])
                    & (~df_lanc_mes["tipo_clean"].isin(["investimento", "investimentos", "aporte", "aportes"]))
                ]["valor"].sum()
                if not df_lanc_mes.empty else 0.0
            )

            total_aportes_mes = (
                df_lanc_mes[df_lanc_mes["tipo_clean"].isin(["investimento", "investimentos", "aporte", "aportes"])]["valor"].sum()
                if not df_lanc_mes.empty else 0.0
            )

            total_resgates_mes = (
                df_lanc_mes[
                    df_lanc_mes["tipo_clean"].isin(["resgate", "resgates"]) 
                    | df_lanc_mes["cat_clean"].isin(["resgate", "resgates"])
                ]["valor"].sum()
                if not df_lanc_mes.empty else 0.0
            )

            if total_resgates_mes == 0.0 and not df_resgates.empty:
                df_resgates["valor_num"] = pd.to_numeric(df_resgates["valor"], errors="coerce").fillna(0.0)
                res_resg = df_resgates["data"].apply(extrair_comp)
                df_resgates["competencia"] = [x[0] for x in res_resg]
                total_resgates_mes = df_resgates[df_resgates["competencia"] == comp_sel]["valor_num"].sum()

            saldo_remanescente_anterior = 0.0
            saldo_mes = saldo_remanescente_anterior + total_receitas_mes + total_resgates_mes - total_gastos_mes - total_aportes_mes

            def fmt_m(val):
                return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            self.fmt_saldo_anterior = fmt_m(saldo_remanescente_anterior)
            self.fmt_entradas = fmt_m(total_receitas_mes)
            self.fmt_gastos = fmt_m(total_gastos_mes)
            self.fmt_aportes = fmt_m(total_aportes_mes)
            self.fmt_saldo_final = fmt_m(saldo_mes)

        except Exception as e:
            print(f"Erro ao calcular resumo da competencia: {e}")
            self.fmt_entradas = "R$ 0,00"
            self.fmt_gastos = "R$ 0,00"
            self.fmt_aportes = "R$ 0,00"
            self.fmt_saldo_final = "R$ 0,00"
            self.fmt_saldo_anterior = "R$ 0,00"

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
            try:
                df_total = pd.read_sql_query("SELECT id, data, valor, local_aplicacao FROM desafio_aportes", conexao)
            except:
                df_total = pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao"])
            conexao.close()

            if not df_total.empty:
                df_total["valor_num"] = pd.to_numeric(df_total["valor"], errors="coerce").fillna(0.0)
                
                def parse_dt(d):
                    d_str = str(d).strip()
                    dt = pd.to_datetime(d_str, format="%Y-%m-%d", errors="coerce")
                    if pd.isna(dt):
                        dt = pd.to_datetime(d_str, format="%d/%m/%Y", errors="coerce")
                    if pd.isna(dt):
                        dt = pd.to_datetime(d_str, errors="coerce")
                    return dt

                df_total["data_dt"] = df_total["data"].apply(parse_dt)
                df_total = df_total.sort_values(by="data_dt", ascending=False).drop(columns=["data_dt"])
                return df_total

            return pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao", "valor_num"])
        except Exception as e:
            print(f"Erro ao carregar df_aportes no desafio: {e}")
            return pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao", "valor_num"])

    @rx.var
    def total_aportado_bruto(self) -> float:
        total_geral = 0.0
        try:
            conexao = obter_conexao()
            try:
                df_a = pd.read_sql_query("SELECT SUM(valor) as total FROM desafio_aportes", conexao)
                total_geral += float(df_a["total"].iloc[0]) if not df_a.empty and pd.notna(df_a["total"].iloc[0]) else 0.0
            except:
                pass

            try:
                df_r = pd.read_sql_query("SELECT SUM(valor) as total FROM desafio_rendimentos", conexao)
                total_geral += float(df_r["total"].iloc[0]) if not df_r.empty and pd.notna(df_r["total"].iloc[0]) else 0.0
            except:
                pass
            conexao.close()
        except Exception as e:
            print(f"Erro ao calcular total aportado bruto: {e}")
        return total_geral
    
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
    def total_resgatado(self) -> float:
        df = self.df_resgates
        return float(df["valor_num"].sum()) if not df.empty and "valor_num" in df.columns else 0.0

    @rx.var
    def total_aportado(self) -> float:
        return max(0.0, self.total_aportado_bruto - self.total_resgatado)

    @rx.var
    def total_guardado(self) -> float:
        return self.total_aportado

    @rx.var
    def progresso_perc(self) -> float:
        if self.meta_total > 0:
            return min(self.total_guardado / self.meta_total, 1.0)
        return 0.0

    @rx.var
    def fmt_total_aportado_bruto_com_rendimentos(self) -> str:
        val = self.total_aportado_bruto
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def fmt_total_aportado_liquido(self) -> str:
        val = self.total_aportado
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def lista_investimentos_exibicao(self) -> list[dict]:
        df = self.df_aportes
        if df.empty: return []
        res = []
        for _, row in df.iterrows():
            val = float(row["valor"] or 0)
            res.append({
                "id": int(row["id"]),
                "data": str(row["data"]),
                "local_aplicacao": str(row["local_aplicacao"]),
                "valor": f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            })
        return res
    
    def salvar_aporte(self):
        local_final = self.local_outro.strip() if self.local_selecionado == "Outro (Personalizado)" and self.local_outro.strip() else self.local_selecionado
        try:
            dt_obj = pd.to_datetime(self.data_aporte.strip(), errors="coerce")
            if pd.isna(dt_obj):
                raise ValueError
            data_reg = dt_obj.strftime("%Y-%m-%d")

            conexao = obter_conexao()
            cursor = conexao.cursor()
            cursor.execute("INSERT INTO desafio_aportes (data, valor, local_aplicacao) VALUES (%s, %s, %s)", (data_reg, self.valor_aporte, local_final))
            conexao.commit()
            cursor.close()
            conexao.close()
            self.refresh_trigger += 1
            self.calcular_resumo_competencia()
            return rx.window_alert("Aporte registrado com sucesso!")
        except ValueError:
            return rx.window_alert("Data inválida. Utilize o formato DD/MM/AAAA.")
        except Exception as e:
            return rx.window_alert(f"Erro ao salvar: {e}")

    def salvar_resgate(self):
        origem_final = self.origem_personalizada.strip() if self.local_origem_sel == "Outro (Personalizado)" and self.origem_personalizada.strip() else self.local_origem_sel
        try:
            dt_obj = pd.to_datetime(self.data_resgate.strip(), errors="coerce")
            if pd.isna(dt_obj):
                raise ValueError
            data_reg = dt_obj.strftime("%Y-%m-%d")
            val = float(self.valor_resgate)
            
            conexao = obter_conexao()
            cursor = conexao.cursor()
            
            cursor.execute(
                "INSERT INTO desafio_resgates (data, valor, local_origem, motivo) VALUES (%s, %s, %s, %s)",
                (data_reg, val, origem_final, self.motivo_resgate.strip())
            )
            
            cursor.execute(
                """
                INSERT INTO lancamentos (data, tipo, categoria, descricao, valor)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (data_reg, "Investimento", "Resgate", f"Resgate {origem_final} - {self.motivo_resgate.strip()}", val)
            )

            conexao.commit()
            cursor.close()
            conexao.close()
            
            self.refresh_trigger += 1
            self.calcular_resumo_competencia()
            return rx.window_alert("Resgate registrado e integrado ao caixa com sucesso!")
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
            self.refresh_trigger += 1
            self.calcular_resumo_competencia()
            return rx.window_alert("Lançamento excluído com sucesso!")
        except Exception as e:
            return rx.window_alert(f"Erro ao excluir: {e}")

    aportes: list[dict] = []
    
    def carregar_dados_investimentos(self):
        try:
            df = self.df_aportes
            self.aportes = df.to_dict("records") if not df.empty else []
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