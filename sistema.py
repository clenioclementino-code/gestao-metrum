import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# Configuração da página
st.set_page_config(page_title="Gestão Metrum - Clenio", layout="wide", page_icon="⚡")

# --- CONEXÃO COM GOOGLE SHEETS ---
# Link da sua planilha fornecida
url = "https://docs.google.com/spreadsheets/d/1H-92JQuuSMGhJPxhs9houb4n08vVQztILIob6tQcM9U/edit?gid=0#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # ttl=0 garante que os dados sejam atualizados a cada recarregamento
        return conn.read(spreadsheet=url, ttl=0)
    except:
        # Cria um DataFrame vazio com as colunas necessárias se a planilha estiver limpa
        return pd.DataFrame(columns=["id", "nome", "certificado", "data_calibracao", "data_vencimento"])

# --- SIDEBAR ---
st.sidebar.title("⚡ METRUM")
st.sidebar.write(f"**Técnico:** Clenio")
st.sidebar.divider()

df = carregar_dados()

with st.sidebar.expander("➕ CADASTRAR EQUIPAMENTO", expanded=False):
    with st.form("cad_sidebar", clear_on_submit=True):
        n = st.text_input("Nome")
        ce = st.text_input("Certificado")
        d_cal = st.date_input("Data da Calibração", value=date.today(), format="DD/MM/YYYY")
        d_venc = st.date_input("Data de Expiração", value=date.today(), format="DD/MM/YYYY")
        
        if st.form_submit_button("SALVAR"):
            # Lógica para gerar ID incremental
            novo_id = int(df['id'].max() + 1) if not df.empty and 'id' in df.columns else 1
            
            nova_linha = pd.DataFrame([{
                "id": novo_id, 
                "nome": n, 
                "certificado": ce, 
                "data_calibracao": str(d_cal), 
                "data_vencimento": str(d_venc)
            }])
            
            # Remove colunas auxiliares antes de salvar para não sujar a planilha
            df_para_salvar = df.copy()
            if 'data_vencimento_dt' in df_para_salvar.columns:
                df_para_salvar = df_para_salvar.drop(columns=['data_vencimento_dt', 'dias_restantes'])
            
            df_atualizado = pd.concat([df_para_salvar, nova_linha], ignore_index=True)
            conn.update(spreadsheet=url, data=df_atualizado)
            st.success("Equipamento cadastrado com sucesso!")
            st.rerun()

# --- PAINEL PRINCIPAL ---
st.title("🛡️ Controle de Validade")

if not df.empty and 'data_vencimento' in df.columns:
    # Conversão para formato de data e cálculo de prazos
    df['data_vencimento_dt'] = pd.to_datetime(df['data_vencimento']).dt.date
    hoje = date.today()
    df['dias_restantes'] = df['data_vencimento_dt'].apply(lambda x: (x - hoje).days)
    
    # Ordenação: mais urgentes primeiro
    df = df.sort_values(by='dias_restantes', ascending=True)

    # --- DASHBOARD SUPERIOR ---
    vencidos = len(df[df['dias_restantes'] < 0])
    em_alerta = len(df[(df['dias_restantes'] >= 0) & (df['dias_restantes'] <= 30)])
    em_dia = len(df[df['dias_restantes'] > 30])
    total = len(df)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 Cadastrados", total)
    m2.metric("❌ Vencidos", vencidos)
    m3.metric("⚠️ Próximos a Vencer", em_alerta)
    m4.metric("✅ Em Dia", em_dia)
    
    st.divider()

    busca = st.text_input("🔍 Pesquisar na tabela:", placeholder="Nome ou certificado...")
    if busca:
        df = df[df['certificado'].astype(str).str.contains(busca, case=False) | df['nome'].str.contains(busca, case=False)]

    st.subheader("📋 Lista de Prioridades")

    # Cabeçalho da Tabela
    c_head = st.columns([2, 2, 1.5, 1.5, 1, 1.2])
    c_head[0].write("**Equipamento**")
    c_head[1].write("**Certificado**")
    c_head[2].write("**Vencimento**")
    c_head[3].write("**Prazo**")
    c_head[4].write("**Status**")
    c_head[5].write("**Ações**")
    st.divider()

    # Linhas da Tabela
    for index, row in df.iterrows():
        if row['dias_restantes'] < 0:
            status_txt, cor = "❌ VENCIDO", "#ff4b4b"
        elif row['dias_restantes'] <= 30:
            status_txt, cor = "⚠️ ALERTA", "#ffa500"
        else:
            status_txt, cor = "✅ EM DIA", "#28a745"

        prazo_txt = f"Vencido há {abs(row['dias_restantes'])} d" if row['dias_restantes'] < 0 else f"Faltam {row['dias_restantes']} d"

        r = st.columns([2, 2, 1.5, 1.5, 1, 1.2])
        r[0].write(row['nome'])
        r[1].write(row['certificado'])
        r[2].write(row['data_vencimento_dt'].strftime('%d/%m/%Y'))
        r[3].write(prazo_txt)
        r[4].markdown(f"<span style='color:{cor}; font-weight:bold'>{status_txt}</span>", unsafe_allow_html=True)
        
        # Ação de Excluir
        if r[5].button("🗑️", key=f"del_{row['id']}"):
            df_base = carregar_dados() # Lê a versão limpa do banco
            df_pos_del = df_base[df_base['id'].astype(int) != int(row['id'])]
            conn.update(spreadsheet=url, data=df_pos_del)
            st.rerun()

        st.write("---")
else:
    st.info("Aguardando o primeiro cadastro de equipamento, Clenio.")
