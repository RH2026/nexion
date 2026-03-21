import streamlit as st
import pandas as pd
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Nexion - Rastreo Inteligente", layout="wide")

# --- FUNCIÓN DE LIMPIEZA DE EXCEL (PARA QUITAR FILAS VACÍAS ARRIBA) ---
def limpiar_excel_logistica(file_bytes):
    try:
        # Cargamos el archivo para explorar las primeras filas
        df_sucio = pd.read_excel(file_bytes, header=None)
        
        # Estas son tus palabras clave sagradas para encontrar el encabezado
        claves = ['CARTA_PORTE', 'FACTURA_INTERNA', 'TALON', 'OBSERVACION 1']
        fila_encabezado = -1
        
        for i, row in df_sucio.head(50).iterrows():
            row_str = row.astype(str).str.upper().tolist()
            # Si la fila contiene alguna de tus palabras clave, ahí es
            if any(clave in str(celda) for celda in row_str for clave in claves):
                fila_encabezado = i
                break
        
        if fila_encabezado != -1:
            return pd.read_excel(file_bytes, header=fila_encabezado)
        else:
            return pd.read_excel(file_bytes) # Si no halla nada, lo abre normal
    except Exception as e:
        st.error(f"Error al limpiar archivo: {e}")
        return None

# --- INTERFAZ PRINCIPAL ---
st.title("📦 Nexion: Rastreo Inteligente Multicliente")
st.markdown("---")

# 1. CARGA DE ARCHIVOS (T1, T2 o cualquier reporte)
archivos_subidos = st.file_uploader(
    "Arrastra aquí tus reportes de Tiny Pack y Tres Guerras:", 
    type=['xlsx'], 
    accept_multiple_files=True
)

base_datos = {}

if archivos_subidos:
    for archivo in archivos_subidos:
        nombre = archivo.name.upper()
        # Limpieza y carga
        file_bytes = io.BytesIO(archivo.read())
        df_limpio = limpiar_excel_logistica(file_bytes)
        
        if df_limpio is not None:
            base_datos[nombre] = df_limpio
            st.success(f"✅ {nombre} listo para búsqueda.")

st.markdown("---")

# 2. MOTOR DE BÚSQUEDA TODOTERRENO
query = st.text_input("🔍 Ingresa número de Pedido, Factura o Guía:")

if query and base_datos:
    hallado = False
    
    for nombre_archivo, df in base_datos.items():
        # Convertimos todo a texto para buscar sin errores de formato
        df_str = df.astype(str)
        mask = df_str.apply(lambda x: x.str.contains(query, case=False, na=False)).any(axis=1)
        resultados = df[mask]
        
        if not resultados.empty:
            hallado = True
            fila = resultados.iloc[0] # Tomamos el primer resultado
            
            st.subheader(f"📍 Resultado en: {nombre_archivo}")
            
            # --- LÓGICA UNIFICADA (T1 + T2) ---
            # Buscamos columnas de GUÍA (CARTA_PORTE o TALON)
            col_guia = [c for c in df.columns if 'CARTA_PORTE' in str(c).upper() or 'TALON' in str(c).upper()]
            # Buscamos columnas de FACTURA (FACTURA_INTERNA o OBSERVACION 1)
            col_fact = [c for c in df.columns if 'FACTURA_INTERNA' in str(c).upper() or 'OBSERVACION 1' in str(c).upper()]
            
            # Extraemos los datos finales
            guia_final = fila.get(col_guia[0]) if col_guia else "No encontrada"
            factura_final = fila.get(col_fact[0]) if col_fact else "No encontrada"
            
            # Mostramos los resultados en grande (Métricas)
            c1, c2 = st.columns(2)
            with c1:
                st.metric("📦 NÚMERO DE GUÍA", guia_final)
            with c2:
                # Si es de Tres Guerras, esto será lo que hay en OBSERVACION 1
                st.metric("📄 FACTURA / REFERENCIA", factura_final)
            
            # Tabla completa por si quieres ver surtidor, fecha, etc.
            with st.expander("Ver detalles completos del envío"):
                st.dataframe(df[mask], use_container_width=True, hide_index=True)
                
    if not hallado:
        st.warning("No se encontró ninguna coincidencia en los archivos cargados.")

elif query and not base_datos:
    st.info("Por favor, sube primero los archivos de Excel.")
























































































































































