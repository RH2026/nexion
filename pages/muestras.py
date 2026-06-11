import streamlit as st
import pandas as pd
import re
import io  # <-- ¡Importante! Nueva librería para crear archivos Excel

st.set_page_config(page_title="Nexion Conciliación", layout="wide")
st.title("Sistema de Conciliación Inteligente")
st.subheader("Paso 1: Carga y Limpieza de Datos")

# --- FUNCIÓN HELPER DE LIMPIEZA PARA TRESGUERRAS ---
def limpiar_y_explotar_tresguerras(df):
    col_guia = 'NÚMERO DE GUÍA'
    col_costo = 'COSTO DE LA GUÍA'
    col_factura = 'FACTURA'

    df_clean = df.copy()

    st.write("🔍 Iniciando limpieza del reporte de Tresguerras...")

    # A. Limpiar formato de dinero
    if df_clean[col_costo].dtype == 'object':
        df_clean[col_costo] = df_clean[col_costo].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
    df_clean[col_costo] = pd.to_numeric(df_clean[col_costo], errors='coerce').fillna(0.0)

    # B. Manejar la columna FACTURA (explotar filas)
    df_clean[col_factura] = df_clean[col_factura].fillna('').astype(str).str.strip()

    def procesar_texto_factura(text):
        if not text: return []
        text = text.replace(',', ' ')
        partes = re.split(r'\s+', text)
        
        lista_final = []
        for parte in partes:
            parte = parte.strip()
            if not parte: continue
            
            match_rango = re.search(r'^(\d+)-(\d+)$', parte)
            if match_rango:
                inicio = int(match_rango.group(1))
                fin = int(match_rango.group(2))
                for n in range(inicio, fin + 1):
                    lista_final.append(str(n))
            else:
                lista_final.append(parte)
        return lista_final

    df_clean['Factura_List'] = df_clean[col_factura].apply(procesar_texto_factura)

    # C. PRORRATEAR COSTO DE TRESGUERRAS
    df_clean['num_facturas'] = df_clean['Factura_List'].apply(len).replace(0, 1)
    df_clean[col_costo] = df_clean[col_costo] / df_clean['num_facturas']

    # D. EXPLOTAR EL DATAFRAME
    df_final = df_clean.explode('Factura_List').reset_index(drop=True)
    df_final[col_factura] = df_final['Factura_List']

    # E. LIMPIEZA FINAL
    df_final = df_final.drop(columns=['Factura_List', 'num_facturas'])
    df_final[col_costo] = df_final[col_costo].round(2)
    
    st.success("¡Reporte de Tresguerras limpio y prorrateado con éxito!")
    return df_final


# =========================================================
# === FLUJO PRINCIPAL DE STREAMLIT ===
# =========================================================

st.write("---")
col1, col2 = st.columns(2)
with col1:
    archivo_matriz = st.file_uploader("📥 Sube tu Matriz Operativa", type=["xlsx", "xls"])
with col2:
    archivo_tg = st.file_uploader("📥 Sube el reporte de Tresguerras", type=["xlsx", "xls"])

if archivo_matriz and archivo_tg:
    try:
        # Leemos los archivos
        df_matriz = pd.read_excel(archivo_matriz)
        df_tg_crudo = pd.read_excel(archivo_tg)
        
        # Limpiamos espacios invisibles en los encabezados
        df_matriz.columns = df_matriz.columns.str.strip()
        df_tg_crudo.columns = df_tg_crudo.columns.str.strip()

        # LIMPIEZA APLICADA SOLO A TRESGUERRAS
        df_tg_limpio = limpiar_y_explotar_tresguerras(df_tg_crudo)
        
        # Preparación de tu Matriz Operativa
        c_guia = 'NÚMERO DE GUÍA'
        c_fac = 'FACTURA'
        c_costo = 'COSTO DE LA GUÍA'

        # Asegurar que el costo de tu matriz sea numérico
        if df_matriz[c_costo].dtype == 'object':
            df_matriz[c_costo] = df_matriz[c_costo].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
        df_matriz[c_costo] = pd.to_numeric(df_matriz[c_costo], errors='coerce').fillna(0.0).round(2)
        
        # Asegurar que la factura de tu matriz sea texto
        df_matriz[c_fac] = df_matriz[c_fac].fillna('').astype(str).str.strip()


        # MATCH FINAL
        st.subheader("Paso 2: Ejecutando el Match y Análisis Contable")
        
        df_match = pd.merge(
            df_matriz, 
            df_tg_limpio, 
            on=[c_fac, c_guia], 
            how='outer', 
            suffixes=('_Matriz', '_TG'),
            indicator=True
        )
        
        def revisar_estatus(fila):
            if fila['_merge'] == 'left_only':
                return '🔴 Falta en reporte Tresguerras (Operación sin cobro)'
            elif fila['_merge'] == 'right_only':
                return '🔴 Falta en tu Matriz (Cobro sin registro operativo)'
            
            costo_matriz = fila[f'{c_costo}_Matriz']
            costo_tg = fila[f'{c_costo}_TG']
            
            if abs(costo_matriz - costo_tg) < 0.01: 
                return '✅ ¡Cuadra perfecto!'
            else:
                return f"⚠️ Diferencia de costo: Matriz(${costo_matriz:.2f}) vs TG(${costo_tg:.2f})"

        df_match['Estatus_Match'] = df_match.apply(revisar_estatus, axis=1)
        df_resultado = df_match.drop(columns=['_merge'])
        
        st.success("¡Conciliación completada con éxito, corazón!")
        st.dataframe(df_resultado, use_container_width=True)
        
        # =========================================================
        # LA MAGIA PREMIUM: Descargar como Excel Real (.xlsx)
        # =========================================================
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_resultado.to_excel(writer, index=False, sheet_name='Diferencias')
        
        st.download_button(
            label="📥 Descargar Reporte Completo en Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name="Conciliacion_Nexion_Final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        # =========================================================
        
    except KeyError as e:
        st.error(f"¡Ups! Asegúrate de que las columnas se llamen exactamente igual que en tu imagen. No encuentro: {e}")
    except Exception as e:
        st.error(f"Hubo un detalle inesperado: {e}")
else:
    st.info("Esperando tus archivos para hacer la magia.")














