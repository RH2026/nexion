import streamlit as st
import pandas as pd
import unicodedata

# 1. CONFIGURACIÓN DE PÁGINA (Debe ser lo primero)
st.set_page_config(page_title="Nexion - Dashboard Logístico", layout="wide")

# Función Maestra para limpiar nombres de columnas (Quita acentos, espacios y pone Mayúsculas)
def limpiar_columnas(txt):
    if not isinstance(txt, str): return txt
    # Normaliza y elimina acentos (ej: Í -> I)
    texto_limpio = ''.join(c for c in unicodedata.normalize('NFD', txt)
                          if unicodedata.category(c) != 'Mn')
    return texto_limpio.strip().upper()

st.title("🚀 NEXION: Gestión Logística JYPESA")
st.markdown("---")

# 2. CARGA DE DATOS
try:
    # Cargamos tus dos archivos CSV
    df_actual = pd.read_csv('Matriz_Excel_Dashboard.csv')
    df_2025 = pd.read_csv('Historial2025.csv')

    # Aplicamos la limpieza a todas las columnas de ambas matrices
    df_actual.columns = [limpiar_columnas(c) for c in df_actual.columns]
    df_2025.columns = [limpiar_columnas(c) for c in df_2025.columns]

    # 3. PROCESAMIENTO Y CRUCE DE DATOS
    # Extraemos solo lo necesario de 2025 para comparar
    # (Asegúrate que en Historial2025.csv las columnas se llamen MES y COSTO DE LA GUIA)
    df_2025_ref = df_2025[['MES', 'COSTO DE LA GUIA']].rename(columns={'COSTO DE LA GUIA': 'GUIA_2025'})
    
    # Unimos la matriz actual con la de 2025 por el MES
    df_final = pd.merge(df_actual, df_2025_ref, on='MES', how='left')

    # 4. CÁLCULOS DE INDICADORES (KPIs)
    # Llenamos vacíos en COSTOS ADICIONALES con 0 para que no truene la suma
    df_final['COSTOS ADICIONALES'] = df_final.get('COSTOS ADICIONALES', 0).fillna(0)
    
    # Fórmulas solicitadas
    df_final['COSTO DE FLETE'] = df_final['COSTO DE LA GUIA'] + df_final['COSTOS ADICIONALES']
    df_final['COSTO LOGISTICO'] = (df_final['COSTO DE FLETE'] / df_final['FACTURACION']) * 100
    df_final['COSTO POR CAJA'] = df_final['COSTO DE FLETE'] / df_final['CAJAS']
    
    # Incrementos vs 2025
    df_final['INCREMENTO_VALOR'] = df_final['COSTO DE FLETE'] - df_final['GUIA_2025']
    df_final['% INCREMENTO VS 2025'] = (df_final['INCREMENTO_VALOR'] / df_final['GUIA_2025']) * 100

    # 5. RENDERIZADO VISUAL (EL "DISEÑO CHINGÓN")
    
    # FILA 1: Tarjetas de Métricas
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        total_flete = df_final['COSTO DE FLETE'].sum()
        # El delta indica cuánto subió el flete vs el año pasado en promedio
        avg_inc = df_final['% INCREMENTO VS 2025'].mean()
        st.metric("Total Fletes 2026", f"${total_flete:,.2f}", delta=f"{avg_inc:.1f}% vs 2025", delta_color="inverse")
    
    with m2:
        total_fact = df_final['FACTURACION'].sum()
        st.metric("Facturación Total", f"${total_fact:,.2f}")
        
    with m3:
        cl_promedio = df_final['COSTO LOGISTICO'].mean()
        st.metric("% Costo Logístico", f"{cl_promedio:.2f}%")
        
    with m4:
        total_cajas = df_final['CAJAS'].sum()
        st.metric("Cajas Enviadas", f"{total_cajas:,.0f}")

    st.markdown("---")

    # FILA 2: Buscador y Tabla Principal
    st.subheader("📋 Detalle de Matriz de Operaciones")
    
    col_busq, col_esp = st.columns([2, 2])
    with col_busq:
        search = st.text_input("🔍 Filtrar por Cliente, Destino o Fletera:")

    # Aplicamos filtro de búsqueda si el usuario escribe algo
    if search:
        mask = df_final.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
        df_display = df_final[mask]
    else:
        df_display = df_final

    # Formato de la tabla para que se vea profesional
    st.dataframe(
        df_display.style.format({
            'COSTO DE LA GUIA': '${:,.2f}',
            'COSTO DE FLETE': '${:,.2f}',
            'FACTURACION': '${:,.2f}',
            'COSTO LOGISTICO': '{:.2f}%',
            'COSTO POR CAJA': '${:,.2f}',
            '% INCREMENTO VS 2025': '{:.2f}%'
        }).highlight_max(axis=0, subset=['COSTO LOGISTICO'], color='#FFAAAA'), # Resalta el costo logístico más alto
        use_container_width=True,
        height=400
    )

    # FILA 3: Análisis Gráfico
    st.markdown("### 📊 Comparativa Mensual: 2026 vs 2025")
    # Agrupamos por mes para la gráfica
    chart_data = df_final.groupby('MES')[['COSTO DE FLETE', 'GUIA_2025']].sum()
    st.area_chart(chart_data)

except FileNotFoundError:
    st.error("❌ ¡Amor! No encuentro los archivos CSV. Asegúrate que 'Matriz_Excel_Dashboard.csv' y 'Historial2025.csv' estén en la misma carpeta que este script.")
except Exception as e:
    st.error(f"❌ Error inesperado: {e}")
    st.info("Tip: Revisa que las columnas FACTURACION, CAJAS y COSTO DE LA GUIA existan en tus archivos.")















































































































