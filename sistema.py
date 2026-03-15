import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

# --- CONFIGURAÇÃO E BANCO DE DADOS ---
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
    df['data_vencimento_dt'] = pd.to_datetime(df['data_vencimento']).dt.date
    hoje = date.today()
    df['dias_restantes'] = df['data_vencimento_dt'].apply(lambda x: (x - hoje).days)
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
        df = df[df['certificado'].str.contains(busca, case=False) | df['nome'].str.contains(busca, case=False)]

    st.subheader("📋 Lista de Prioridades")

    c_head = st.columns([2, 2, 1.5, 1.5, 1, 1.2])
    c_head[0].write("**Equipamento**")
    c_head[1].write("**Certificado**")
    c_head[2].write("**Vencimento**")
    c_head[3].write("**Prazo**")
    c_head[4].write("**Status**")
    c_head[5].write("**Ações**")
    st.divider()

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
        
        c_edit, c_del = r[5].columns(2)
        if c_edit.button("📝", key=f"btn_edit_{row['id']}"):
            st.session_state[f"edit_{row['id']}"] = True
        if c_del.button("🗑️", key=f"btn_del_{row['id']}"):
            st.session_state[f"del_confirm_{row['id']}"] = True

        if st.session_state.get(f"edit_{row['id']}", False):
            with st.form(key=f"form_edit_{row['id']}"):
                st.write(f"🔧 **Atualizar:** {row['nome']}")
                f1, f2, f3 = st.columns([2, 1, 1])
                novo_cert = f1.text_input("Novo Certificado", value=row['certificado'])
                data_cal_padrao = datetime.strptime(row['data_calibracao'], '%Y-%m-%d').date()
                nova_data_cal = f2.date_input("Nova Data de Calibração", value=data_cal_padrao, format="DD/MM/YYYY")
                nova_data_venc = f3.date_input("Nova Data de Expiração", value=row['data_vencimento_dt'], format="DD/MM/YYYY")
                
                b1, b2 = st.columns([1, 6])
                if b1.form_submit_button("✅ Salvar"):
                    c.execute("UPDATE equipamentos SET certificado=?, data_calibracao=?, data_vencimento=? WHERE id=?", 
                              (novo_cert, str(nova_data_cal), str(nova_data_venc), row['id']))
                    conn.commit()
                    st.session_state[f"edit_{row['id']}"] = False
                    st.rerun()
                if b2.form_submit_button("❌ Sair"):
                    st.session_state[f"edit_{row['id']}"] = False
                    st.rerun()

        if st.session_state.get(f"del_confirm_{row['id']}", False):
            with st.container(border=True):
                st.warning(f"Excluir **{row['nome']}**?")
                col_sim, col_nao = st.columns([1, 8])
                if col_sim.button("Sim, excluir", key=f"conf_sim_{row['id']}"):
                    c.execute("DELETE FROM equipamentos WHERE id=?", (row['id'],))
                    conn.commit()
                    st.rerun()
                if col_nao.button("Não", key=f"conf_nao_{row['id']}"):
                    st.session_state[f"del_confirm_{row['id']}"] = False
                    st.rerun()
        st.write("---")
else:
    st.info("Nenhum equipamento cadastrado, Clenio.")
