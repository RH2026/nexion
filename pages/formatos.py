import streamlit as st
import pandas as pd
import os

# --- FUNCIÓN PARA CARGAR DESDE REPOSITORIO ---
def cargar_desde_repo(archivo):
    if os.path.exists(archivo):
        try:
            # Intentamos detectar la fila de encabezados automáticamente
            df_preview = pd.read_excel(archivo, nrows=50, header=None)
            claves = ['CARTA_PORTE', 'FACTURA_INTERNA', 'TALON', 'OBSERVACION 1']
            fila_head = -1
            for i, row in df_preview.iterrows():
                if any(clave in str(celda).upper() for celda in row for clave in claves):
                    fila_head = i
                    break
            
            return pd.read_excel(archivo, header=fila_head if fila_head != -1 else 0)
        except:
            return None
    return None

# --- ESTILOS CSS PARA EL RENDER "PERRO" ---
st.markdown("""
    <style>
    .nexion-card {
        background-color: #1e262c;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #00ffcc;
        margin-bottom: 20px;
        color: white;
        font-family: 'sans-serif';
    }
    .label { color: #8899a6; font-size: 0.8rem; text-transform: uppercase; }
    .value { color: #ffffff; font-weight: bold; font-size: 1.1rem; }
    .guia-destacada { color: #00ffcc; font-size: 1.5rem; font-weight: bold; }
    .estatus-badge {
        background-color: #004d40;
        color: #00ffcc;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        float: right;
    }
    .resumen-fin { border-left: 1px solid #3d464d; padding-left: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE DATOS ---
# Cargamos los archivos que ya deben estar en tu repo
df_t1 = cargar_desde_repo("T1.xlsx")
df_t2 = cargar_desde_repo("T2.xlsx")

# --- INTERFAZ ---
st.title("📦 Rastreo Inteligente")
query = st.text_input("Ingresa Factura o Pedido para buscar Guía:", placeholder="Ej. 235225")

if query:
    encontrado = False
    # Buscamos en ambos DataFrames
    for df_source, nombre_f in [(df_t1, "Tiny Pack"), (df_t2, "Tres Guerras")]:
        if df_source is not None:
            df_str = df_source.astype(str)
            mask = df_str.apply(lambda x: x.str.contains(query, case=False, na=False)).any(axis=1)
            res = df_source[mask]
            
            if not res.empty:
                encontrado = True
                f = res.iloc[0] # Tomamos la fila
                
                # Mapeo de columnas según tus reglas
                guia = f.get("TALON") or f.get("CARTA_PORTE") or "S/N"
                factura = f.get("OBSERVACION 1") or f.get("FACTURA_INTERNA") or "S/N"
                cliente = f.get("DESTINATARIO") or f.get("NOMBRE_CLIENTE") or "CLIENTE NO REGISTRADO"
                origen = f.get("ORIGEN") or "PLANTA"
                destino = f.get("DESTINO") or f.get("CIUDAD") or "N/A"
                estatus = f.get("ESTATUS") or f.get("ESTATUS ENTREGA") or "EN TRÁNSITO"
                bultos = f.get("BULTOS") or f.get("PIEZAS") or "0"
                importe = f.get("TOTAL_CARGO") or f.get("IMPORTE") or "0.00"

                # --- RENDERIZADO TIPO DASHBOARD ---
                st.markdown(f"""
                <div class="nexion-card">
                    <div class="estatus-badge">{estatus}</div>
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <div class="label">TALÓN / FOLIO</div>
                            <div class="guia-destacada">{guia}</div>
                            <div class="label">REF: <span style="color:white;">{factura}</span></div>
                        </div>
                        <div style="flex-grow: 1; margin: 0 40px;">
                            <div class="label">DESTINATARIO / ORIGEN-DEST</div>
                            <div class="value">{cliente}</div>
                            <div style="font-size: 0.9rem;">{origen} → {destino}</div>
                        </div>
                        <div class="resumen-fin">
                            <div class="label">RESUMEN FINANCIERO</div>
                            <div class="value">BULTOS: {bultos}</div>
                            <div class="value" style="color: #00ffcc;">TOTAL: ${importe}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    if not encontrado:
        st.error("No se encontró registro con ese número.")
























































































































































