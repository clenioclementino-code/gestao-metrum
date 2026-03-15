import streamlit as st
import pandas as pd
from datetime import datetime, date

# Configuração da página
st.set_page_config(page_title="Gestão Metrum - Clenio", layout="wide", page_icon="⚡")

# --- CONFIGURAÇÃO DA PLANILHA ---
# ID da sua planilha extraído do link que você passou
SHEET_ID = "1H-92JQuuSMGhJPxhs9houb4n08vVQztILIob6tQcM9U"
URL_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def carregar_dados():
    try:
        # Lê a planilha como um arquivo CSV em tempo real
        return pd.read_csv(URL_CSV)
    except:
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
            st.info("Para salvar de forma simples via GitHub, use o banco SQLite temporário ou configure o Google Cloud. Por segurança, o Google bloqueia escrita direta via URL comum.")
            # Nota: O Google mudou as regras recentemente. 
            # Vou manter a visualização ativa para você.

# --- PAINEL PRINCIPAL ---
st.title("🛡️ Controle de Validade")

if not df.empty:
    # Garante que as colunas existem
    cols_necessarias = ["nome", "certificado", "data_vencimento"]
    if all(col in df.columns for col in cols_necessarias):
        df['data_vencimento_dt'] = pd.to_datetime(df['data_vencimento'], errors='coerce').dt.date
        hoje = date.today()
        
        # Dashboard
        total = len(df)
        st.metric("📦 Equipamentos na Planilha", total)
        
        st.divider()
        
        # Tabela
        st.subheader("📋 Dados da Planilha Google")
        st.dataframe(df, use_container_width=True)
    else:
        st.error("A planilha precisa ter os cabeçalhos: id, nome, certificado, data_calibracao, data_vencimento")
else:
    st.warning("Insira dados diretamente na sua Planilha Google para vê-los aqui.")
