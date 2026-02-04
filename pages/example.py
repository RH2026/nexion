import streamlit as st
import pandas as pd
import math
from io import BytesIO

# Configuración de NEXION
st.set_page_config(page_title="NEXION - Simulador de Tarimas", layout="wide")

# Estilos CSS para parecerse al original
st.markdown("""
    <style>
    .tarima-card {
        border: 1px solid #2A2F33;
        border-radius: 10px;
        padding: 15px;
        background-color: white;
        margin-bottom: 20px;
    }
    .header-jypesa {
        background-color: #1F3B4D;
        color: white;
        padding: 15px;
        font-size: 24px;
        font-weight: bold;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-jypesa">JYPESA: SIMULADOR VISUAL DE TARIMAS (NEXION)</div>', unsafe_allow_html=True)

# --- 1. DATOS DEL ENVÍO ---
with st.expander("0. Datos opcionales del envío", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    transfer = c1.text_input("Número de transferencia")
    destino = c2.text_input("Destino")
    fecha = c3.date_input("Fecha")
    razon = c4.text_input("Razón social")

# --- 2. PARÁMETROS Y CARGA ---
st.header("1. Parámetros y carga de CSV")
col_params_1 = st.columns(3)
largo = col_params_1[0].number_input("Largo tarima (m)", value=1.20, step=0.01)
ancho = col_params_1[1].number_input("Ancho tarima (m)", value=1.00, step=0.01)
alto_max = col_params_1[2].number_input("Altura máxima (m)", value=1.70, step=0.01)

col_params_2 = st.columns(3)
altura_base = col_params_2[0].number_input("Altura base (m)", value=0.15, step=0.01)
factor_eficiencia = col_params_2[1].number_input("Factor eficiencia", value=0.85, step=0.01)

# Cálculo de volumen útil (Exactamente como David)
util_height = max(alto_max - altura_base, 0.0)
pallet_volume_limit = largo * ancho * util_height * factor_eficiencia
col_params_2[2].metric("Volumen Útil Tarima (m³)", f"{pallet_volume_limit:.3f}")

uploaded_file = st.file_uploader("Subir MATRIZ.csv", type=["csv"])

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file)
    
    # Procesar productos (Expandir cantidades)
    productos_lista = []
    for _, row in df_raw.iterrows():
        try:
            qty = int(row['Cantidad a enviar'])
            for _ in range(qty):
                productos_lista.append({
                    'ItemCode': row['ItemCode'],
                    'Descripción': row['Descripción'],
                    'Peso': float(row['Peso/caja (kg)']),
                    'Volumen': float(row['Volumen/caja (m3)']),
                    'Densidad': float(row['kg/dm3'])
                })
        except:
            continue

    if st.button("Procesar Tarimas", type="primary"):
        # --- ALGORITMO ORIGINAL DE DAVID ---
        # 1. Ordenar por densidad ascendente
        productos_lista.sort(key=lambda x: x['Densidad'])
        
        pallets = []
        current_pallet_boxes = []
        current_vol = 0
        
        left = 0
        right = len(productos_lista) - 1
        
        def try_push(box, current_boxes, current_v, vol_limit):
            if current_v + box['Volumen'] <= vol_limit:
                current_boxes.append(box)
                return current_boxes, current_v + box['Volumen'], True
            return current_boxes, current_v, False

        # Lógica de dos punteros (Alterna ligero y pesado)
        while left <= right:
            # Intentar meter el ligero (left)
            current_pallet_boxes, current_vol, added = try_push(productos_lista[left], current_pallet_boxes, current_vol, pallet_volume_limit)
            if added:
                left += 1
            else:
                # Si no cabe, cerrar tarima y empezar nueva
                pallets.append(current_pallet_boxes)
                current_pallet_boxes = [productos_lista[left]]
                current_vol = productos_lista[left]['Volumen']
                left += 1
            
            # Intentar meter el pesado (right)
            if left <= right:
                current_pallet_boxes, current_vol, added = try_push(productos_lista[right], current_pallet_boxes, current_vol, pallet_volume_limit)
                if added:
                    right -= 1
                else:
                    pallets.append(current_pallet_boxes)
                    current_pallet_boxes = [productos_lista[right]]
                    current_vol = productos_lista[right]['Volumen']
                    right -= 1
        
        if current_pallet_boxes:
            pallets.append(current_pallet_boxes)

        # --- RENDERIZADO DE RESULTADOS ---
        st.header("2. Tarimas generadas")
        
        col_res_1, col_res_2 = st.columns(2)
        
        for idx, p_boxes in enumerate(pallets):
            target_col = col_res_1 if idx % 2 == 0 else col_res_2
            
            with target_col:
                st.markdown(f"""
                <div class="tarima-card">
                    <h3 style='color:#1F3B4D'>TARIMA {idx + 1}</h3>
                    <p><b>Cajas:</b> {len(p_boxes)} | 
                    <b>Peso:</b> {sum(b['Peso'] for b in p_boxes):.2f} kg | 
                    <b>Vol:</b> {sum(b['Volumen'] for b in p_boxes):.3f} m³</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Agrupar por Capas (Roles)
                df_p = pd.DataFrame(p_boxes)
                capas = df_p.groupby('ItemCode').agg({
                    'ItemCode': 'first',
                    'Peso': 'sum',
                    'Volumen': 'sum',
                    'Densidad': 'first',
                    'Descripción': 'count'
                }).rename(columns={'Descripción': 'Cajas'}).sort_values('Densidad', ascending=False).reset_index(drop=True)
                
                # Asignar Roles
                capas['Rol'] = ""
                if len(capas) > 0:
                    capas.loc[0, 'Rol'] = "BASE"
                    if len(capas) > 1:
                        capas.loc[len(capas)-1, 'Rol'] = "CIMA"
                
                st.dataframe(capas[['Rol', 'ItemCode', 'Cajas', 'Peso', 'Volumen']], use_container_width=True)

# --- NOTA SOBRE LOS 100 CAJAS ---
st.info("""
**Nota de Rigoberto:** Si el cálculo sigue dando más de 100 cajas, es porque matemáticamente el volumen de la caja 
en el CSV (0.016 m³) cabe esa cantidad de veces en el espacio de la tarima (1.58 m³). 
Si en la vida real no caben, revisa si el volumen en el CSV debe ser mayor o si hay un límite de peso 
(ej. 1,000kg) que debamos programar.
""")
