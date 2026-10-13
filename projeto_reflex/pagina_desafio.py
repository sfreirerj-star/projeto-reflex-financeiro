import reflex as rx
import pandas as pd
import database
from datetime import datetime
from .states import FinanceState

class DesafioState(rx.State):
    """Estado para gerir os aportes, resgates e simuladores do Desafio & Reserva."""
    
    # Campos de entrada de novo aporte
    novo_data_deposito: str = datetime.now().strftime("%d/%m/%Y")
    novo_valor_depositado: str = "532.00"
    novo_local_aplicacao: str = "Banco Itaú"
    novo_outro_local: str = ""
    
    # Configuração de Meta
    escolha_perfil_meta: str = "1 Plantão CPROEIS (R$ 532,00 / mês)"
    prazo_meses: int = 12
    valor_manual_meta: float = 532.00

    # Campos de resgate
    resg_data: str = datetime.now().strftime("%d/%m/%Y")
    resg_valor: str = "100.00"
    resg_origem: str = "Banco Itaú"
    resg_outro_origem: str = ""
    resg_motivo: str = ""

    # Setters explícitos para garantir compatibilidade no Reflex
    def set_novo_data_deposito(self, value: str):
        self.novo_data_deposito = value

    def set_novo_valor_depositado(self, value: str):
        self.novo_valor_depositado = value

    def set_novo_local_aplicacao(self, value: str):
        self.novo_local_aplicacao = value

    def set_novo_outro_local(self, value: str):
        self.novo_outro_local = value

    @rx.var
    def df_aportes(self) -> pd.DataFrame:
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
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
            conexao.commit()
            cursor.close()

            df = pd.read_sql_query("SELECT id, data, valor, local_aplicacao FROM desafio_aportes ORDER BY id DESC", conexao)
            conexao.close()
            return df
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
    def meta_mensal_atual(self) -> float:
        if self.escolha_perfil_meta == "Personalizado (Definir manual)":
            return float(self.valor_manual_meta)
        elif "CPROEIS" in self.escolha_perfil_meta:
            return 532.00
        elif "Conservador" in self.escolha_perfil_meta:
            return 300.00
        elif "Intermediário" in self.escolha_perfil_meta:
            return 800.00
        elif "Agressivo" in self.escolha_perfil_meta:
            return 1000.00
        return 532.00

    @rx.var
    def meta_total(self) -> float:
        return self.meta_mensal_atual * int(self.prazo_meses)

    @rx.var
    def fmt_meta_total(self) -> str:
        v = self.meta_total
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def fmt_total_aportado(self) -> str:
        v = self.total_aportado
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def fmt_total_resgatado(self) -> str:
        v = self.total_resgatado
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def fmt_total_guardado(self) -> str:
        v = self.total_guardado
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def lista_aportes_exibicao(self) -> list[dict]:
        df = self.df_aportes
        if df.empty:
            return []
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
        except Exception:
            pass


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

    return rx.vstack(
        barra_navegacao(),
        rx.container(
            rx.vstack(
                rx.heading("💰 Controle Financeiro — Painel do Marcelo", font_size="1.5rem", color="#1e293b", margin_top="15px"),
                rx.heading("🎯 Desafio Personalizado & Simulador de Antecipação", font_size="1.2rem", color="#334155"),
                rx.text("Controle seus aportes mensais, gerencie resgates, diversifique suas instituições financeiras e simule o impacto de ganhos extras nas suas metas.", color="#64748b", font_size="0.9rem", mb="4"),
                rx.divider(mb="4"),

                # --- CARDS DE RESUMO ---
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

                # --- REGISTRAR NOVO APORTE ---
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

                # --- EXTRATO DE APORTES ---
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

                width="100%", align="start"
            ),
            width="100%", max_width="1200px", padding_x=["1em", "2em"], padding_top="1em", center_content=True
        ),
        width="100%", spacing="0", align="center"
    )