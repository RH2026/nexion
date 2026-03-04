import streamlit as st
import pandas as pd

# CONFIGURACIÓN DE PÁGINA (Si no la tienes en el main)
st.set_page_config(layout="wide")

st.title("🚀 NEXION: Dashboard Logístico JYPESA")
st.markdown("---")

# 1. CARGA DE DATOS (Asegúrate de que los archivos estén en la misma carpeta)
try:
    df_actual = pd.read_csv('Matriz_Excel_Dashboard.csv')
    df_2025 = pd.read_csv('Historial2025.csv')

    # LIMPIEZA AUTOMÁTICA DE COLUMNAS (Quita espacios, acentos y pone Mayúsculas)
    df_actual.columns = df_actual.columns.str.strip().str.upper().str.replace('Ó', 'O')
    df_2025.columns = df_2025.columns.str.strip().str.upper().str.replace('Ó', 'O')

    # 2. PROCESAMIENTO Y CÁLCULOS (En el "cerebro" de Python)
    # Unimos con el historial 2025 por MES
    df_2025_subset = df_2025[['MES', 'COSTO DE LA GUIA']].rename(columns={'COSTO DE LA GUIA': 'GUIA_2025'})
    df_final = pd.merge(df_actual, df_2025_subset, on='MES', how='left')

    # Fórmulas mágicas
    df_final['COSTO DE FLETE'] = df_final['COSTO DE LA GUIA'] + df_final['COSTOS ADICIONALES'].fillna(0)
    df_final['COSTO LOGISTICO'] = (df_final['COSTO DE FLETE'] / df_final['FACTURACION']) * 100
    df_final['COSTO POR CAJA'] = df_final['COSTO DE FLETE'] / df_final['CAJAS']
    
    # Incremento vs 2025
    df_final['INCREMENTO_VALOR'] = df_final['COSTO DE FLETE'] - df_final['GUIA_2025']
    df_final['% INCREMENTO VS 2025'] = (df_final['INCREMENTO_VALOR'] / df_final['GUIA_2025']) * 100

    # 3. RENDERIZADO CHINGÓN (Lo que tú ves en pantalla)
    
    # --- FILA 1: MÉTRICAS PRINCIPALES ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_flete = df_final['COSTO DE FLETE'].sum()
        st.metric("Total Fletes 2026", f"${total_flete:,.2f}", delta=f"{df_final['% INCREMENTO VS 2025'].mean():.1f}%", delta_color="inverse")
    
    with col2:
        total_fact = df_final['FACTURACION'].sum()
        st.metric("Facturación Total", f"${total_fact:,.2f}")
        
    with col3:
        costo_log_avg = df_final['COSTO LOGISTICO'].mean()
        st.metric("% Costo Logístico", f"{costo_log_avg:.2f}%")
        
    with col4:
        cajas_totales = df_final['CAJAS'].sum()
        st.metric("Total Cajas Enviadas", f"{cajas_totales:,.0f}")

    st.markdown("---")

    # --- FILA 2: TABLA INTERACTIVA ---
    st.subheader("📋 Detalle de Operaciones")
    # Filtro rápido por Mes o Cliente para que se vea más pro
    busqueda = st.text_input("🔍 Buscar por Cliente o Destino:")
    if busqueda:
        df_display = df_final[df_final['NOMBRE DEL CLIENTE'].str.contains(busqueda, case=False) | 
                              df_final['DESTINO'].str.contains(busqueda, case=False)]
    else:
        df_display = df_final

    # Mostramos la tabla con colores
    st.dataframe(
        df_display.style.format({
            'COSTO DE FLETE': '${:,.2f}',
            'FACTURACION': '${:,.2f}',
            'COSTO LOGISTICO': '{:.2f}%',
            '% INCREMENTO VS 2025': '{:.2f}%'
        }).highlight_max(axis=0, subset=['COSTO LOGISTICO'], color='#ff4b4b22'),
        use_container_width=True,
        height=450
    )

    # --- FILA 3: GRÁFICA RÁPIDA ---
    st.markdown("### 📈 Tendencia de Costos")
    st.line_chart(df_final.set_index('MES')[['COSTO DE FLETE', 'GUIA_2025']])

except FileNotFoundError:
    st.error("⚠️ Amor, no encontré los archivos .csv. Revisa que 'Matriz_Excel_Dashboard.csv' y 'Historial2025.csv' estén en la carpeta.")
except Exception as e:
    st.error(f"❌ Hubo un error inesperado: {e}")














































































































