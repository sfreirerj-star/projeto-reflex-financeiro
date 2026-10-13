import reflex as rx
import pandas as pd
import database
from datetime import datetime

class DesafioState(rx.State):
    """Estado completo para gerir os aportes, resgates, metas e simuladores do Desafio."""
    
    # --- CONFIGURAÇÃO DE META ---
    escolha_perfil_meta: str = "1 Plantão CPROEIS (R$ 532,00 / mês)"
    prazo_meses: int = 12
    valor_manual_meta: str = "532.00"

    # --- CAMPOS DE APORTE ---
    novo_data_deposito: str = datetime.now().strftime("%d/%m/%Y")
    novo_valor_depositado: str = "532.00"
    novo_local_aplicacao: str = "Banco Itaú"
    novo_outro_local: str = ""

    # --- CAMPOS DE RESGATE ---
    resg_data: str = datetime.now().strftime("%d/%m/%Y")
    resg_valor: str = "100.00"
    resg_origem: str = "Banco Itaú"
    resg_outro_origem: str = ""
    resg_motivo: str = ""

    # --- SIMULADOR DE ANTECIPAÇÃO ---
    sim_meta_alvo: str = "10000.00"
    sim_aporte_mensal: str = "532.00"
    sim_ganho_extra: str = "532.00"
    sim_qtd_extras: int = 1

    # --- SETTERS EXPLÍCITOS COM TRATAMENTO DE STRING ---
    def set_escolha_perfil_meta(self, v: str):
        self.escolha_perfil_meta = v
    
    def set_prazo_meses(self, v: str):
        try:
            self.prazo_meses = int(v) if v else 12
        except ValueError:
            self.prazo_meses = 12

    def set_valor_manual_meta(self, v: str):
        self.valor_manual_meta = v

    def set_novo_data_deposito(self, v: str):
        self.novo_data_deposito = v
        
    def set_novo_valor_depositado(self, v: str):
        self.novo_valor_depositado = v
        
    def set_novo_local_aplicacao(self, v: str):
        self.novo_local_aplicacao = v
        
    def set_novo_outro_local(self, v: str):
        self.novo_outro_local = v

    def set_resg_data(self, v: str):
        self.resg_data = v
        
    def set_resg_valor(self, v: str):
        self.resg_valor = v
        
    def set_resg_origem(self, v: str):
        self.resg_origem = v
        
    def set_resg_outro_origem(self, v: str):
        self.resg_outro_origem = v
        
    def set_resg_motivo(self, v: str):
        self.resg_motivo = v

    def set_sim_meta_alvo(self, v: str):
        self.sim_meta_alvo = v
        
    def set_sim_aporte_mensal(self, v: str):
        self.sim_aporte_mensal = v
        
    def set_sim_ganho_extra(self, v: str):
        self.sim_ganho_extra = v
    
    def set_sim_qtd_extras(self, v: str):
        try:
            self.sim_qtd_extras = int(v) if v else 1
        except ValueError:
            self.sim_qtd_extras = 1

    # --- CONSULTAS AO BANCO ---
    @rx.var
    def df_aportes(self) -> pd.DataFrame:
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            
            # Garantir tabelas
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
            conexao.commit()
            cursor.close()

            # Busca aportes registrados na tabela especifica do desafio
            df_desafio = pd.read_sql_query(
                "SELECT id, data, valor, local_aplicacao FROM desafio_aportes", conexao
            )

            # Busca aportes/investimentos da tabela geral de lançamentos do sistema
            df_geral = pd.read_sql_query(
                "SELECT id, data, valor, categoria AS local_aplicacao FROM lancamentos WHERE tipo IN ('Aporte', 'Investimento')",
                conexao
            )

            conexao.close()

            # Une ambos os DataFrames para contabilizar todos os aportes
            df_total = pd.concat([df_desafio, df_geral], ignore_index=True)
            if not df_total.empty:
                df_total = df_total.sort_values(by="id", ascending=False)

            return df_total
        except Exception:
            return pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao"])

    @rx.var
    def df_resgates(self) -> pd.DataFrame:
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df = pd.read_sql_query("SELECT id, data, valor, local_origem, motivo FROM desafio_resgates ORDER BY id DESC", conexao)
            conexao.close()
            return df
        except Exception:
            return pd.DataFrame(columns=["id", "data", "valor", "local_origem", "motivo"])

    # --- CÁLCULOS E PROPRIEDADES ---
    @rx.var
    def total_aportado(self) -> float:
        df = self.df_aportes
        if df.empty or "valor" not in df.columns:
            return 0.0
        return float(pd.to_numeric(df["valor"], errors="coerce").fillna(0.0).sum())

    @rx.var
    def total_resgatado(self) -> float:
        df = self.df_resgates
        if df.empty or "valor" not in df.columns:
            return 0.0
        return float(pd.to_numeric(df["valor"], errors="coerce").fillna(0.0).sum())

    @rx.var
    def total_guardado(self) -> float:
        return self.total_aportado - self.total_resgatado

    @rx.var
    def meta_mensal_base(self) -> float:
        if self.escolha_perfil_meta == "Personalizado (Definir manual)":
            try: return float(self.valor_manual_meta)
            except: return 532.00
        elif "CPROEIS" in self.escolha_perfil_meta: return 532.00
        elif "Conservador" in self.escolha_perfil_meta: return 300.00
        elif "Intermediário" in self.escolha_perfil_meta: return 800.00
        elif "Agressivo" in self.escolha_perfil_meta: return 1000.00
        return 532.00

    @rx.var
    def meta_total(self) -> float:
        return self.meta_mensal_base * int(self.prazo_meses or 12)

    @rx.var
    def progresso_perc(self) -> float:
        mt = self.meta_total
        if mt <= 0: return 0.0
        return min(self.total_guardado / mt, 1.0)

    @rx.var
    def progresso_perc_fmt(self) -> str:
        return f"Progresso Atual do Desafio: {self.progresso_perc * 100:.1f}% alcançado"

    # --- FORMATAÇÃO MONETÁRIA ---
    @rx.var
    def fmt_meta_total(self) -> str:
        return f"R$ {self.meta_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def fmt_total_aportado(self) -> str:
        return f"R$ {self.total_aportado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def fmt_total_resgatado(self) -> str:
        return f"R$ {self.total_resgatado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def fmt_total_guardado(self) -> str:
        return f"R$ {self.total_guardado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # --- TABELAS PARA A TELA ---
    @rx.var
    def lista_aportes_exibicao(self) -> list[dict]:
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

    @rx.var
    def lista_resgates_exibicao(self) -> list[dict]:
        df = self.df_resgates
        if df.empty: return []
        res = []
        for _, row in df.iterrows():
            val = float(row["valor"] or 0)
            res.append({
                "id": int(row["id"]),
                "data": str(row["data"]),
                "local_origem": str(row["local_origem"]),
                "valor": f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "motivo": str(row["motivo"] or ""),
            })
        return res

    # --- SIMULADOR DE METAS CÁLCULOS ---
    @rx.var
    def sim_meses_sem_extra(self) -> str:
        try:
            m_alvo = float(self.sim_meta_alvo)
            ap_m = float(self.sim_aporte_mensal)
            falta = max(0.0, m_alvo - self.total_guardado)
            if ap_m <= 0: return "0.0 meses"
            return f"{falta / ap_m:.1f} meses"
        except: return "0.0 meses"

    @rx.var
    def sim_meses_com_extra(self) -> str:
        try:
            m_alvo = float(self.sim_meta_alvo)
            ap_m = float(self.sim_aporte_mensal)
            g_extra = float(self.sim_ganho_extra) * self.sim_qtd_extras
            total_mensal = ap_m + g_extra
            falta = max(0.0, m_alvo - self.total_guardado)
            if total_mensal <= 0: return "0.0 meses"
            return f"{falta / total_mensal:.1f} meses"
        except: return "0.0 meses"

    # --- AÇÕES ---
    def salvar_aporte(self):
        local = self.novo_local_aplicacao
        if local == "Outro (Personalizado)":
            local = self.novo_outro_local.strip() if self.novo_outro_local.strip() else "Outro"
        try:
            val = float(self.novo_valor_depositado)
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            cursor.execute(
                "INSERT INTO desafio_aportes (data, valor, local_aplicacao) VALUES (%s, %s, %s)",
                (self.novo_data_deposito.strip(), val, local)
            )
            conexao.commit()
            cursor.close()
            conexao.close()
            self.novo_valor_depositado = "532.00"
        except Exception: pass

    def salvar_resgate(self):
        origem = self.resg_origem
        if origem == "Outro (Personalizado)":
            origem = self.resg_outro_origem.strip() if self.resg_outro_origem.strip() else "Outro"
        try:
            val = float(self.resg_valor)
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            cursor.execute(
                "INSERT INTO desafio_resgates (data, valor, local_origem, motivo) VALUES (%s, %s, %s, %s)",
                (self.resg_data.strip(), val, origem, self.resg_motivo.strip())
            )
            conexao.commit()
            cursor.close()
            conexao.close()
            self.resg_valor = "100.00"
            self.resg_motivo = ""
        except Exception: pass


