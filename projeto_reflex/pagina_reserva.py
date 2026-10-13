import reflex as rx
import pandas as pd
from datetime import datetime
import database
from projeto_reflex.states import FinanceState
from projeto_reflex.navegacao import barra_navegacao

class DiagnosticoState(rx.State):
    """Estado para gerir o diagnóstico de saúde financeira e competência."""
    competencia_selecionada: str = datetime.now().strftime("%m/%Y")

    def set_competencia_selecionada(self, valor: str):
        self.competencia_selecionada = valor

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
    def total_receitas(self) -> float:
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df = pd.read_sql_query("SELECT tipo, valor, data FROM lancamentos", conexao)
            conexao.close()
            if df.empty:
                return 0.0
            dt = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce", dayfirst=True)
            df["competencia"] = dt.dt.strftime("%m/%Y")
            df_mes = df[df["competencia"] == self.competencia_selecionada]
            return float(df_mes[df_mes["tipo"] == "Receita"]["valor"].sum())
        except Exception:
            return 0.0

    @rx.var
    def total_despesas_manuais(self) -> float:
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df = pd.read_sql_query("SELECT tipo, valor, data FROM lancamentos", conexao)
            conexao.close()
            if df.empty:
                return 0.0
            dt = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce", dayfirst=True)
            df["competencia"] = dt.dt.strftime("%m/%Y")
            df_mes = df[df["competencia"] == self.competencia_selecionada]
            return float(df_mes[df_mes["tipo"] == "Despesa"]["valor"].sum())
        except Exception:
            return 0.0

    @rx.var
    def total_parcelas_dividas(self) -> float:
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df = pd.read_sql_query("SELECT valor_parcela, status FROM dividas WHERE status = 'Pendente'", conexao)
            conexao.close()
            if df.empty:
                return 0.0
            return float(df[df["valor_parcela"] > 0]["valor_parcela"].sum())
        except Exception:
            return 0.0

    @rx.var
    def despesa_total_real(self) -> float:
        return self.total_despesas_manuais + self.total_parcelas_dividas

    @rx.var
    def saldo_livre(self) -> float:
        return self.total_receitas - self.despesa_total_real

    @rx.var
    def status_saude(self) -> str:
        rec = self.total_receitas
        esp = self.despesa_total_real
        sld = self.saldo_livre
        if rec == 0 and esp == 0:
            return "Sem Dados"
        elif sld < 0:
            return "🚨 Em Déficit (Vermelho)"
        elif sld == 0:
            return "⚠️ No Zero a Zero"
        else:
            return "✅ Com Sobra (Azul)"

    @rx.var
    def fmt_receitas(self) -> str:
        v = self.total_receitas
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def fmt_despesas(self) -> str:
        v = self.despesa_total_real
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def fmt_saldo(self) -> str:
        v = self.saldo_livre
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    

@rx.page(route="/reserva", title="Diagnóstico e Saúde Financeira")
def pagina_reserva() -> rx.Component:
    from .navegacao import barra_navegacao

    return rx.vstack(
        barra_navegacao(),
        rx.container(
            rx.vstack(
                rx.heading("💡 Consultoria Inteligente & Diagnóstico Financeiro", font_size={"base": "1.2rem", "md": "1.5rem"}, color="#1e293b", margin_top="15px", margin_bottom="2px"),
                rx.text("Análise automática da sua saúde financeira com base nos ganhos, compromissos e dívidas ativas.", color="#64748b", font_size="0.9rem", margin_bottom="15px"),
                rx.divider(mb="4"),

                # Filtro de Competência Responsivo
                rx.hstack(
                    rx.text("Mês/Ano de Referência:", weight="bold"),
                    rx.select(
                        DiagnosticoState.competencias_disponiveis,
                        value=DiagnosticoState.competencia_selecionada,
                        on_change=DiagnosticoState.set_competencia_selecionada,
                    ),
                    align="center",
                    wrap="wrap",
                    mb="4",
                ),

                rx.divider(mb="4"),

                # Métricas Atuais (Grid Responsiva: 1 coluna no telemóvel, 2 em tablets e 4 no desktop)
                rx.heading("📊 Seus Indicadores Atuais", font_size="1.2rem", color="#1e293b", mb="3"),
                rx.grid(
                    rx.card(rx.vstack(rx.text("🟢 Total de Ganhos", weight="bold"), rx.text(DiagnosticoState.fmt_receitas, color="green"))),
                    rx.card(rx.vstack(rx.text("🔴 Total de Compromissos", weight="bold"), rx.text(DiagnosticoState.fmt_despesas, color="red"))),
                    rx.card(rx.vstack(rx.text("⚖️ Saldo Livre", weight="bold"), rx.text(DiagnosticoState.fmt_saldo, color="blue"))),
                    rx.card(rx.vstack(rx.text("🩺 Status da Saúde", weight="bold"), rx.text(DiagnosticoState.status_saude, weight="bold"))),
                    columns={"base": "1", "sm": "2", "md": "4"},
                    spacing="4",
                    width="100%",
                    mb="6",
                ),

                rx.divider(mb="4"),

                # Orientação Personalizada baseada no saldo
                rx.heading("🧭 Roteiro Estratégico Personalizado", font_size="1.2rem", color="#1e293b", mb="3"),
                
                rx.cond(
                    DiagnosticoState.saldo_livre < 0,
                    rx.vstack(
                        rx.callout("🚨 Diagnóstico: Suas despesas e compromissos mensais estão superando os seus ganhos. O foco principal não é investir, e sim estancar o sangramento do orçamento.", color_scheme="red"),
                        rx.markdown("""
                            **Plano de Ação Imediato para Sair do Vermelho:**
                            1. **Estancar o Sangramento:** Priorize negociar as dívidas com juros altos (rotativo de cartão / cheque especial).
                            2. **Corte Cirúrgico de Custos:** Reduza supérfluos identificados nos lançamentos para reequilibrar o mês.
                            3. **A Metodologia do Centavo:** Evite pequenos gastos diários invisíveis que consomem boa parte do ganho mensal.
                        """),
                        spacing="3",
                    ),
                    rx.cond(
                        DiagnosticoState.saldo_livre == 0,
                        rx.vstack(
                            rx.callout("⚠️ Diagnóstico: Suas contas estão empatadas com os seus ganhos. Sem acúmulo de novas dívidas, mas sem construir gordura financeira.", color_scheme="yellow"),
                            rx.markdown("""
                                **Plano de Ação para Criar Folga:**
                                1. **Encontrar Margem:** Esprema 5% a 10% dos gastos mensais para gerar sobra livre.
                                2. **Acordo de Dívidas:** Use eventuais sobras para propor acordos à vista com desconto em dívidas pendentes.
                            """),
                            spacing="3",
                        ),
                        rx.vstack(
                            rx.callout("✅ Diagnóstico: Parabéns! Seus ganhos estão superiores aos compromissos mensais. Há sobra de caixa para direcionar ao futuro.", color_scheme="green"),
                            rx.markdown("""
                                **Plano de Ação Rumo à Reserva de Emergência:**
                                1. **Destino do Saldo Livre:** Direcione para **Renda Fixa com liquidez diária** (Tesouro Selic ou CDB 100% CDI). Alvo: 3 a 6 meses do custo de vida.
                                2. **Proteção FGC:** Opções seguras com rendimento diário e proteção do Fundo Garantidor de Créditos.
                                3. **Amortização:** Se houver dívidas parceladas, utilize excedentes para quitar parcelas antecipadamente e poupar juros.
                            """),
                            spacing="3",
                        ),
                    ),
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