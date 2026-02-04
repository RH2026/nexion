import streamlit as st
import pandas as pd
import math

# Configuración de página con el estilo de NEXION
st.set_page_config(page_title="NEXION - Simulador de Tarimas", layout="wide")

st.title("📦 Simulador Visual de Tarimas (Versión Streamlit)")

# 1. Parámetros en el Sidebar
with st.sidebar:
    st.header("Parámetros de Tarima")
    largo = st.number_input("Largo (m)", value=1.20)
    ancho = st.number_input("Ancho (m)", value=1.00)
    alto_max = st.number_input("Altura Máxima (m)", value=1.70)
    altura_base = st.number_input("Altura Base/Pallet (m)", value=0.15)
    eficiencia = st.number_input("Factor Eficiencia", value=0.85)

    # Cálculo del volumen útil
    vol_util = (largo * ancho * (alto_max - altura_base)) * eficiencia
    st.info(f"Volumen útil por tarima: {vol_util:.3f} m³")

# 2. Carga de Archivo (MATRIZ.csv)
uploaded_file = st.file_uploader("Sube tu archivo MATRIZ.csv", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # Lógica de procesamiento (Similar a lo que hacías en JS)
    # 1. Expandir productos según cantidad
    lista_unidades = []
    for _, row in df.iterrows():
        for _ in range(int(row['Cantidad a enviar'])):
            lista_unidades.append({
                'ItemCode': row['ItemCode'],
                'Peso': row['Peso/caja (kg)'],
                'Volumen': row['Volumen/caja (m3)'],
                'Densidad': row['kg/dm3']
            })
    
    # 2. Ordenar por densidad para estabilidad (Pesado abajo)
    lista_unidades.sort(key=lambda x: x['Densidad'], reverse=True)

    # 3. Algoritmo de llenado
    tarimas = []
    tarima_actual = []
    vol_acumulado = 0
    
    for caja in lista_unidades:
        if vol_acumulado + caja['Volumen'] <= vol_util:
            tarima_actual.append(caja)
            vol_acumulado += caja['Volumen']
        else:
            tarimas.append(tarima_actual)
            tarima_actual = [caja]
            vol_acumulado = caja['Volumen']
    
    if tarima_actual:
        tarimas.append(tarima_actual)

    # 3. Visualización de Resultados
    st.subheader(f"Tarimas Generadas: {len(tarimas)}")
    
    cols = st.columns(2) # Mostrar en dos columnas como en tu web
    for i, tarima in enumerate(tarimas):
        with cols[i % 2]:
            st.write(f"### TARIMA {i+1}")
            df_tarima = pd.DataFrame(tarima)
            resumen = df_tarima.groupby('ItemCode').agg({
                'ItemCode': 'count',
                'Peso': 'sum',
                'Volumen': 'sum'
            }).rename(columns={'ItemCode': 'Cant. Cajas'})
            
            st.dataframe(resumen, use_container_width=True)
            
            # Aquí podrías meter un gráfico de barras apiladas con Plotly 
            # para simular la vista visual de las capas.
            st.progress(min(df_tarima['Volumen'].sum() / vol_util, 1.0))
