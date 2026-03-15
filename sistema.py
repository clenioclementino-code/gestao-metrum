import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

# --- CONFIGURAÇÃO E BANCO DE DADOS ---
# O banco SQLite será criado automaticamente no servidor do Streamlit
conn = sqlite3.connect('gestao_validade.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS equipamentos 
              (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, certificado TEXT, 
               data_calibracao TEXT, data_vencimento TEXT)''')
conn.commit()

st.set_page_config(page_title="Gestão Metrum - Clenio", layout="wide", page_icon="⚡")

# --- SIDEBAR ---
st.sidebar.title("⚡ METRUM")
st.sidebar.write(f"**Técnico:** Clenio")
st.sidebar.divider()

with st.sidebar.expander("➕ CADASTRAR EQUIPAMENTO", expanded=False):
    with st.form("cad_sidebar", clear_on_submit=True):
        n = st.text_input("Nome")
        ce = st.text_input("Certificado")
        # Calendários com formato brasileiro
        d_cal = st.date_input("Data da Calibração", value=date.today(), format="DD/MM/YYYY")
        d_venc = st.date_input("Data de Expiração", value=date.today(), format="DD/MM/YYYY")
        
        if st.form_submit_button("SALVAR"):
            c.execute("INSERT INTO equipamentos (nome, certificado, data_calibracao, data_vencimento) VALUES (?,?,?,?)",
                      (n, ce, str(d_cal), str(d_venc)))
            conn.commit()
            st.rerun()

# --- PAINEL PRINCIPAL ---
st.title("🛡️ Controle de Validade")

df = pd.read_sql_query("SELECT * FROM equipamentos", conn)

if not df.empty:
    # Tratamento de datas
    df['data_vencimento_dt'] = pd.to_datetime(df['data_vencimento']).dt.date
    hoje = date.today()
    df['dias_restantes'] = df['data_vencimento_dt'].apply(lambda x: (x - hoje).days)
    
    # Ordenação por urgência
    df = df.sort_values(by='dias_restantes', ascending=True)

    # --- DASHBOARD ---
    vencidos = len(df[df['dias_restantes'] < 0])
    em_alerta = len(df[(df['dias_restantes'] >= 0) & (df['dias_restantes'] <= 30)])
    em_dia = len(df[df['dias_restantes'] > 30])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 Cadastrados", len(df))
    m2.metric("❌ Vencidos", vencidos)
    m3.metric("⚠️ Em Alerta", em_alerta)
    m4.metric("✅ Em Dia", em_dia)
    
    st.divider()

    # Busca
    busca = st.text_input("🔍 Pesquisar na tabela:", placeholder="Nome ou certificado...")
    if busca:
        df = df[df['certificado'].str.contains(busca, case=False) | df['nome'].str.contains(busca, case=False)]

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
        r[2].write(row['data_vencimento_dt'].strftime('%d/%m/%Y')) # Data BR
        r[3].write(prazo_txt)
        r[4].markdown(f"<span style='color:{cor}; font-weight:bold'>{status_txt}</span>", unsafe_allow_html=True)
        
        # Botão de Excluir
        if r[5].button("🗑️", key=f"del_{row['id']}"):
            c.execute("DELETE FROM equipamentos WHERE id=?", (row['id'],))
            conn.commit()
            st.rerun()

        st.write("---")
else:
    st.info("Nenhum equipamento cadastrado, Clenio.")
