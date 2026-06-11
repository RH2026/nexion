import streamlit as st
import pandas as pd
import re # Necesario para la limpieza avanzada de textos

st.set_page_config(page_title="Nexion Conciliación", layout="wide")
st.title("Sistema de Conciliación Inteligente")
st.subheader("Paso 1: Carga y Limpieza de Datos")

# --- FUNCIÓN HELPER DE LIMPIEZA AVANZADA ---
# Definimos esto arriba para que Streamlit lo tenga listo
def limpiar_y_explotar_matriz(df):
    """
    Toma la matriz operativa, limpia costos y expande/prorratea facturas
    basado en las columnas EXACTAS de la imagen.
    """
    # Nombres de columnas exactos de tu imagen
    col_guia = 'NÚMERO DE GUÍA'
    col_costo = 'COSTO DE LA GUÍA'
    col_factura = 'FACTURA'

    # Copia del dataframe para no afectar el original
    df_clean = df.copy()

    st.write("🔍 Iniciando limpieza de Matriz Operativa...")

    # A. Limpiar columna COSTO (eliminar '$', ',' y convertir a número)
    st.write("- Limpiando formato de dinero de los costos...")
    df_clean[col_costo] = df_clean[col_costo].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
    df_clean[col_costo] = pd.to_numeric(df_clean[col_costo], errors='coerce').fillna(0.0)

    # B. Manejar la columna FACTURA (explotar filas)
    st.write("- Analizando y expandiendo facturas múltiples/rangos...")
    
    # Asegurar que factura sea texto y manejar nulos
    df_clean[col_factura] = df_clean[col_factura].fillna('').astype(str).str.strip()

    # Función interna para convertir texto de factura en lista
    def procesar_texto_factura(text):
        if not text: return []
        # Reemplazar comas por espacios para estandarizar
        text = text.replace(',', ' ')
        # Dividir por cualquier secuencia de espacios
        partes = re.split(r'\s+', text)
        
        lista_final = []
        for parte in partes:
            parte = parte.strip()
            if not parte: continue
            
            # Detectar rangos numéricos puros (ej: 238914-238917)
            # Buscamos: solo dígitos - solo dígitos
            match_rango = re.search(r'^(\d+)-(\d+)$', parte)
            if match_rango:
                inicio = int(match_rango.group(1))
                fin = int(match_rango.group(2))
                # Generar el rango inclusivo
                for n in range(inicio, fin + 1):
                    lista_final.append(str(n))
            else:
                # Es factura normal o alfanumérica
                lista_final.append(parte)
        return lista_final

    # Creamos una columna temporal con la lista de facturas
    df_clean['Factura_List'] = df_clean[col_factura].apply(procesar_texto_factura)

    # C. PRORRATEAR COSTO
    st.write("- Calculando prorrateo de costos...")
    # Calcular cuántas facturas hay por fila
    df_clean['num_facturas'] = df_clean['Factura_List'].apply(len).replace(0, 1) # Evitar división por cero

    # El COSTO DE LA GUÍA será el prorrateado ANTES de explotar
    df_clean[col_costo] = df_clean[col_costo] / df_clean['num_facturas']

    # D. EXPLOTAR EL DATAFRAME
    # Ahora sí, creamos filas separadas para cada elemento en Factura_List
    df_final = df_clean.explode('Factura_List').reset_index(drop=True)

    # Reemplazamos la columna FACTURA original con el valor individual limpio
    df_final[col_factura] = df_final['Factura_List']

    # E. LIMPIEZA FINAL (eliminar columnas temporales)
    df_final = df_final.drop(columns=['Factura_List', 'num_facturas'])

    # Redondear costos a 2 decimales para evitar problemas de flotantes en contabilidad
    df_final[col_costo] = df_final[col_costo].round(2)
    
    st.success("¡Matriz limpia y prorrateada con éxito!")
    return df_final


# =========================================================
# === FLUJO PRINCIPAL DE STREAMLIT ===
# =========================================================

# 1. Cargadores de archivos interactivos
st.write("---")
col1, col2 = st.columns(2)
with col1:
    archivo_matriz = st.file_uploader("📥 Sube tu Matriz Operativa", type=["xlsx", "xls"])
with col2:
    archivo_tg = st.file_uploader("📥 Sube el reporte de Tresguerras", type=["xlsx", "xls"])

