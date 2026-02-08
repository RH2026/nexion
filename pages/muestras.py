import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Reparador Logístico", layout="wide")

st.title("🛠️ Reparador de Costos Automático")
st.markdown("Sube tu archivo y yo me encargo de encontrar las columnas, aunque tengan nombres extraños.")

uploaded_file = st.file_uploader("Sube tu Excel o CSV", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # 1. Leer archivo
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        else:
            df = pd.read_excel(uploaded_file)
        
        # Limpieza básica de nombres de columnas (quitar espacios locos)
        df.columns = [str(c).strip() for c in df.columns]

        # --- LÓGICA DE DETECCIÓN INTELIGENTE ---
        # Buscamos columnas que CONTENGAN las palabras clave
        def encontrar_columna(lista, palabra_clave):
            for c in lista:
                if palabra_clave.upper() in c.upper():
                    return c
            return lista[0] # Si no halla nada, toma la primera por defecto

        c_factura = encontrar_columna(df.columns, "FACTURA")
        c_guia = encontrar_columna(df.columns, "GUIA")
        c_costo = encontrar_columna(df.columns, "COSTO")
        c_cajas = encontrar_columna(df.columns, "CAJAS")

        st.write(f"✅ **Columnas detectadas:** Factura: `{c_factura}`, Guía: `{c_guia}`, Costo: `{c_costo}`, Cajas: `{c_cajas}`")

        if st.button("Reparar y Generar Excel"):
            res_df = df.copy()

            # Limpiar datos numéricos (quitar símbolos de pesos, comas, etc.)
            for col in [c_costo, c_cajas]:
                if res_df[col].dtype == 'object':
                    res_df[col] = res_df[col].str.replace('$', '').str.replace(',', '').str.strip()
                res_df[col] = pd.to_numeric(res_df[col], errors='coerce').fillna(0)

            # 1. Sumar cajas por guía
            df_sumas = res_df.groupby(c_guia, as_index=False)[c_cajas].sum()
            df_sumas = df_sumas.rename(columns={c_cajas: 'TOTAL_CAJAS_DE_LA_GUIA'})

            # 2. Unir y calcular
            final_df = pd.merge(res_df, df_sumas, on=c_guia, how='left')
            
            # Prorrateo: (Costo Repetido / Total Cajas) * Cajas de la Factura
            final_df['COSTO_UNITARIO_POR_CAJA'] = 0.0
            mask = final_df['TOTAL_CAJAS_DE_LA_GUIA'] > 0
            
            final_df.loc[mask, 'COSTO_UNITARIO_POR_CAJA'] = final_df.loc[mask, c_costo] / final_df.loc[mask, 'TOTAL_CAJAS_DE_LA_GUIA']
            final_df['COSTO_REAL_FILA'] = final_df['COSTO_UNITARIO_POR_CAJA'] * final_df[c_cajas]

            st.success("¡Listo! Costos corregidos.")
            st.dataframe(final_df.head(10))

            # --- DESCARGA ---
            output = BytesIO()
            # Usamos un try/except por si falla el motor de Excel, usar CSV
            try:
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    final_df.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 Descargar Excel Corregido",
                    data=output.getvalue(),
                    file_name="costos_reales_logistica.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except:
                csv = final_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Descargar como CSV (Excel lo abre)", data=csv, file_name="costos_reales.csv")

    except Exception as e:
        st.error(f"Error inesperado: {e}")




