@rx.page(route="/desafio", title="Desafio Reserva & Simulador")
def pagina_desafio() -> rx.Component:
    from .navegacao import barra_navegacao

    locais_opcoes = [
        "Banco Itaú",
        "Nomad (Investimentos em Dólar)",
        "Sofisa Direto (CDB 105% CDI)",
        "Banco Inter (CDB Liquidez Diária)",
        "Nubank (Caixinha / RDB 100% CDI)",
        "Tesouro Selic (Tesouro Direto)",
        "Outro (Personalizado)",
    ]

    perfis_opcoes = [
        "Personalizado (Definir manual)",
        "1 Plantão CPROEIS (R$ 532,00 / mês)",
        "Conservador (R$ 300,00 / mês)",
        "Intermediário (R$ 800,00 / mês)",
        "Agressivo (R$ 1.000,00 / mês)",
    ]

    return rx.vstack(
        barra_navegacao(),
        rx.container(
            rx.vstack(
                rx.heading("💰 Controle Financeiro — Painel do Marcelo", font_size="1.5rem", color="#1e293b", margin_top="15px"),
                rx.heading("🎯 Desafio Personalizado & Simulador de Antecipação", font_size="1.2rem", color="#334155"),
                rx.text("Controle seus aportes mensais, gerencie resgates, diversifique suas instituições financeiras e simule o impacto de ganhos extras nas suas metas.", color="#64748b", font_size="0.9rem", mb="4"),
                rx.divider(mb="4"),

                # --- ABAS DA PÁGINA ---
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("🎯 Meu Desafio & Aportes", value="aba_desafio"),
                        rx.tabs.trigger("💸 Módulo de Resgates", value="aba_resgates"),
                        rx.tabs.trigger("🎯 Simulador de Antecipação", value="aba_simulador"),
                        rx.tabs.trigger("📈 Consultoria Diária (Moderado)", value="aba_consultoria"),
                    ),

                    # ==================== ABA 1: DESAFIO & APORTES ====================
                    rx.tabs.content(
                        rx.vstack(
                            # Configuração de Meta
                            rx.accordion.root(
                                rx.accordion.item(
                                    header="⚙️ Configurar / Selecionar Meta Mensal (Inclui CPROEIS)",
                                    content=rx.vstack(
                                        rx.grid(
                                            rx.vstack(
                                                rx.text("Escolha o Perfil / Valor Mensal", size="2", weight="bold"),
                                                rx.select(perfis_opcoes, value=DesafioState.escolha_perfil_meta, on_change=DesafioState.set_escolha_perfil_meta, width="100%"),
                                                spacing="1"
                                            ),
                                            rx.vstack(
                                                rx.text("Prazo do Desafio (Meses)", size="2", weight="bold"),
                                                rx.input(value=DesafioState.prazo_meses, on_change=DesafioState.set_prazo_meses, type="number", width="100%"),
                                                spacing="1"
                                            ),
                                            columns={"base": "1", "md": "2"}, gap="4", width="100%", mb="3"
                                        ),
                                        rx.cond(
                                            DesafioState.escolha_perfil_meta == "Personalizado (Definir manual)",
                                            rx.vstack(
                                                rx.text("Valor Desejado por Mês (R$)", size="2", weight="bold"),
                                                rx.input(value=DesafioState.valor_manual_meta, on_change=DesafioState.set_valor_manual_meta, width="100%"),
                                                spacing="1", width="100%", mb="3"
                                            )
                                        ),
                                        width="100%", padding="10px"
                                    ),
                                ),
                                collapsible=True, width="100%", mb="4"
                            ),

                            # Cards de Indicadores
                            rx.flex(
                                rx.box(
                                    rx.text("Meta Total Calculada", size="2", color="gray"),
                                    rx.heading(DesafioState.fmt_meta_total, size="5", color="#2563eb"),
                                    padding="14px", border_radius="8px", border="1px solid #e2e8f0", bg="white", width=["100%", "220px"], flex_grow="1"
                                ),
                                rx.box(
                                    rx.text("Total Aportado", size="2", color="gray"),
                                    rx.heading(DesafioState.fmt_total_aportado, size="5", color="#16a34a"),
                                    padding="14px", border_radius="8px", border="1px solid #e2e8f0", bg="white", width=["100%", "220px"], flex_grow="1"
                                ),
                                rx.box(
                                    rx.text("Total Resgatado", size="2", color="gray"),
                                    rx.heading(DesafioState.fmt_total_resgatado, size="5", color="#dc2626"),
                                    padding="14px", border_radius="8px", border="1px solid #e2e8f0", bg="white", width=["100%", "220px"], flex_grow="1"
                                ),
                                rx.box(
                                    rx.text("Patrimônio Líquido Guardado", size="2", color="gray"),
                                    rx.heading(DesafioState.fmt_total_guardado, size="5", color="#7c3aed"),
                                    padding="14px", border_radius="8px", border="1px solid #e2e8f0", bg="white", width=["100%", "220px"], flex_grow="1"
                                ),
                                direction="row", wrap="wrap", spacing="3", width="100%", mb="4"
                            ),

                            # Barra de Progresso (Convertida para int)
                            rx.vstack(
                                rx.text(DesafioState.progresso_perc_fmt, size="2", weight="bold", color="#334155"),
                                rx.progress(value=(DesafioState.progresso_perc * 100).to(int), width="100%", height="12px"),
                                width="100%", mb="6"
                            ),

                            # Form Novo Aporte
                            rx.vstack(
                                rx.heading("📥 Registrar Novo Depósito / Aporte", font_size="1.1rem", color="#1e293b", mb="2"),
                                rx.grid(
                                    rx.vstack(
                                        rx.text("Data do Depósito (DD/MM/AAAA)", size="2", weight="bold"),
                                        rx.input(value=DesafioState.novo_data_deposito, on_change=DesafioState.set_novo_data_deposito, width="100%"),
                                        spacing="1"
                                    ),
                                    rx.vstack(
                                        rx.text("Valor Depositado (R$)", size="2", weight="bold"),
                                        rx.input(value=DesafioState.novo_valor_depositado, on_change=DesafioState.set_novo_valor_depositado, width="100%"),
                                        spacing="1"
                                    ),
                                    rx.vstack(
                                        rx.text("Local da Aplicação", size="2", weight="bold"),
                                        rx.select(locais_opcoes, value=DesafioState.novo_local_aplicacao, on_change=DesafioState.set_novo_local_aplicacao, width="100%"),
                                        spacing="1"
                                    ),
                                    columns={"base": "1", "md": "3"}, gap="4", width="100%", mb="3"
                                ),
                                rx.text("Se selecionou 'Outro (Personalizado)' acima, digite o nome:", size="2", weight="bold"),
                                rx.input(value=DesafioState.novo_outro_local, on_change=DesafioState.set_novo_outro_local, placeholder="Nome do Banco ou Corretora", width="100%", mb="3"),
                                rx.button("💾 Salvar Aporte no Desafio", on_click=DesafioState.salvar_aporte, color_scheme="blue"),
                                padding="20px", border="1px solid #e2e8f0", border_radius="10px", bg="white", width="100%", mb="6"
                            ),

                            # Extrato de Aportes
                            rx.heading("📊 Extrato de Aportes Realizados", font_size="1.1rem", color="#1e293b", mb="3"),
                            rx.cond(
                                DesafioState.lista_aportes_exibicao.length() > 0,
                                rx.box(
                                    rx.table.root(
                                        rx.table.header(
                                            rx.table.row(
                                                rx.table.column_header_cell("ID"),
                                                rx.table.column_header_cell("Data"),
                                                rx.table.column_header_cell("Local da Aplicação"),
                                                rx.table.column_header_cell("Valor"),
                                            )
                                        ),
                                        rx.table.body(
                                            rx.foreach(
                                                DesafioState.lista_aportes_exibicao,
                                                lambda item: rx.table.row(
                                                    rx.table.cell(item["id"]),
                                                    rx.table.cell(item["data"]),
                                                    rx.table.cell(item["local_aplicacao"]),
                                                    rx.table.cell(item["valor"]),
                                                )
                                            )
                                        ),
                                        variant="surface", size="2", width="100%"
                                    ),
                                    max_height="250px", overflow_y="auto", width="100%", border="1px solid #e2e8f0", border_radius="8px", mb="6"
                                ),
                                rx.text("Nenhum aporte registrado ainda.", color="gray", mb="6")
                            ),
                            width="100%", pt="4"
                        ),
                        value="aba_desafio"
                    ),

                    # ==================== ABA 2: RESGATES ====================
                    rx.tabs.content(
                        rx.vstack(
                            rx.heading("💸 Módulo de Resgate de Aportes", font_size="1.1rem", color="#1e293b", mb="2"),
                            rx.text("Registre retiradas ou resgates parciais/totais realizados nas suas contas.", color="gray", size="2", mb="4"),
                            
                            rx.grid(
                                rx.vstack(
                                    rx.text("Data do Resgate (DD/MM/AAAA)", size="2", weight="bold"),
                                    rx.input(value=DesafioState.resg_data, on_change=DesafioState.set_resg_data, width="100%"),
                                    spacing="1"
                                ),
                                rx.vstack(
                                    rx.text("Valor Resgatado (R$)", size="2", weight="bold"),
                                    rx.input(value=DesafioState.resg_valor, on_change=DesafioState.set_resg_valor, width="100%"),
                                    spacing="1"
                                ),
                                rx.vstack(
                                    rx.text("Instituição de Origem", size="2", weight="bold"),
                                    rx.select(locais_opcoes, value=DesafioState.resg_origem, on_change=DesafioState.set_resg_origem, width="100%"),
                                    spacing="1"
                                ),
                                columns={"base": "1", "md": "3"}, gap="4", width="100%", mb="3"
                            ),
                            rx.text("Motivo do Resgate / Destino (Ex: Emergência, Compra...)", size="2", weight="bold"),
                            rx.input(value=DesafioState.resg_motivo, on_change=DesafioState.set_resg_motivo, width="100%", mb="3"),
                            rx.button("📤 Registrar Resgate", on_click=DesafioState.salvar_resgate, color_scheme="red", mb="6"),

                            # Tabela de Resgates
                            rx.heading("📋 Histórico de Resgates Realizados", font_size="1.1rem", color="#1e293b", mb="3"),
                            rx.cond(
                                DesafioState.lista_resgates_exibicao.length() > 0,
                                rx.box(
                                    rx.table.root(
                                        rx.table.header(
                                            rx.table.row(
                                                rx.table.column_header_cell("ID"),
                                                rx.table.column_header_cell("Data"),
                                                rx.table.column_header_cell("Origem"),
                                                rx.table.column_header_cell("Valor"),
                                                rx.table.column_header_cell("Motivo"),
                                            )
                                        ),
                                        rx.table.body(
                                            rx.foreach(
                                                DesafioState.lista_resgates_exibicao,
                                                lambda item: rx.table.row(
                                                    rx.table.cell(item["id"]),
                                                    rx.table.cell(item["data"]),
                                                    rx.table.cell(item["local_origem"]),
                                                    rx.table.cell(item["valor"]),
                                                    rx.table.cell(item["motivo"]),
                                                )
                                            )
                                        ),
                                        variant="surface", size="2", width="100%"
                                    ),
                                    max_height="250px", overflow_y="auto", width="100%", border="1px solid #e2e8f0", border_radius="8px", mb="6"
                                ),
                                rx.text("Nenhum resgate registrado até o momento.", color="gray", mb="6")
                            ),
                            width="100%", pt="4"
                        ),
                        value="aba_resgates"
                    ),

                    # ==================== ABA 3: SIMULADOR ====================
                    rx.tabs.content(
                        rx.vstack(
                            rx.heading("🎯 Simulador de Antecipação de Metas", font_size="1.1rem", color="#1e293b", mb="2"),
                            rx.text("Descubra o impacto de um ganho extra (como um plantão CPROEIS) no alcance da sua meta.", color="gray", size="2", mb="4"),
                            
                            rx.grid(
                                rx.vstack(
                                    rx.text("Meta Alvo Total Desejada (R$)", size="2", weight="bold"),
                                    rx.input(value=DesafioState.sim_meta_alvo, on_change=DesafioState.set_sim_meta_alvo, width="100%"),
                                    spacing="1"
                                ),
                                rx.vstack(
                                    rx.text("Aporte Mensal Atual (R$)", size="2", weight="bold"),
                                    rx.input(value=DesafioState.sim_aporte_mensal, on_change=DesafioState.set_sim_aporte_mensal, width="100%"),
                                    spacing="1"
                                ),
                                rx.vstack(
                                    rx.text("Valor do Ganho Extra / Plantão (R$)", size="2", weight="bold"),
                                    rx.input(value=DesafioState.sim_ganho_extra, on_change=DesafioState.set_sim_ganho_extra, width="100%"),
                                    spacing="1"
                                ),
                                columns={"base": "1", "md": "3"}, gap="4", width="100%", mb="6"
                            ),

                            rx.flex(
                                rx.box(
                                    rx.text("Tempo estimado sem o extra", size="2", color="gray"),
                                    rx.heading(DesafioState.sim_meses_sem_extra, size="5", color="#dc2626"),
                                    padding="16px", border_radius="8px", border="1px solid #e2e8f0", bg="white", width=["100%", "250px"], flex_grow="1"
                                ),
                                rx.box(
                                    rx.text("Tempo estimado COM o extra", size="2", color="gray"),
                                    rx.heading(DesafioState.sim_meses_com_extra, size="5", color="#16a34a"),
                                    padding="16px", border_radius="8px", border="1px solid #e2e8f0", bg="white", width=["100%", "250px"], flex_grow="1"
                                ),
                                direction="row", wrap="wrap", spacing="4", width="100%", mb="6"
                            ),
                            width="100%", pt="4"
                        ),
                        value="aba_simulador"
                    ),

                    # ==================== ABA 4: CONSULTORIA ====================
                    rx.tabs.content(
                        rx.vstack(
                            rx.heading("📈 Painel Diário de Alocação & Mercado", font_size="1.1rem", color="#1e293b", mb="2"),
                            rx.text("Opções recomendadas no mercado financeiro para diversificação segura:", color="gray", size="2", mb="4"),

                            rx.flex(
                                rx.box(rx.text("Retorno Médio Esperado", size="2", color="gray"), rx.heading("105% a 110% CDI", size="4", color="blue"), padding="12px", border="1px solid #e2e8f0", border_radius="8px", width="220px"),
                                rx.box(rx.text("Segurança Coberta", size="2", color="gray"), rx.heading("FGC & Tesouro", size="4", color="green"), padding="12px", border="1px solid #e2e8f0", border_radius="8px", width="220px"),
                                rx.box(rx.text("Liquidez Principal", size="2", color="gray"), rx.heading("Diária (D+0)", size="4", color="purple"), padding="12px", border="1px solid #e2e8f0", border_radius="8px", width="220px"),
                                spacing="3", wrap="wrap", mb="6"
                            ),

                            rx.heading("📋 Checklist de Governança Financeira", font_size="1rem", color="#1e293b", mb="3"),
                            rx.vstack(
                                rx.checkbox("Possuo ao menos 6 meses do meu custo de vida guardados em liquidez diária."),
                                rx.checkbox("Meus investimentos estão divididos em pelo menos duas instituições financeiras."),
                                rx.checkbox("Acompanho periodicamente minhas despesas e receitas para manter os aportes."),
                                spacing="2", mb="6"
                            ),
                            width="100%", pt="4"
                        ),
                        value="aba_consultoria"
                    ),

                    default_value="aba_desafio",
                    width="100%",
                ),

                width="100%", align="start"
            ),
            width="100%", max_width="1200px", padding_x=["1em", "2em"], padding_top="1em", center_content=True
        ),
        width="100%", spacing="0", align="center"
    )