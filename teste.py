import streamlit as st
import pandas as pd
import math

st.set_page_config(layout="wide", page_title="Sistema de Orçamento")

st.title("Orçamento de Engenharia")

# --- CAMPO DIGITÁVEL DE MESES ---
meses_obra = st.number_input("Quantidade de meses de obra", min_value=1, value=1, step=1)
bdi = st.number_input(
    "BDI", 
    min_value=0.0, 
    max_value=100.0, 
    value=10.0, 
    step=0.1, 
    format="%.2f%%"
)
bdi_calculo = bdi / 100

st.markdown("---")

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados():
    return pd.read_excel("base_de_dados.xlsx")

try:
    df = carregar_dados()
except FileNotFoundError:
    st.error("Arquivo 'base_de_dados.xlsx' não encontrado. Verifique se ele está na mesma pasta.")
    st.stop()
except Exception as e:
    st.error(f"Erro ao ler o arquivo: {e}.")
    st.stop()

todos_servicos = df['nome_servico'].tolist()

# --- ESTRUTURA DA TABELA INTERATIVA ---
st.subheader("Planilha Orçamentária")
st.markdown("Preencha os dados diretamente na tabela abaixo. **No celular, arraste a tabela para os lados.**")

# 1. Inicializa o estado da tabela com 4 linhas vazias
if "dados_tabela" not in st.session_state:
    st.session_state.dados_tabela = pd.DataFrame({
        "Descrição": [None, None, None, None],
        "Quantidade": [1.0, 1.0, 1.0, 1.0]
    })

# 2. Prepara a tabela de exibição com as colunas calculadas
df_exibicao = st.session_state.dados_tabela.copy()
df_exibicao["Unidade"] = "-"
df_exibicao["Preço Unitário"] = 0.0
df_exibicao["Total"] = 0.0

soma_consumo_mo1 = 0.0
soma_consumo_mo2 = 0.0

# Faz os cálculos linha a linha baseado no que o usuário preencheu
for i, row in df_exibicao.iterrows():
    servico = row["Descrição"]
    qtd = row["Quantidade"]
    
    if pd.notna(servico) and servico in todos_servicos:
        linha_db = df[df['nome_servico'] == servico].iloc[0]
        
        # Preenche colunas que serão bloqueadas para edição
        df_exibicao.at[i, "Unidade"] = linha_db['un_servico']
        preco = float(linha_db['preco_unitario_do_servico'])
        df_exibicao.at[i, "Preço Unitário"] = preco
        df_exibicao.at[i, "Total"] = preco * qtd
        
        # Soma a mão de obra
        soma_consumo_mo1 += qtd * float(linha_db['consumo_mo1'])
        soma_consumo_mo2 += qtd * float(linha_db['consumo_mo2'])

# Reordena as colunas para a ordem correta de leitura
df_exibicao = df_exibicao[["Descrição", "Unidade", "Quantidade", "Preço Unitário", "Total"]]

# 3. Exibe o Editor de Dados na tela
df_editado = st.data_editor(
    df_exibicao,
    column_config={
        "Descrição": st.column_config.SelectboxColumn(
            "Descrição", 
            options=todos_servicos,
            required=False,
            width="large" # Dá mais espaço para textos longos
        ),
        "Unidade": st.column_config.TextColumn("Unidade", disabled=True),
        "Quantidade": st.column_config.NumberColumn("Quantidade", min_value=0.0, step=1.0),
        "Preço Unitário": st.column_config.NumberColumn("Preço Unitário", format="R$ %.2f", disabled=True),
        "Total": st.column_config.NumberColumn("Total", format="R$ %.2f", disabled=True)
    },
    num_rows="dynamic", # Mágica: Permite ao usuário adicionar e remover linhas!
    use_container_width=True,
    hide_index=False # Mantém o "1, 2, 3..." no início da linha simulando o campo "Item"
)

# 4. Lógica de Atualização Instantânea
# Pega apenas as colunas que o usuário pode editar
novos_dados_input = df_editado[["Descrição", "Quantidade"]]

# Se o usuário alterou algum serviço ou quantidade, atualiza e recarrega para calcular os totais
if not novos_dados_input.equals(st.session_state.dados_tabela):
    st.session_state.dados_tabela = novos_dados_input
    st.rerun()

st.markdown("---")

# --- RESULTADOS E DIMENSIONAMENTO DE EQUIPE ---
st.subheader("Dimensionamento de Equipe: Mão de Obra 1 (Servente)")
resultado_arredondado = round(soma_consumo_mo1)
st.info(f"**Total de horas de consumo:** {resultado_arredondado} horas")

qtd_serventes = math.ceil(soma_consumo_mo1 / (220 * meses_obra))
st.success(f"**Quantidade de serventes necessários (arredondado):** {qtd_serventes} profissional(is)")

st.subheader("Dimensionamento de Equipe: Mão de Obra 2 (Pedreiro)")
resultado_arredondado_mo2 = round(soma_consumo_mo2)
st.info(f"**Total de horas de consumo (Pedreiro):** {resultado_arredondado_mo2} horas")

qtd_pedreiros = math.ceil(soma_consumo_mo2 / (220 * meses_obra))
st.success(f"**Quantidade de pedreiros necessários (arredondado):** {qtd_pedreiros} profissional(is)")