import base64
from datetime import datetime
import io
import re
import time
import unicodedata
import requests
import pandas as pd
import pytz
import streamlit as st

from components.layout import render_layout

# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Logistics - Carga de Datos",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO Y PERMISOS
# ============================================================
render_layout(modulo_actual="CENTRO DE DATOS", submodulo_actual="CARGAR DATOS")


# ============================================================
# 3. INTERFAZ PRINCIPAL (DATA HUB PREMIUM)
# ============================================================
def main():    
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True

    tz_gdl = pytz.timezone('America/Mexico_City')

    # Estilos específicos de la consola y tarjetas de carga
    st.markdown("""
        <style>
        .hud-header {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.04) 0%, rgba(0, 0, 0, 0.3) 100%);
            border: 1px solid rgba(0, 212, 255, 0.12);
            border-left: 5px solid #00D4FF;
            padding: 24px 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            backdrop-filter: blur(12px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .node-card {
            background: linear-gradient(145deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.8) 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-top: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 14px;
            padding: 20px 22px;
            text-align: left;
            box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.3);
            transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: center;
            gap: 18px;
        }
        .node-card:hover {
            transform: translateY(-5px);
            border-color: rgba(0, 212, 255, 0.4);
            box-shadow: 0 15px 35px -5px rgba(0, 212, 255, 0.2);
            background: linear-gradient(145deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        }

        .node-icon {
            font-size: 22px;
            background: rgba(0, 0, 0, 0.4);
            width: 46px;
            height: 46px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
        }

        .node-label {
            font-size: 10px;
            color: #CBD5E1;
            letter-spacing: 2.5px;
            font-weight: 800;
            margin-bottom: 5px;
            text-transform: uppercase;
        }
        .node-value {
            font-size: 16px;
            font-weight: 900;
            color: #FFFFFF;
            letter-spacing: 0.5px;
        }

        .terminal-log {
            background: #0D1117;
            border: 1px solid #1E293B;
            border-left: 3px solid #00FFAA;
            padding: 16px 20px;
            border-radius: 8px;
            margin-bottom: 12px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            transition: all 0.2s ease;
        }
        .terminal-log:hover {
            background: #111823;
            border-left-color: #00D4FF;
        }
        </style>
    """, unsafe_allow_html=True)

    TOKEN = st.secrets.get("GITHUB_TOKEN", None)
    REPO_NAME = "RH2026/nexion"
    DASHBOARD_NAME = "Matriz_Excel_Dashboard.csv"
    CONSIGNAS_FILE = "consignas.csv" 
    PEDIDOS_FILE = "pedidos.csv" 
    MATRICES_EXCEL = ["T1.xlsx", "T2.xlsx", "T3.xlsx", "TGG.xlsx"]
    TODOS_LOS_PERMITIDOS = [DASHBOARD_NAME, CONSIGNAS_FILE, PEDIDOS_FILE] + MATRICES_EXCEL

    # Header Visual
    st.markdown('''
        <div class="hud-header">
            <div>
                <h2 style="margin:0; color:#FFFFFF; font-size: 22px; font-weight: 900; letter-spacing: 1.5px; text-shadow: 0 2px 10px rgba(0,0,0,0.5);">CENTRAL DATA HUB</h2>
                <p style="margin:2px 0 0 0; color:#00D4FF; font-size:10px; letter-spacing: 4px; font-weight: 700; opacity: 0.9;">NEXION LOGISTIC NODE // MULTIPLE UPLINK</p>
            </div>
        </div>
    ''', unsafe_allow_html=True)

    # Tarjetas de Estado (Nodos)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'''
            <div class="node-card">
                <div class="node-icon">📦</div>
                <div>
                    <div class="node-label">Repository Node</div>
                    <div class="node-value" style="color:#00D4FF;">{REPO_NAME.split("/")[1].upper()}</div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
    with c2:
        st.markdown('''
            <div class="node-card">
                <div class="node-icon">⚡</div>
                <div>
                    <div class="node-label">Active Protocol</div>
                    <div class="node-value">BATCH // SYNC</div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
    with c3:
        color_token = "#00FFAA" if TOKEN else "#FF453A"
        icon_token = "🔐" if TOKEN else "🔓"
        st.markdown(f'''
            <div class="node-card">
                <div class="node-icon">{icon_token}</div>
                <div>
                    <div class="node-label">Token Auth</div>
                    <div class="node-value" style="color:{color_token}; text-shadow: 0 0 10px {color_token}40;">{"ENCRYPTED" if TOKEN else "MISSING"}</div>
                </div>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("<div style='margin: 25px 0;'></div>", unsafe_allow_html=True)

    # Área de Carga Múltiple
    with st.container(border=True):
        st.markdown("<h4 style='color: white; font-weight: 700; font-size: 16px; letter-spacing: 1px;'>SECURE MULTI-UPLINK</h4>", unsafe_allow_html=True)
        st.caption(f"Accepted Assets: `{DASHBOARD_NAME}`, `{CONSIGNAS_FILE}`, `{PEDIDOS_FILE}` and `T1, T2, T3, TGG` (XLSX)")

        uploaded_files = st.file_uploader("", type=["csv", "xlsx"], accept_multiple_files=True, key="multi_uploader")

        if uploaded_files:
            archivos_validos = []
            errores = False

            for uploaded_file in uploaded_files:
                if uploaded_file.name not in TODOS_LOS_PERMITIDOS:
                    st.markdown(f"""
                        <div style="background: rgba(255, 69, 58, 0.08); border: 1px solid #FF453A; border-left: 4px solid #FF453A; border-radius: 8px; padding: 15px 20px; margin-bottom: 15px; display: flex; align-items: center; gap: 15px;">
                            <div style="font-size: 24px;">⚠️</div>
                            <div>
                                <strong style="color: #FF453A; font-size: 13px; letter-spacing: 1px; text-transform: uppercase;">CRITICAL: PROTOCOL VIOLATION</strong><br>
                                <span style="color: #FFFFFF; font-size: 13px;">Asset no autorizado: <span style="color: white; font-weight: 700;">{uploaded_file.name}</span></span><br>
                                <small style="color: #FF453A; opacity: 0.9; font-weight: 600;">[ SYSTEM ACTION: UPLINK BLOCKED ]</small>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    errores = True
                else:
                    archivos_validos.append(uploaded_file)

            if archivos_validos and not errores:
                with st.expander("📋 Lote preparado para Sincronización", expanded=True):
                    for f in archivos_validos:
                        st.markdown(f"<div style='color: #00FFAA; font-size: 13px; margin-bottom: 5px; font-weight: 600;'>✓ Asset Validado: <span style='color: white;'>{f.name}</span></div>", unsafe_allow_html=True)

                hora_actual_gdl = datetime.now(tz_gdl).strftime('%d/%m/%Y %H:%M')
                commit_msg = st.text_input("Global Sync Message", value=f"BATCH_UPDATE // {hora_actual_gdl}")

                if st.button("EXECUTE GLOBAL SINCRONIZATION", type="primary", use_container_width=True):
                    with st.status("Iniciando Batch Uplink hacia la matriz...", expanded=True) as status:
                        try:
                            from github import Github
                            g = Github(TOKEN)
                            repo = g.get_repo(REPO_NAME)

                            for f in archivos_validos:
                                status.write(f"Sincronizando nodo: `{f.name}`...")
                                content = f.getvalue()
                                try:
                                    target = repo.get_contents(f.name)
                                    repo.update_file(target.path, commit_msg, content, target.sha)
                                except:
                                    repo.create_file(f.name, commit_msg, content)

                            status.update(label="Assets Sincronizados Correctamente", state="complete", expanded=False)
                            st.toast("Matriz Nexion Actualizada", icon="🛡️")
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            status.update(label=f"Fallo en Uplink: {str(e)}", state="error")

    # Logs del Sistema (Terminal)
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("💻 SYSTEM AUDIT LOGS (GITHUB COMMITS)", expanded=False):
        if TOKEN:
            try:
                from github import Github
                g = Github(TOKEN)
                repo = g.get_repo(REPO_NAME)
                
                commits = repo.get_commits()
                commits_filtrados = []
                
                for c in commits:
                    if "Registro de acceso" not in c.commit.message:
                        commits_filtrados.append(c)
                    if len(commits_filtrados) == 10:
                        break
                
                if not commits_filtrados:
                    st.markdown("<div class='terminal-log' style='color:#CBD5E1;'>No hay cargas de datos recientes.</div>", unsafe_allow_html=True)
                else:
                    for commit in commits_filtrados:
                        fecha_utc = commit.commit.author.date.replace(tzinfo=pytz.utc)
                        fecha_local = fecha_utc.astimezone(tz_gdl)
                        
                        st.markdown(f"""
                            <div class="terminal-log">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                    <span style="color: #94A3B8; font-size: 11px; font-weight: 700;">[{fecha_local.strftime('%d/%m/%Y %H:%M:%S')}]</span>
                                    <span style="color: #38BDF8; font-size: 11px; font-weight: 700;">SHA: {commit.sha[:8]}</span>
                                </div>
                                <div style="color: #F8FAFC; font-size: 13px; font-weight: 700; margin-bottom: 6px; line-height: 1.4;">
                                    <span style="color: #00FFAA;">></span> {commit.commit.message}
                                </div>
                                <div style="color: #94A3B8; font-size: 10px; font-weight: 800; letter-spacing: 1px;">
                                    AUTHORIZED_AGENT: <span style="color: #FFFFFF;">{commit.commit.author.name}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error de conexión con la terminal de logs: {e}")

if __name__ == "__main__":
    main()
