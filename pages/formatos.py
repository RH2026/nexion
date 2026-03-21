import streamlit as st
import pandas as pd

# --- SECCIÓN DE RASTREO INTELIGENTE ---
st.header("🔍 Rastreo Inteligente Multicliente")

# 1. CARGA DE ARCHIVOS (Directo en el cuerpo de la app)
archivos_paqueteria = st.file_uploader(
    "Suelta aquí tus reportes de Tiny Pack (T1) y Tres Guerras (T2):", 
    type=['xlsx'], 
    accept_multiple_files=True
)

# Diccionario para guardar lo que subas temporalmente
base_datos_guias = {}

if archivos_paqueteria:
    for archivo in archivos_paqueteria:
        try:
            # Cargamos cada Excel en un DataFrame
            nombre = archivo.name.upper()
            df_temp = pd.read_excel(archivo)
            base_datos_guias[nombre] = df_temp
            st.success(f"✅ {nombre} cargado correctamente.")
        except Exception as e:
            st.error(f"Error al leer {archivo.name}: {e}")

st.markdown("---")

# 2. MOTOR DE BÚSQUEDA
busqueda = st.text_input("Escribe el Pedido, Factura o Guía que buscas:")

if busqueda and base_datos_guias:
    encontrado = False
    
    for nombre_archivo, df in base_datos_guias.items():
        # Convertimos todo a texto para buscar sin errores de formato
        df_str = df.astype(str)
        
        # Buscamos en todas las celdas (Case insensitive)
        mask = df_str.apply(lambda x: x.str.contains(busqueda, case=False, na=False)).any(axis=1)
        resultados = df[mask]
        
        if not resultados.empty:
            encontrado = True
            st.subheader(f"📍 Encontrado en: {nombre_archivo}")
            
            # Mostramos los resultados en una tabla limpia
            st.dataframe(resultados, use_container_width=True, hide_index=True)
            
            # Bonus: Intentar resaltar la guía si existe la columna
            for col in resultados.columns:
                if 'guia' in col.lower() or 'rastreo' in col.lower() or 'tracking' in col.lower():
                    valor_guia = resultados.iloc[0][col]
                    st.info(f"🚀 **Número de Guía detectado:** {valor_guia}")
    
    if not encontrado:
        st.warning("No se encontró ese dato en los archivos cargados.")

elif busqueda and not base_datos_guias:
    st.info("Primero sube los archivos de Excel para poder buscar.")

























































































































































