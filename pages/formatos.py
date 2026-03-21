import streamlit as st
import pandas as pd
import os

# --- FUNCIÓN PARA CARGAR DESDE REPOSITORIO ---
def cargar_desde_repo(archivo):
    if os.path.exists(archivo):
        try:
            df_preview = pd.read_excel(archivo, nrows=50, header=None)
            # Tus claves sagradas para encontrar el inicio de la tabla
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

# --- ESTILOS CSS PERSONALIZADOS (DISEÑO NEXION) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .nexion-card {
        background-color: #1e262c;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #00ffcc;
        margin-bottom: 20px;
        color: white;
        font-family: 'sans-serif';
    }
    .label { color: #8899a6; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; }
    .value { color: #ffffff; font-weight: bold; font-size: 1.1rem; }
    .guia-destacada { color: #00ffcc; font-size: 1.6rem; font-weight: bold; line-height: 1.2; }
    .estatus-badge {
        background-color: #004d40;
        color: #00ffcc;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: bold;
        float: right;
        text-transform: uppercase;
    }
    .resumen-fin { border-left: 1px solid #3d464d; padding-left: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS AUTOMÁTICA ---
df_t1 = cargar_desde_repo("T1.xlsx")
df_t2 = cargar_desde_repo("T2.xlsx")

# --- INTERFAZ ---
st.title("📦 Rastreo Inteligente JYPESA")
query = st.text_input("🔍 Ingresa Factura o Pedido para buscar Guía:", placeholder="Escribe aquí...")

if query:
    encontrado = False
    # Buscamos en los archivos del repo
    for df_source, nombre_f in [(df_t1, "Tiny Pack"), (df_t2, "Tres Guerras")]:
        if df_source is not None:
            df_str = df_source.astype(str)
            mask = df_str.apply(lambda x: x.str.contains(query, case=False, na=False)).any(axis=1)
            res = df_source[mask]
            
            if not res.empty:
                encontrado = True
                f = res.iloc[0] 
                
                # --- MAPEO INTELIGENTE (TUS REGLAS) ---
                guia = f.get("TALON") or f.get("CARTA_PORTE") or "S/N"
                factura = f.get("OBSERVACION 1") or f.get("FACTURA_INTERNA") or "S/N"
                
                # Búsqueda de Cliente (Mezclada como pediste)
                cliente = f.get("CLIENTE_DESTINO") or f.get("DESTINATARIO") or f.get("NOMBRE_CLIENTE") or "CLIENTE NO REGISTRADO"
                
                origen = f.get("ORIGEN") or "PLANTA GDL"
                destino = f.get("DESTINO") or f.get("CIUDAD") or "N/A"
                estatus = f.get("ESTATUS") or f.get("ESTATUS ENTREGA") or "PROCESANDO"
                bultos = f.get("BULTOS") or f.get("PIEZAS") or "0"
                
                # Búsqueda de Importe (Si Total está vacío, usa Subtotal o Cargo)
                importe = f.get("TOTAL") or f.get("SUBTOTAL") or f.get("TOTAL_CARGO") or f.get("IMPORTE") or "0.00"

                # --- RENDERIZADO DE LA TARJETA ---
                st.markdown(f"""
                <div class="nexion-card">
                    <div class="estatus-badge">{estatus}</div>
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="flex: 1;">
                            <div class="label">TALÓN / FOLIO</div>
                            <div class="guia-destacada">{guia}</div>
                            <div class="label" style="margin-top:5px;">REF: <span style="color:white; font-size:1rem;">{factura}</span></div>
                        </div>
                        
                        <div style="flex: 2; margin: 0 30px;">
                            <div class="label">DESTINATARIO / RUTA</div>
                            <div class="value" style="font-size: 1.2rem;">{cliente}</div>
                            <div style="font-size: 0.9rem; color: #8899a6; margin-top:5px;">
                                <span style="color:#00ffcc;">📍</span> {origen} ➔ {destino}
                            </div>
                        </div>
                        
                        <div class="resumen-fin" style="flex: 1;">
                            <div class="label">RESUMEN FINANCIERO</div>
                            <div class="value" style="font-size: 0.95rem;">BULTOS: <span style="color:#00ffcc;">{bultos}</span></div>
                            <div class="value" style="font-size: 1.2rem; margin-top:10px; color: #00ffcc;">$ {importe}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    if not encontrado:
        st.warning(f"No se encontró información para: {query}")
























































































































































