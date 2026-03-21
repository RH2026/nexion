import streamlit as st
import pandas as pd

st.header("🔍 Rastreo Inteligente de Guías")

# 1. Carga de Archivos
archivos_paqueteria = st.file_uploader(
    "Suelta aquí tus reportes T1 (Tiny) y T2 (Tres Guerras):", 
    type=['xlsx'], 
    accept_multiple_files=True
)

base_datos_guias = {}

if archivos_paqueteria:
    for archivo in archivos_paqueteria:
        nombre = archivo.name.upper()
        df_temp = pd.read_excel(archivo)
        base_datos_guias[nombre] = df_temp
        st.success(f"✅ {nombre} cargado.")

st.markdown("---")

# 2. Buscador
busqueda = st.text_input("Ingresa Factura o Guía para buscar:")

if busqueda and base_datos_guias:
    encontrado = False
    
    for nombre_archivo, df in base_datos_guias.items():
        # Convertimos todo a texto para buscar parejo
        df_str = df.astype(str)
        mask = df_str.apply(lambda x: x.str.contains(busqueda, case=False, na=False)).any(axis=1)
        resultados = df[mask]
        
        if not resultados.empty:
            encontrado = True
            # Tomamos la primera coincidencia
            fila = resultados.iloc[0]
            
            with st.container():
                st.subheader(f"📍 Resultado en {nombre_archivo}")
                
                # --- Lógica específica por archivo ---
                if "T1" in nombre_archivo: # Tiny Pack
                    guia = fila.get("CARTA_PORTE", "No encontrada")
                    factura = fila.get("FACTURA_INTERNA", "No encontrada")
                    fuente = "Tiny Pack"
                elif "T2" in nombre_archivo: # Tres Guerras
                    guia = fila.get("TALON", "No encontrada")
                    factura = fila.get("OBSERVACION 1", "No encontrada")
                    fuente = "Tres Guerras"
                else:
                    guia = "Archivo desconocido"
                    factura = "Archivo desconocido"
                
                # Diseño de tarjetas para los datos clave
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("NÚMERO DE GUÍA", guia)
                with col2:
                    st.metric("FACTURA / REF", factura)
                
                # Mostramos la fila completa por si quieres ver más detalles
                with st.expander("Ver todos los detalles del envío"):
                    st.write(df[mask])

    if not encontrado:
        st.warning("No se encontró ninguna coincidencia.")

























































































































































