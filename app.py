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
    bdi = st.number_input("BDI (%)", min_value=0.0, value=25.0, step=1.0, format="%.2f")
bdi_calculo = bdi / 100
# ADICIONADO: Cria um espaço reservado na terceira coluna
with col_espaco:
    st.write("") # Pula uma linha para alinhar o texto com as caixas de input
    placeholder_total = st.empty()
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
# --- NOVO: Variável para armazenar a soma do valor em Reais ---
soma_valor_total = 0.0
# Baseado no seu comando 2, criei 4 linhas. 
# (No futuro, podemos transformar isso em um botão de "Adicionar Linha")
numero_de_linhas = 4
# Dicionário para armazenar a soma de todos os materiais
soma_materiais = {}
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
        
        # --- NOVO: Acumulando o valor total da linha ---
        soma_valor_total += total
        
        # --- LÓGICA DO COMANDO 2 ---
        consumo_mo1 = float(linha_db['consumo_mo1'])
        total = quantidade * preco_unitario
        total_formatado = f"{total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        
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
        # --- LÓGICA PARA SOMA DE MATERIAIS ---
        # A base de dados tem até 3 materiais por serviço
        for num_mat in [1, 2, 3]:
            col_nome = f'nome_material_{num_mat}'
            col_consumo = f'consumo_material_{num_mat}'
            col_unidade = f'un_material_{num_mat}'
            
            # Verifica se a coluna de material existe e se ela não está vazia (NaN)
            if col_nome in linha_db and pd.notna(linha_db[col_nome]):
                nome_mat = str(linha_db[col_nome]).strip()
                
                # Garante que não vai ler campos vazios do Excel
                if nome_mat and nome_mat.lower() != 'nan':
                    consumo_mat = float(linha_db[col_consumo])
                    unidade_mat = str(linha_db[col_unidade])
                    
                    # Calcula a quantidade necessária desse material para a linha atual
                    qtd_total_mat = quantidade * consumo_mat
                    
                    # Acumula no dicionário global
                    if nome_mat in soma_materiais:
                        soma_materiais[nome_mat]['quantidade'] += qtd_total_mat
                    else:
                        soma_materiais[nome_mat] = {
                            'quantidade': qtd_total_mat,
                            'unidade': unidade_mat
                        }
    else:
        # Campos vazios se nenhum serviço for selecionado
        col3.write("-")
        col5.write("-")
        col6.write("-")
# --- NOVO: EXIBIR O VALOR TOTAL DA PLANILHA ---
soma_valor_total = (soma_valor_total/1.25)*(1+float(bdi_calculo))
valor_total_formatado = f"{soma_valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# INSERIR APENAS ISTO:
valor_total_formatado = f"{soma_valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
#placeholder_total.subheader(f"Valor Total: R$ {valor_total_formatado}")
placeholder_total.markdown(
    f"<h3 style='text-align: center;'>Valor Total:R$ {valor_total_formatado}</h3>", 
    unsafe_allow_html=True
)
    
st.markdown("---")

# --- RESULTADOS E COMANDO 2 ---
#st.subheader("Valor Total: ")
st.subheader("Dimensionamento de Equipe de Mão de Obra")

# Total de horas
resultado_arredondado = round(soma_consumo_mo1)
#st.info(f"**Total de horas de consumo:** {resultado_arredondado} horas")

# Cálculo da quantidade de serventes (Comando 2)
# math.ceil arredonda sempre para o número inteiro de cima
qtd_serventes = math.ceil(soma_consumo_mo1 / (220 * meses_obra))

# Exibição do resultado do Comando 2
st.markdown(f"**Quantidade de serventes necessários: {qtd_serventes} profissional(is)**")
# --- ADICIONE ESTE BLOCO NO FINAL DO ARQUIVO ---
#st.subheader("Dimensionamento de Equipe: Pedreiro")

# Total de horas Pedreiro
resultado_arredondado_mo2 = round(soma_consumo_mo2)
#st.info(f"**Total de horas de consumo (Pedreiro):** {resultado_arredondado_mo2} horas")

# Cálculo da quantidade de pedreiros
qtd_pedreiros = math.ceil(soma_consumo_mo2 / (220 * meses_obra))

# Exibição do resultado
st.markdown(f"**Quantidade de pedreiros necessários: {qtd_pedreiros} profissional(is)**")
st.markdown("---")
st.subheader("Lista de Materiais Necessários")

# Verifica se existe algum material no dicionário
if soma_materiais:
    # Cria os cabeçalhos da tabela de materiais
    col_mat1, col_mat2, col_mat3 = st.columns([4, 1.5, 1])
    col_mat1.markdown("**Descrição do Material**")
    col_mat2.markdown("**Quantidade Total**")
    col_mat3.markdown("**Unidade**")
    
    # Itera sobre o dicionário acumulado e imprime os resultados
    for mat, info in soma_materiais.items():
        col_mat1, col_mat2, col_mat3 = st.columns([4, 1.5, 1])
        col_mat1.write(mat)
        
        # Formata a quantidade para exibir com 2 casas decimais e vírgula no padrão PT-BR
        qtd_formatada = f"{info['quantidade']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        col_mat2.write(qtd_formatada)
        
        col_mat3.write(info['unidade'])
else:
    st.info("Nenhum material necessário para os serviços selecionados atualmente.")