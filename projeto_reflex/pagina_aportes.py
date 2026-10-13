import reflex as rx
import pandas as pd
from datetime import datetime
import database
from projeto_reflex.states import FinanceState
from .navegacao import barra_navegacao

class ResgateState(rx.State):
    """Estado específico para gerir o Módulo de Resgates e o Simulador."""
    data_resgate: str = datetime.now().strftime("%d/%m/%Y")
    valor_resgate: str = ""
    local_resgate: str = "Banco Itaú"
    motivo_resgate: str = ""

    # Estados do Simulador de Antecipação
    meta_alvo: float = 10000.00
    valor_ganho_extra: float = 532.00
    aporte_mensal_atual: float = 532.00
    qtd_extras_mes: int = 1

    # Estados do Simulador Avançado (Juros Compostos)
    patrimonio_inicial: float = 1614.00
    aporte_mensal_previsto: float = 532.00
    taxa_cdi_anual: float = 11.25
    horizonte_meses: int = 24

    def set_data_resgate(self, valor: str):
        self.data_resgate = valor

    def set_valor_resgate(self, valor: str):
        self.valor_resgate = valor

    def set_local_resgate(self, valor: str):
        self.local_resgate = valor

    def set_motivo_resgate(self, valor: str):
        self.motivo_resgate = valor

    # Setters do Simulador
    def set_meta_alvo(self, val: str):
        try: self.meta_alvo = float(val.replace(",", "."))
        except: pass

    def set_valor_ganho_extra(self, val: str):
        try: self.valor_ganho_extra = float(val.replace(",", "."))
        except: pass

    def set_aporte_mensal_atual(self, val: str):
        try: self.aporte_mensal_atual = float(val.replace(",", "."))
        except: pass

    def set_qtd_extras_mes(self, val: str):
        try: self.qtd_extras_mes = int(val)
        except: pass

    # Setters Simulador Avançado
    def set_patrimonio_inicial(self, val: str):
        try: self.patrimonio_inicial = float(val.replace(",", "."))
        except: pass

    def set_aporte_mensal_previsto(self, val: str):
        try: self.aporte_mensal_previsto = float(val.replace(",", "."))
        except: pass

    def set_taxa_cdi_anual(self, val: str):
        try: self.taxa_cdi_anual = float(val.replace(",", "."))
        except: pass

    def set_horizonte_meses(self, val: str):
        try: self.horizonte_meses = int(val)
        except: pass

    @rx.var
    def tempo_sem_extra(self) -> str:
        if self.aporte_mensal_atual <= 0:
            return "Indefinido"
        meses = self.meta_alvo / self.aporte_mensal_atual
        return f"{meses:.1f} meses"

    @rx.var
    def tempo_com_extra(self) -> str:
        reforco = self.aporte_mensal_atual + (self.valor_ganho_extra * self.qtd_extras_mes)
        if reforco <= 0:
            return "Indefinido"
        meses = self.meta_alvo / reforco
        return f"{meses:.1f} meses"

    @rx.var
    def reforco_mensal_injetado_fmt(self) -> str:
        total = self.valor_ganho_extra * self.qtd_extras_mes
        return f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def patrimonio_projetado_fmt(self) -> str:
        taxa_mensal = (self.taxa_cdi_anual / 100.0) / 12.0
        pv = self.patrimonio_inicial
        pmt = self.aporte_mensal_previsto
        n = self.horizonte_meses
        
        fv = pv * ((1 + taxa_mensal) ** n)
        if taxa_mensal > 0:
            fv += pmt * (((1 + taxa_mensal) ** n - 1) / taxa_mensal)
        else:
            fv += pmt * n

        return f"R$ {fv:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def realizar_resgate(self):
        if not self.valor_resgate:
            return rx.window_alert("Por favor, preencha o valor do resgate.")
        try:
            datetime.strptime(self.data_resgate.strip(), "%d/%m/%Y")
            valor_float = float(self.valor_resgate.replace(",", "."))
            
            database.inicializar_banco()
            conexao = database.obter_conexao()
            cursor = conexao.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS desafio_resgates (
                    id SERIAL PRIMARY KEY,
                    data VARCHAR(20),
                    valor NUMERIC,
                    local_origem VARCHAR(100),
                    motivo TEXT
                )
            """)
            
            cursor.execute(
                "INSERT INTO desafio_resgates (data, valor, local_origem, motivo) VALUES (%s, %s, %s, %s)",
                (self.data_resgate.strip(), valor_float, self.local_resgate, self.motivo_resgate.strip())
            )
            conexao.commit()
            cursor.close()
            conexao.close()

            self.valor_resgate = ""
            self.motivo_resgate = ""
            return rx.window_alert("Resgate registado com sucesso!")
        except ValueError:
            return rx.window_alert("Data inválida. Utilize o formato DD/MM/AAAA.")
        except Exception as e:
            return rx.window_alert(f"Erro ao registar resgate: {e}")

    @rx.var
    def lista_resgates(self) -> list[dict]:
        try:
            database.inicializar_banco()
            conexao = database.obter_conexao()
            df = pd.read_sql_query("SELECT id, data, valor, local_origem, motivo FROM desafio_resgates ORDER BY id DESC", conexao)
            conexao.close()

            if df.empty:
                return []

            resultado = []
            for _, row in df.iterrows():
                val_float = float(row['valor'])
                resultado.append({
                    "id": int(row["id"]),
                    "data": str(row["data"]),
                    "local": str(row["local_origem"]),
                    "motivo": str(row["motivo"] or "-"),
                    "valor": f"R$ {val_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                })
            return resultado
        except Exception:
            return []


def card_metrica_desafio(titulo: str, valor: str, cor_borda: str = "#2563eb", tag: str = None) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(titulo, font_size="0.8rem", color="#64748b", font_weight="600"),
            rx.text(valor, font_size="1.3rem", color="#1e293b", font_weight="bold", white_space="nowrap"),
            rx.cond(
                tag is not None,
                rx.badge(tag, color_scheme="green", variant="soft", font_size="0.75rem"),
            ),
            spacing="1",
            align_items="start",
        ),
        bg="white",
        padding="16px",
        border_radius="10px",
        box_shadow="0 2px 4px rgba(0,0,0,0.05)",
        border_left=f"5px solid {cor_borda}",
        border_top="1px solid #e2e8f0",
        border_right="1px solid #e2e8f0",
        border_bottom="1px solid #e2e8f0",
        width="100%",
    )

@rx.page(route="/aportes", title="Desafio Reserva & Aportes")
def pagina_aportes() -> rx.Component:
    return rx.vstack(
        barra_navegacao(),
        rx.container(
            rx.vstack(
                rx.heading("🎯 Desafio Personalizado & Simulador de Antecipação", font_size="1.5rem", color="#1e293b", margin_top="15px", margin_bottom="2px"),
                rx.text("Controle seus aportes mensais, gerencie resgates, diversifique suas instituições financeiras e simule o impacto de ganhos extras nas suas metas.", color="#64748b", font_size="0.9rem", margin_bottom="15px"),
                rx.divider(mb="4"),

                # Sistema de Abas Equivalente ao Streamlit
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("🎯 Meu Desafio & Aportes", value="desafio"),
                        rx.tabs.trigger("💸 Módulo de Resgates", value="resgate"),
                        rx.tabs.trigger("🎯 Simulador de Antecipação", value="simulador"),
                        rx.tabs.trigger("📈 Consultoria Diária de Investimentos", value="orientacao"),
                    ),
                    
                    # --- ABA 1: MEU DESAFIO & APORTES ---
                    rx.tabs.content(
                        rx.vstack(
                            rx.accordion.root(
                                rx.accordion.item(
                                    header=rx.heading("⚙ Configurar / Selecionar Meta Mensal (Inclui CPROEIS)", size="3"),
                                    content=rx.grid(
                                        rx.vstack(
                                            rx.text("Escolha o Perfil / Valor Mensal", weight="bold", size="2"),
                                            rx.select(
                                                [
                                                    "Personalizado (Definir manual)",
                                                    "1 Plantão CPROEIS (R$ 532,00 / mês)",
                                                    "Conservador (R$ 300,00 / mês)",
                                                    "Intermediário (R$ 800,00 / mês)",
                                                    "Agressivo (R$ 1.000,00 / mês)",
                                                ],
                                                value=FinanceState.escolha_perfil,
                                                on_change=FinanceState.set_escolha_perfil,
                                                width="100%",
                                            ),
                                            spacing="1",
                                        ),
                                        rx.vstack(
                                            rx.text("Valor Desejado por Mês (R$)", weight="bold", size="2"),
                                            rx.input(
                                                value=FinanceState.algum_valor, 
                                                on_change=FinanceState.set_algum_valor,
                                                placeholder="532,00",
                                                width="100%",
                                            ),
                                            spacing="1",
                                        ),
                                        columns="2",
                                        gap="4",
                                        width="100%",
                                        padding="10px",
                                    ),
                                ),
                                collapsible=True,
                                width="100%",
                                mb="4",
                            ),

                            # PAINEL DE CARTÕES
                            rx.grid(
                                card_metrica_desafio("Meta Total Calculada", "R$ 6.384,00", "#2563eb"),
                                card_metrica_desafio("Total Aportado", "R$ 2.146,00", "#16a34a"),
                                card_metrica_desafio("Total Resgatado", "R$ 532,00", "#dc2626"),
                                card_metrica_desafio("Patrimônio Líquido Guardado", "R$ 1.614,00", "#8b5cf6"),
                                columns="4",
                                gap="4",
                                width="100%",
                                mb="3",
                            ),

                            # Barra de Progresso do Desafio
                            rx.vstack(
                                rx.text("Progresso Atual do Desafio: 25% alcançado", size="2", color="#64748b", weight="bold"),
                                rx.progress(value=25, width="100%", color_scheme="blue", height="8px"),
                                width="100%",
                                mb="6",
                            ),

                            rx.divider(mb="4"),

                            # Formulário de Depósito / Aporte
                            rx.heading("📥 Registrar Novo Depósito / Aporte", font_size="1.2rem", color="#1e293b", mb="3"),
                            rx.grid(
                                rx.vstack(
                                    rx.text("Data do Aporte (DD/MM/AAAA)", weight="bold", size="2"),
                                    rx.input(
                                        placeholder="DD/MM/AAAA",
                                        value=FinanceState.data_aporte,
                                        on_change=FinanceState.set_data_aporte,
                                        width="100%",
                                    ),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("Local de Aplicação", weight="bold", size="2"),
                                    rx.select(
                                        [
                                            "Banco Itaú",
                                            "Nomad (Investimentos em Dólar)",
                                            "Sofisa Direto (CDB 105% CDI)",
                                            "Banco Inter (CDB Liquidez Diária)",
                                            "Nubank (Caixinha / RDB 100% CDI)",
                                            "Tesouro Selic (Tesouro Direto)",
                                            "Outro (Personalizado)",
                                        ],
                                        value=FinanceState.local_selecionado,
                                        on_change=FinanceState.set_local_selecionado,
                                        width="100%",
                                    ),
                                    spacing="1",
                                ),
                                rx.box(
                                    rx.button("💾 Salvar Aporte no Desafio", on_click=FinanceState.salvar_aporte, color_scheme="blue", width="100%"),
                                    width="100%",
                                ),
                                columns="3",
                                gap="4",
                                width="100%",
                                align_items="end",
                                mb="4",
                            ),
                            padding="20px",
                            border="1px solid #e2e8f0",
                            border_radius="10px",
                            bg="#ffffff",
                            box_shadow="sm",
                            spacing="4",
                            width="100%",
                        ),
                        value="desafio",
                    ),
                    
                    # --- ABA 2: RESGATES ---
                    rx.tabs.content(
                        rx.vstack(
                            rx.heading("💸 Módulo de Resgate de Aportes", font_size="1.2rem", color="#1e293b", mt="3", mb="2"),
                            rx.text("Registre retiradas ou resgates parciais/totais realizados dos seus investimentos.", color="#64748b", mb="3"),
                            
                            rx.vstack(
                                rx.grid(
                                    rx.vstack(
                                        rx.text("Data do Resgate (DD/MM/AAAA)", weight="bold", size="2"),
                                        rx.input(value=ResgateState.data_resgate, on_change=ResgateState.set_data_resgate, width="100%"),
                                        spacing="1",
                                    ),
                                    rx.vstack(
                                        rx.text("Valor do Resgate (R$)", weight="bold", size="2"),
                                        rx.input(value=ResgateState.valor_resgate, on_change=ResgateState.set_valor_resgate, placeholder="0.00", width="100%"),
                                        spacing="1",
                                    ),
                                    rx.vstack(
                                        rx.text("Instituição / Origem", weight="bold", size="2"),
                                        rx.select(
                                            ["Banco Itaú", "Nomad", "Sofisa Direto", "Banco Inter", "Nubank", "Tesouro Selic", "Outro"],
                                            value=ResgateState.local_resgate,
                                            on_change=ResgateState.set_local_resgate,
                                            width="100%",
                                        ),
                                        spacing="1",
                                    ),
                                    columns="3",
                                    gap="4",
                                    width="100%",
                                    mb="3",
                                ),
                                rx.vstack(
                                    rx.text("Motivo / Destino do Resgate", weight="bold", size="2"),
                                    rx.input(value=ResgateState.motivo_resgate, on_change=ResgateState.set_motivo_resgate, placeholder="Ex: Emergência, Compra de Ativo...", width="100%"),
                                    spacing="1",
                                    width="100%",
                                    mb="3",
                                ),
                                rx.button("💸 Efetuar e Registar Resgate", on_click=ResgateState.realizar_resgate, color_scheme="red", width="100%"),
                                padding="20px",
                                border="1px solid #e2e8f0",
                                border_radius="10px",
                                bg="#ffffff",
                                box_shadow="sm",
                                width="100%",
                                mb="6",
                            ),

                            rx.divider(mb="4"),

                            rx.heading("📋 Histórico de Resgates Realizados", font_size="1.2rem", color="#1e293b", mb="3"),
                            rx.cond(
                                ResgateState.lista_resgates.length() > 0,
                                rx.table.root(
                                    rx.table.header(
                                        rx.table.row(
                                            rx.table.column_header_cell("ID"),
                                            rx.table.column_header_cell("Data"),
                                            rx.table.column_header_cell("Instituição"),
                                            rx.table.column_header_cell("Motivo"),
                                            rx.table.column_header_cell("Valor Resgatado"),
                                        ),
                                    ),
                                    rx.table.body(
                                        rx.foreach(
                                            ResgateState.lista_resgates,
                                            lambda item: rx.table.row(
                                                rx.table.cell(item["id"]),
                                                rx.table.cell(item["data"]),
                                                rx.table.cell(item["local"]),
                                                rx.table.cell(item["motivo"]),
                                                rx.table.cell(item["valor"]),
                                            ),
                                        )
                                    ),
                                    variant="surface",
                                    size="3",
                                    width="100%",
                                ),
                                rx.text("Nenhum resgate registado até ao momento.", color="gray"),
                            ),
                            spacing="4",
                            width="100%",
                        ),
                        value="resgate",
                    ),
                    
                    # --- ABA 3: SIMULADOR ---
                    rx.tabs.content(
                        rx.vstack(
                            rx.heading("🎯 Simulador de Antecipação de Metas", font_size="1.2rem", color="#1e293b", mt="3", mb="2"),
                            rx.text("Descubra o impacto de um ganho extra (como um plantão ou projeto digital) no alcance da sua meta de reserva.", color="#64748b", mb="3"),
                            
                            rx.grid(
                                rx.vstack(
                                    rx.text("Meta Alvo Total Desejada (R$)", weight="bold", size="2"),
                                    rx.input(value=ResgateState.meta_alvo.to_string(), on_change=ResgateState.set_meta_alvo, width="100%"),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("Valor do Ganho Extra Pontual / Plantão Extra (R$)", weight="bold", size="2"),
                                    rx.input(value=ResgateState.valor_ganho_extra.to_string(), on_change=ResgateState.set_valor_ganho_extra, width="100%"),
                                    spacing="1",
                                ),
                                columns="2",
                                gap="4",
                                width="100%",
                                mb="3",
                            ),
                            rx.grid(
                                rx.vstack(
                                    rx.text("Sua média de aporte mensal atual (R$)", weight="bold", size="2"),
                                    rx.input(value=ResgateState.aporte_mensal_atual.to_string(), on_change=ResgateState.set_aporte_mensal_atual, width="100%"),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("Quantos extras desses você faria no mês?", weight="bold", size="2"),
                                    rx.input(value=ResgateState.qtd_extras_mes.to_string(), on_change=ResgateState.set_qtd_extras_mes, width="100%"),
                                    spacing="1",
                                ),
                                columns="2",
                                gap="4",
                                width="100%",
                                mb="4",
                            ),

                            rx.heading("📊 Resultado da Simulação", font_size="1.1rem", color="#1e293b", mb="2"),
                            rx.grid(
                                card_metrica_desafio("Tempo estimado sem o extra", ResgateState.tempo_sem_extra, "#2563eb"),
                                card_metrica_desafio("Tempo estimado COM o extra", ResgateState.tempo_com_extra, "#16a34a"),
                                card_metrica_desafio("Reforço Mensal Injetado", ResgateState.reforco_mensal_injetado_fmt, "#8b5cf6"),
                                columns="3",
                                gap="4",
                                width="100%",
                                mb="6",
                            ),

                            rx.divider(mb="4"),

                            rx.heading("📈 Simulador Avançado de Prazo e Juros Compostos (Reserva de Emergência)", font_size="1.2rem", color="#1e293b", mb="2"),
                            rx.text("Projete o crescimento do seu capital ao longo dos meses considerando uma taxa média de rendimento (ex: 100% a 105% do CDI).", color="#64748b", mb="3"),
                            
                            rx.grid(
                                rx.vstack(
                                    rx.text("Patrimônio Inicial Guardado (R$)", weight="bold", size="2"),
                                    rx.input(value=ResgateState.patrimonio_inicial.to_string(), on_change=ResgateState.set_patrimonio_inicial, width="100%"),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("Aporte Mensal Previsto (R$)", weight="bold", size="2"),
                                    rx.input(value=ResgateState.aporte_mensal_previsto.to_string(), on_change=ResgateState.set_aporte_mensal_previsto, width="100%"),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("Taxa CDI Anual Estimada (%)", weight="bold", size="2"),
                                    rx.input(value=ResgateState.taxa_cdi_anual.to_string(), on_change=ResgateState.set_taxa_cdi_anual, width="100%"),
                                    spacing="1",
                                ),
                                columns="3",
                                gap="4",
                                width="100%",
                                mb="3",
                            ),
                            rx.vstack(
                                rx.text("Horizonte de Projeção (Meses)", weight="bold", size="2"),
                                rx.input(value=ResgateState.horizonte_meses.to_string(), on_change=ResgateState.set_horizonte_meses, width="100%"),
                                spacing="1",
                                width="100%",
                                mb="3",
                            ),
                            
                            rx.card(
                                rx.vstack(
                                    rx.text("Patrimônio Total Projetado no Período", font_size="0.85rem", color="#64748b", weight="bold"),
                                    rx.heading(ResgateState.patrimonio_projetado_fmt, font_size="1.5rem", color="#16a34a"),
                                    spacing="1",
                                ),
                                bg="white",
                                padding="16px",
                                border_radius="10px",
                                width="100%",
                                mb="4",
                            ),

                            spacing="4",
                            width="100%",
                        ),
                        value="simulador",
                    ),
                    
                    # --- ABA 4: CONSULTORIA DIÁRIA (PREENCHIDA COMPLETA) ---
                    rx.tabs.content(
                        rx.vstack(
                            rx.heading("📈 Painel Diário de Alocação & Mercado (Perfil Moderado)", font_size="1.2rem", color="#1e293b", mt="3", mb="2"),
                            rx.text("Opções recomendadas no mercado financeiro para diversificação segura e rentável:", color="#64748b", mb="4"),
                            
                            # Métricas de Alocação
                            rx.grid(
                                card_metrica_desafio("Retorno Médio Esperado", "105% a 110% CDI", "#2563eb", tag="↑ Pós-fixado"),
                                card_metrica_desafio("Segurança Coberta", "FGC & Tesouro Nacional", "#16a34a", tag="↑ Garantido"),
                                card_metrica_desafio("Liquidez Principal", "Diária (D+0)", "#dc2626", tag="↑ Resgate Imediato"),
                                columns="3",
                                gap="4",
                                width="100%",
                                mb="6",
                            ),

                            # Tabela de Opções de Bancos e Corretoras
                            rx.heading("🏦 Melhores Opções de Bancos e Corretoras no Mercado", font_size="1.1rem", color="#1e293b", mb="3"),
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("Instituição / Corretora"),
                                        rx.table.column_header_cell("Produto Recomendado"),
                                        rx.table.column_header_cell("Vantagem para Reserva"),
                                    )
                                ),
                                rx.table.body(
                                    rx.table.row(
                                        rx.table.cell("Banco Itaú", font_weight="bold"),
                                        rx.table.cell("CDBs e Fundos DI"),
                                        rx.table.cell("Solidez do maior banco privado do Brasil"),
                                    ),
                                    rx.table.row(
                                        rx.table.cell("Nomad (Global)", font_weight="bold"),
                                        rx.table.cell("Investimento Internacional em Dólar"),
                                        rx.table.cell("Diversificação cambial geográfica"),
                                    ),
                                    rx.table.row(
                                        rx.table.cell("Sofisa Direto", font_weight="bold"),
                                        rx.table.cell("CDB Liquidez Diária (105% CDI)"),
                                        rx.table.cell("Excelente taxa para pós-fixado com FGC"),
                                    ),
                                    rx.table.row(
                                        rx.table.cell("Banco Inter", font_weight="bold"),
                                        rx.table.cell("CDB Mais Limite / Liquidez Diária"),
                                        rx.table.cell("Praticidade e solidez de banco múltiplo"),
                                    ),
                                    rx.table.row(
                                        rx.table.cell("Tesouro Direto", font_weight="bold"),
                                        rx.table.cell("Tesouro Selic 2029 / 2031"),
                                        rx.table.cell("Segurança soberana máxima do governo"),
                                    ),
                                ),
                                variant="surface",
                                size="3",
                                width="100%",
                                mb="6",
                            ),

                            # Estratégia de Diversificação
                            rx.heading("💡 Estratégia de Diversificação (Regra dos Ovos)", font_size="1.1rem", color="#1e293b", mb="2"),
                            rx.callout(
                                "📌 Dica de Ouro: Dividir os aportes entre 2 ou 3 instituições diferentes (por exemplo, Banco Itaú, Nomad e Sofisa) protege seu patrimônio, garante taxas competitivas e mantém o valor protegido.",
                                color_scheme="blue",
                                width="100%",
                                mb="6",
                            ),

                            # Checklist de Governança
                            rx.heading("📋 Checklist de Saúde Financeira e Governança", font_size="1.1rem", color="#1e293b", mb="2"),
                            rx.text("Garanta que sua estrutura patrimonial e de documentos esteja perfeitamente organizada:", color="#64748b", mb="3"),
                            
                            rx.vstack(
                                rx.checkbox("Possuo ao menos 6 meses do meu custo de vida guardados em ativos de liquidez diária."),
                                rx.checkbox("Meus investimentos estão divididos em pelo menos duas instituições financeiras."),
                                rx.checkbox("Acompanho periodicamente minhas despesas e receitas mensais."),
                                rx.checkbox("Mantenho meus registros administrativos e comprovações organizados."),
                                spacing="3",
                                align_items="start",
                                mb="4",
                            ),
                            spacing="4",
                            width="100%",
                        ),
                        value="orientacao",
                    ),
                    default_value="desafio",
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