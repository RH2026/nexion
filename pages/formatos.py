import streamlit as st
import pandas as pd
import io

# --- FUNCIÓN DE LIMPIEZA INTELIGENTE ---
def limpiar_excel_logistica(file_bytes, nombres_clave):
    """
    Busca la fila que contiene los encabezados reales y recorta el Excel.
    nombres_clave: Lista de palabras que deben estar en la fila de encabezados (ej: ['TALON', 'GUIA']).
    """
    try:
        # Cargamos todo el archivo sin encabezados para explorar
        df_sucio = pd.read_excel(file_bytes, header=None)
        
        fila_encabezado = -1
        
        # Recorremos las primeras 50 filas buscando las claves
        for i, row in df_sucio.head(50).iterrows():
            row_str = row.astype(str).str.lower().tolist()
            # Si encontramos al menos dos claves de las que buscamos en esa fila
            if sum(1 for clave in nombres_clave if clave.lower() in row_str) >= 1:
                fila_encabezado = i
                break
        
        if fila_encabezado != -1:
            # Re-leemos el Excel, ahora sí con la fila correcta como header
            df_limpio = pd.read_excel(file_bytes, header=fila_encabezado)
            return df_limpio
        else:
            # Si no encontramos las claves, devolvemos el original por si acaso
            return pd.read_excel(file_bytes)
            
    except Exception as e:
        st.error(f"Error limpiando el archivo: {e}")
        return None


# --- SECCIÓN DE RASTREO INTELIGENTE ---
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
        try:
            nombre = archivo.name.upper()
            
            # Leemos los bytes del archivo para que la limpieza funcione
            file_bytes = io.BytesIO(archivo.read())
            
            # Definimos qué buscar para cada archivo
            if "T1" in nombre:
                claves = ['CARTA_PORTE', 'FACTURA_INTERNA']
            elif "T2" in nombre:
                claves = ['TALON', 'OBSERVACION 1']
            else:
                claves = ['GUIA', 'FACTURA'] # Genéricas por si acaso
            
            # Limpiamos el archivo antes de guardarlo
            df_temp = limpiar_excel_logistica(file_bytes, claves)
            
            if df_temp is not None:
                base_datos_guias[nombre] = df_temp
                st.success(f"✅ {nombre} cargado y limpiado.")
        except Exception as e:
            st.error(f"Error procesando {archivo.name}: {e}")

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
                
                # --- Lógica específica por archivo (Ahora con columnas LIMPIAS) ---
                if "T1" in nombre_archivo: # Tiny Pack
                    # Usamos .get() para evitar errores si no encuentra la columna exacta
                    guia = fila.get("CARTA_PORTE", "No encontrada")
                    factura = fila.get("FACTURA_INTERNA", "No encontrada")
                elif "T2" in nombre_archivo: # Tres Guerras
                    guia = fila.get("TALON", "No encontrada")
                    factura = fila.get("OBSERVACION 1", "No encontrada")
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
                    st.dataframe(df[mask], use_container_width=True, hide_index=True)

    if not encontrado:
        st.warning("No se encontró ninguna coincidencia.")

























































































































































