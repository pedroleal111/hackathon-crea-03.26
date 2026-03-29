import streamlit as st
import pandas as pd
import math  # <-- Nova importação necessária para arredondar para cima
# Configuração da página para ocupar mais espaço na tela
st.set_page_config(layout="wide", page_title="Sistema de Orçamento")

st.title("Orçamento de Engenharia")
# --- COMANDO 1: CAMPO DIGITÁVEL DE MESES ---
# O usuário digita os meses. Mínimo de 1 mês para evitar erro de divisão por zero.
# A primeira e segunda colunas terão largura 1, e criamos uma terceira vazia com largura 2 
# para "empurrar" os campos para a esquerda e não ocupar a tela toda
col_meses, col_bdi, col_espaco = st.columns([1, 1, 2])

with col_meses:
    meses_obra = st.number_input("Meses de obra", min_value=1.0, step=1.0, value=1.0)

with col_bdi:
    bdi = st.number_input("BDI (%)", min_value=0.0, value=1.0, step=1.0, format="%.2f")
bdi_calculo = bdi / 100
st.markdown("---")
# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados():
    # Carrega a tabela do arquivo Excel fornecido
    return pd.read_excel("base_de_dados.xlsx")

try:
    df = carregar_dados()
except FileNotFoundError:
    st.error("Arquivo 'base_de_dados.xlsx' não encontrado. Verifique se ele está na mesma pasta do app.py.")
    st.stop()
except Exception as e:
    st.error(f"Erro ao ler o arquivo: {e}. Certifique-se de ter instalado o openpyxl (pip install openpyxl).")
    st.stop()

# Lista com todos os serviços (sem a opção vazia)
todos_servicos = df['nome_servico'].tolist()

# --- COMANDO 1: ESTRUTURA DA TABELA ---
st.subheader("Planilha Orçamentária")

# Cabeçalhos da tabela
col1, col2, col3, col4, col5, col6 = st.columns([0.5, 3.5, 1, 1, 1.5, 1.5])
col1.markdown("**Item**")
col2.markdown("**Descrição**")
col3.markdown("**Unidade**")
col4.markdown("**Quantidade**")
col5.markdown("**Preço Unitário**")
col6.markdown("**Total**")

# Variável para armazenar a soma de horas
soma_consumo_mo1 = 0.0
soma_consumo_mo2 = 0.0
# Baseado no seu comando 2, criei 4 linhas. 
# (No futuro, podemos transformar isso em um botão de "Adicionar Linha")
numero_de_linhas = 4

for i in range(numero_de_linhas):
    col1, col2, col3, col4, col5, col6 = st.columns([0.5, 3.5, 1, 1, 1.5, 1.5])
    
    # 1ª Coluna: Item (1, 2, 3...)
    col1.write(i + 1)
    
    # --- LÓGICA DE FILTRAGEM DE ITENS ÚNICOS ---
    # Descobre quais serviços já estão selecionados nas outras linhas
    selecionados_outros = [
        st.session_state.get(f"servico_{j}") 
        for j in range(numero_de_linhas) 
        if j != i and st.session_state.get(f"servico_{j}") is not None
    ]
    
    # Cria uma lista apenas com os serviços que ainda não foram usados
    opcoes_filtradas = [s for s in todos_servicos if s not in selecionados_outros]
    
    # 2ª Coluna: Descrição (com index=None para ficar vazio sem opção em branco)
    servico_selecionado = col2.selectbox(
        f"Descrição {i+1}", 
        options=opcoes_filtradas, 
        index=None,
        placeholder="Selecione um serviço...",
        key=f"servico_{i}", 
        label_visibility="collapsed"
    )
    
    # 4ª Coluna: Quantidade (Input digitável de 1 ao infinito)
    # Colocado aqui no código para podermos usar o valor no cálculo do Total abaixo
    quantidade = col4.number_input(
        f"Qtd {i+1}", 
        min_value=1.0, 
        value=1.0, 
        step=1.0, 
        key=f"qtd_{i}", 
        label_visibility="collapsed"
    )
    
   # Se o usuário selecionou algum serviço no Dropdown, preenchemos o resto:
    if servico_selecionado is not None:
        # Pegar a linha correspondente no banco de dados
        linha_db = df[df['nome_servico'] == servico_selecionado].iloc[0]
        
        # 3ª Coluna: Unidade
        unidade = linha_db['un_servico']
        col3.write(unidade)
        
       # 5ª Coluna: Preço Unitário (com formatação PT-BR)
        preco_unitario = float(linha_db['preco_unitario_do_servico'])
        preco_formatado = f"{preco_unitario:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        col5.write(f"R$ {preco_formatado}")
        
        # 6ª Coluna: Total (Quantidade x Preço Unitário com formatação PT-BR)
        total = quantidade * preco_unitario
        total_formatado = f"{total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        col6.write(f"R$ {total_formatado}")
        
        # --- LÓGICA DO COMANDO 2 ---
        consumo_mo1 = float(linha_db['consumo_mo1'])
        
        # 1. Calculamos o valor exato que essa linha vai adicionar
        valor_da_linha = quantidade * consumo_mo1
        
        # 2. Somamos esse valor ao total acumulado
        soma_consumo_mo1 += valor_da_linha
        
        # 3. IMPRIMIMOS O LOG NO TERMINAL
        print(f"-> Linha {i+1}: Adicionando {valor_da_linha:.2f} horas | Soma Acumulada no momento: {soma_consumo_mo1:.2f} horas")
        # LÓGICA PARA MÃO DE OBRA 2 (PEDREIRO)
        consumo_mo2 = float(linha_db['consumo_mo2'])
        valor_da_linha_mo2 = quantidade * consumo_mo2
        soma_consumo_mo2 += valor_da_linha_mo2
        print(f"-> Linha {i+1} (Pedreiro): Adicionando {valor_da_linha_mo2:.2f} horas | Soma Acumulada no momento: {soma_consumo_mo2:.2f} horas")
    else:
        # Campos vazios se nenhum serviço for selecionado
        col3.write("-")
        col5.write("-")
        col6.write("-")

st.markdown("---")

# --- RESULTADOS E COMANDO 2 ---
st.subheader("Dimensionamento de Equipe: Mão de Obra 1 (Servente)")

# Total de horas
resultado_arredondado = round(soma_consumo_mo1)
st.info(f"**Total de horas de consumo:** {resultado_arredondado} horas")

# Cálculo da quantidade de serventes (Comando 2)
# math.ceil arredonda sempre para o número inteiro de cima
qtd_serventes = math.ceil(soma_consumo_mo1 / (220 * meses_obra))

# Exibição do resultado do Comando 2
st.success(f"**Quantidade de serventes necessários (arredondado):** {qtd_serventes} profissional(is)")
# --- ADICIONE ESTE BLOCO NO FINAL DO ARQUIVO ---
st.subheader("Dimensionamento de Equipe: Mão de Obra 2 (Pedreiro)")

# Total de horas Pedreiro
resultado_arredondado_mo2 = round(soma_consumo_mo2)
st.info(f"**Total de horas de consumo (Pedreiro):** {resultado_arredondado_mo2} horas")

# Cálculo da quantidade de pedreiros
qtd_pedreiros = math.ceil(soma_consumo_mo2 / (220 * meses_obra))

# Exibição do resultado
st.success(f"**Quantidade de pedreiros necessários (arredondado):** {qtd_pedreiros} profissional(is)")