# 2. Procesamos la información cuando subas ambos archivos
if archivo_matriz and archivo_tg:
    try:
        df_matriz_crudo = pd.read_excel(archivo_matriz)
        df_tg = pd.read_excel(archivo_tg)
        
        # Limpiamos espacios invisibles en los encabezados por seguridad
        df_matriz_crudo.columns = df_matriz_crudo.columns.str.strip()
        df_tg.columns = df_tg.columns.str.strip()

        # =========================================================
        # NUEVO MODULO DE LIMPIEZA: El prorrateo de amor
        # =========================================================
        # Llamamos a nuestra función HELPER definida arriba
        df_matriz_limpia = limpiar_y_explotar_matriz(df_matriz_crudo)
        
        # Mostramos cómo quedó la matriz limpia (opcional para control)
        st.write("📈 Visualización de tu Matriz Limpia:")
        st.dataframe(df_matriz_limpia.head(10), use_container_width=True)
        # =========================================================

        # También necesitamos limpiar el costo de Tresguerras para comparar números vs números
        # Asumiendo que Tresguerras tiene la columna 'COSTO DE LA GUÍA' o similar,
        # necesitamos asegurarnos de que sea numérica.
        # Por seguridad, estandarizaremos los nombres de columnas de TG también si fallan.
        
        st.subheader("Paso 2: Ejecutando el Match y Análisis Contable")
        
        # Nombres de columnas de match de tu imagen
        c_guia = 'NÚMERO DE GUÍA'
        c_fac = 'FACTURA'
        c_costo = 'COSTO DE LA GUÍA'

        # Asegurar que TG tenga costos numéricos para comparar bien
        # (Si en TG también viene como '$...', aplicamos la misma limpieza)
        if df_tg[c_costo].dtype == 'object': # Si es texto
            df_tg[c_costo] = df_tg[c_costo].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df_tg[c_costo] = pd.to_numeric(df_tg[c_costo], errors='coerce').fillna(0.0)
        df_tg[c_costo] = df_tg[c_costo].round(2)
        # Asegurar que factura en TG sea texto para el merge
        df_tg[c_fac] = df_tg[c_fac].fillna('').astype(str).str.strip()


        # 3. Hacemos el Match usando los nombres EXACTOS y la matriz YA LIMPIA
        df_match = pd.merge(
            df_matriz_limpia, 
            df_tg, 
            on=[c_fac, c_guia], 
            how='outer', 
            suffixes=('_Matriz', '_TG'),
            indicator=True
        )
        
        # 4. Función lógica para encontrar las diferencias de costos
        # (Modificada un poco para redondear flotantes y evitar falsos positivos)
        def revisar_estatus(fila):
            if fila['_merge'] == 'left_only':
                return '🔴 Falta en reporte Tresguerras (Operación sin cobro)'
            elif fila['_merge'] == 'right_only':
                return '🔴 Falta en tu Matriz (Cobro sin registro operativo)'
            
            # Comparamos costos redondeados
            costo_matriz = fila[f'{c_costo}_Matriz']
            costo_tg = fila[f'{c_costo}_TG']
            
            # Usamos un margen de error contable muy pequeño para float precision
            if abs(costo_matriz - costo_tg) < 0.01: 
                return '✅ ¡Cuadra perfecto!'
            else:
                return f"⚠️ Diferencia de costo: Matriz(${costo_matriz:.2f}) vs TG(${costo_tg:.2f})"

        # Aplicamos la revisión fila por fila
        df_match['Estatus_Match'] = df_match.apply(revisar_estatus, axis=1)
        
        # Limpiamos la columna interna de Pandas para el resultado final
        df_resultado = df_match.drop(columns=['_merge'])
        
        st.success("¡Conciliación completada con éxito, corazón!")
        
        # 5. Mostramos el resultado en una tabla premium de Streamlit
        st.dataframe(df_resultado, use_container_width=True)
        
        # Botón elegante para que descargues el reporte listo para el contador
        # Convertir dataframe a CSV compatible con Excel español
        csv = df_resultado.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig') # Estilo Excel latino
        st.download_button(
            label="📥 Descargar Reporte de Diferencias (CSV para Excel)",
            data=csv,
            file_name="Conciliacion_Premium_Nexion.csv",
            mime="text/csv",
        )
        
    except KeyError as e:
        st.error(f"¡Ups! Asegúrate de que ambos archivos tengan las columnas escritas igual que en tu imagen. No encuentro: {e}")
    except Exception as e:
        st.error(f"Hubo un detalle inesperado durante la limpieza o el match: {e}")
else:
    st.info("Esperando a que subas ambos archivos para ejecutar el cruce de datos, mi vida. Recuerda subir la matriz de Mayo y SAP.")





































