import pandas as pd

# 1. Cargamos tus matrices
df_actual = pd.read_csv('Matriz_Excel_Dashboard.csv')
df_2025 = pd.read_csv('Historial2025.csv')

# Limpiamos nombres de columnas por si tienen espacios (pasa mucho en Excel)
df_actual.columns = df_actual.columns.str.strip()
df_2025.columns = df_2025.columns.str.strip()

# 2. Renombramos columnas de 2025 para no confundir al unir
df_2025 = df_2025.rename(columns={
    'COSTO DE LA GUÍA': 'COSTO_GUIA_2025',
    'CAJAS': 'CAJAS_2025'
})

# 3. Unimos los datos por MES
# Nota: Asegúrate que el nombre del mes esté escrito igual (ej. "Enero")
df_final = pd.merge(df_actual, df_2025[['MES', 'COSTO_GUIA_2025']], on='MES', how='left')

# 4. CALCULAMOS TUS INDICADORES
# --- Costo de Flete Total ---
df_final['COSTO DE FLETE'] = df_final['COSTO DE LA GUÍA'] + df_final['COSTOS ADICIONALES'].fillna(0)

# --- Costo Logístico (%) ---
df_final['COSTO LOGISTICO'] = (df_final['COSTO DE FLETE'] / df_final['FACTURACION']) * 100

# --- Costo por Caja ---
df_final['COSTO POR CAJA'] = df_final['COSTO DE FLETE'] / df_final['CAJAS']

# --- % de Incidencias ---
# Marcamos como incidencia cualquier cosa que NO sea "ENTREGADO OK" (o lo que tú prefieras)
df_final['ES_INCIDENCIA'] = df_final['INCIDENCIAS'].apply(lambda x: 1 if str(x).upper() != 'ENTREGADO OK' else 0)
porcentaje_incidencias = (df_final['ES_INCIDENCIA'].sum() / len(df_final)) * 100

# --- Incrementos vs 2025 ---
df_final['INCREMENTO_MONTO'] = df_final['COSTO DE FLETE'] - df_final['COSTO_GUIA_2025']
df_final['% DE INCREMENTO VS 2025'] = (df_final['INCREMENTO_MONTO'] / df_final['COSTO_GUIA_2025']) * 100

# 5. Guardamos el resultado para Nexion
df_final.to_csv('Matriz_Nexion_Final.csv', index=False)
print("¡Listo, amor! Matriz procesada con éxito.")












































































































