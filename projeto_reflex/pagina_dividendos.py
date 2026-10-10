import reflex as rx
import pandas as pd
from .navegacao import barra_navegacao

@rx.page(route="/dividendos", title="Dividendos e Simuladores")
def pagina_dividendos() -> rx.Component:
    
    # Dados para a tabela de fluxo
    dados_tabela = [
        {
            "Ativo / ETF": "SCHD",
            "Tipo de Ativo": "ETF de Dividendos Qualitativos",
            "Frequência": "Trimestral",
            "Meses de Pagamento Padrão": "Março, Junho, Setembro, Dezembro",
        },
        {
            "Ativo / ETF": "VYM",
            "Tipo de Ativo": "ETF de Alto Rendimento (Yield)",
            "Frequência": "Trimestral",
            "Meses de Pagamento Padrão": "Março, Junho, Setembro, Dezembro",
        },
        {
            "Ativo / ETF": "Realty Income (O)",
            "Tipo de Ativo": "REIT (Imobiliário Americano)",
            "Frequência": "Mensal",
            "Meses de Pagamento Padrão": "Todos os meses do ano",
        },
        {
            "Ativo / ETF": "Coca-Cola (KO)",
            "Tipo de Ativo": "Ação (Dividend King)",
            "Frequência": "Trimestral",
            "Meses de Pagamento Padrão": "Abril, Julho, Outubro, Dezembro",
        },
    ]

    return rx.box(
        barra_navegacao(),
        rx.container(
            rx.vstack(
                rx.heading("🌐 Estratégia de Dividendos Globais em Dólar", size="7", mb="3"),
                rx.text(
                    "Esta página integra o seu objetivo de geração de renda passiva em moeda forte ao seu planejamento financeiro atual, respeitando a sua fase de consolidação da Reserva de Emergência.",
                    color="gray",
                    mb="6",
                ),
                rx.divider(mb="6"),

                # 1. Pré-Requisitos do Projeto
                rx.heading("🚦 1. Pré-Requisitos do Projeto (Sinal Verde)", size="5", mb="3"),
                rx.text("Antes de aportar o primeiro dólar focado em dividendos, valide os seguintes marcos no seu controle principal:", color="gray", mb="4"),
                
                rx.grid(
                    rx.box(
                        rx.text("1. Reserva de Emergência Concluída", weight="bold", mb="2"),
                        rx.text("Mínimo de 3 a 6 meses dos seus custos mensais totais guardados em ativos de liquidez imediata no Brasil (CDB 100% CDI ou Tesouro Selic).", size="2"),
                        padding="4", background_color="#e0f2fe", border_radius="8px", border_left="4px solid #0284c7"
                    ),
                    rx.box(
                        rx.text("2. Capital de Risco Isolado", weight="bold", mb="2"),
                        rx.text("O dinheiro enviado para plataformas globais (como Avenue ou Nomad) deve ser aquele que você não precisará resgatar nos próximos 3 a 5 anos.", size="2"),
                        padding="4", background_color="#fef3c7", border_radius="8px", border_left="4px solid #d97706"
                    ),
                    columns="2", gap="4", width="100%", mb="6",
                ),
                rx.divider(mb="6"),

                # 2. Como Funciona a Renda Passiva nos EUA
                rx.heading("🇺🇸 2. Como Funciona a Renda Passiva nos EUA?", size="5", mb="3"),
                rx.text("Diferente do Brasil, onde a maioria das ações paga dividendos semestrais ou anuais, o mercado americano possui características únicas que facilitam a previsibilidade da renda:", color="gray", mb="4"),
                
                rx.grid(
                    rx.box(
                        rx.text("• Pagamentos Trimestrais ou Mensais:", weight="bold", mb="1"),
                        rx.text("A maioria das empresas americanas divide seus dividendos em 4 pagamentos ao ano. Existem também ativos específicos que pagam todos os meses.", size="2"),
                        padding="4", background_color="#f8fafc", border_radius="8px"
                    ),
                    rx.box(
                        rx.text("• Tributação Direta na Fonte:", weight="bold", mb="1"),
                        rx.text("Os EUA retêm automaticamente 30% de imposto de renda sobre o dividendo distribuído a estrangeiros. O valor líquido já cai pronto para uso ou reinvestimento.", size="2"),
                        padding="4", background_color="#f8fafc", border_radius="8px"
                    ),
                    columns="2", gap="4", width="100%", mb="6",
                ),
                rx.divider(mb="6"),

                # 3. Pilares de Ativos (Com Abas)
                rx.heading("🏗️ 3. Pilares de Ativos para Renda em Dólar", size="5", mb="3"),
                rx.text("Para montar uma carteira focada em renda com a segurança necessária, o estudo deve focar em três classes de ativos:", color="gray", mb="4"),

                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("👑 Dividend Aristocrats & Kings", value="tab1"),
                        rx.tabs.trigger("🏢 REITs (Fundos Imobiliários)", value="tab2"),
                        rx.tabs.trigger("📦 ETFs de Dividendos", value="tab3"),
                    ),
                    rx.tabs.content(
                        rx.box(
                            rx.heading("Ações Individuais Sólidas", size="4", mb="2"),
                            rx.text("São empresas listadas no índice S&P 500 que aumentam o pagamento de dividendos consecutivamente há pelo menos 25 anos (Aristocratas) ou 50 anos (Reis).", size="2", mb="2"),
                            rx.text("• Exemplos clássicos: Coca-Cola (KO), Johnson & Johnson (JNJ), Procter & Gamble (PG).", size="2", mb="2"),
                            rx.text("• Vantagem: Extrema resiliência econômica e histórico sólido de manutenção de proventos mesmo em crises globais.", size="2"),
                            padding="4", background_color="#f8fafc", border_radius="8px", mt="2"
                        ),
                        value="tab1",
                    ),
                    rx.tabs.content(
                        rx.box(
                            rx.heading("REITs (Real Estate Investment Trusts)", size="4", mb="2"),
                            rx.text("O equivalente americano aos Fundos Imobiliários (FIIs). São empresas que possuem, operam ou financiam imóveis geradores de caixa (galpões logísticos, shoppings, data centers).", size="2", mb="2"),
                            rx.text("• Exemplo clássico: Realty Income (O) – Conhecido como 'The Monthly Dividend Company' por pagar proventos mensalmente há décadas.", size="2", mb="2"),
                            rx.text("• Vantagem: A legislação americana obriga os REITs a distribuírem pelo menos 90% do lucro tributável aos acionistas.", size="2"),
                            padding="4", background_color="#f8fafc", border_radius="8px", mt="2"
                        ),
                        value="tab2",
                    ),
                    rx.tabs.content(
                        rx.box(
                            rx.heading("ETFs de Dividendos (Maior Segurança)", size="4", mb="2"),
                            rx.text("Em vez de escolher ações sozinhas, você adquire um pacote diversificado com centenas de empresas pagadoras de dividendos. É a forma mais recomendada para mitigar o risco de concentração.", size="2", mb="2"),
                            rx.text("• SCHD (Schwab U.S. Dividend Equity ETF): Focado em empresas americanas de altíssima qualidade e crescimento sustentável.", size="2", mb="2"),
                            rx.text("• VYM (Vanguard High Dividend Yield ETF): Focado em empresas com rendimentos (yields) acima da média do mercado.", size="2"),
                            padding="4", background_color="#f8fafc", border_radius="8px", mt="2"
                        ),
                        value="tab3",
                    ),
                    default_value="tab1",
                    width="100%",
                    mb="6",
                ),
                rx.divider(mb="6"),

                # 4. Tabela de Simulação de Fluxo de Dividendos
                rx.heading("📉 4. Tabela de Simulação de Fluxo de Dividendos", size="5", mb="3"),
                rx.text("Organize o cronograma de estudos combinando ativos com diferentes frequências de pagamento para preencher o seu calendário:", color="gray", mb="4"),

                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Ativo / ETF"),
                            rx.table.column_header_cell("Tipo de Ativo"),
                            rx.table.column_header_cell("Frequência"),
                            rx.table.column_header_cell("Meses de Pagamento Padrão"),
                        ),
                    ),
                    rx.table.body(
                        rx.table.row(
                            rx.table.cell("SCHD"),
                            rx.table.cell("ETF de Dividendos Qualitativos"),
                            rx.table.cell("Trimestral"),
                            rx.table.cell("Março, Junho, Setembro, Dezembro"),
                        ),
                        rx.table.row(
                            rx.table.cell("VYM"),
                            rx.table.cell("ETF de Alto Rendimento (Yield)"),
                            rx.table.cell("Trimestral"),
                            rx.table.cell("Março, Junho, Setembro, Dezembro"),
                        ),
                        rx.table.row(
                            rx.table.cell("Realty Income (O)"),
                            rx.table.cell("REIT (Imobiliário Americano)"),
                            rx.table.cell("Mensal"),
                            rx.table.cell("Todos os meses do ano"),
                        ),
                        rx.table.row(
                            rx.table.cell("Coca-Cola (KO)"),
                            rx.table.cell("Ação (Dividend King)"),
                            rx.table.cell("Trimestral"),
                            rx.table.cell("Abril, Julho, Outubro, Dezembro"),
                        ),
                    ),
                    width="100%",
                    variant="surface",
                    mb="6",
                ),
                rx.divider(mb="6"),

                # 5. Próximos Passos
                rx.heading("📝 5. Próximos Passos para o seu Planejamento", size="5", mb="3"),
                rx.ordered_list(
                    rx.list_item("Defina a sua Meta de Renda Passiva: Estabeleça o primeiro marco inicial (ex: Receber US$ 10 por mês, evoluindo progressivamente)."),
                    rx.list_item("Método de Aporte Constante: Separe um percentual planejado do orçamento após a consolidação da sua base no Brasil para iniciar a internacionalização."),
                    rx.list_item("Reinvestimento em Bola de Neve: Utilize os primeiros dólares recebidos de dividendos para comprar novas frações de ETFs, acelerando o crescimento exponencial."),
                    space="2",
                ),
                
                rx.divider(my="6"),
                rx.text(
                    "Este documento é de caráter exclusivamente educativo para guiar os seus estudos de planejamento financeiro. Investimentos em renda variável possuem riscos inerentes de mercado.",
                    size="1", color="gray", align="center", width="100%", mb="4"
                ),
                
                width="100%",
                padding="2em",
            )
        ),
    )