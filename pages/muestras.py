import pandas as pd

# 1. Leemos tus dos archivos (asegúrate de poner el nombre correcto de tus columnas)
# Supongamos que las columnas se llaman: 'Factura', 'Guia', 'Costo'
df_matriz = pd.read_excel('matriz.xlsx')
df_tg = pd.read_excel('tresguerras.xlsx')

# 2. Hacemos el "Match" uniendo ambos archivos por Factura y Guía
# Usamos how='outer' para no perder ningún registro, aunque falte en un lado.
# El parámetro 'indicator=True' nos dirá de dónde viene cada fila.
df_match = pd.merge(
    df_matriz, 
    df_tg, 
    on=['Factura', 'Guia'], 
    how='outer', 
    suffixes=('_Matriz', '_TG'),
    indicator=True
)

# 3. Creamos una nueva columna para decirle a mi amor exactamente qué pasó
def revisar_estatus(fila):
    if fila['_merge'] == 'left_only':
        return 'Falta en reporte Tresguerras'
    elif fila['_merge'] == 'right_only':
        return 'Falta en tu Matriz'
    elif fila['Costo_Matriz'] == fila['Costo_TG']:
        return '¡Cuadra perfecto!'
    else:
        return f"Diferencia de costo: Matriz(${fila['Costo_Matriz']}) vs TG(${fila['Costo_TG']})"

df_match['Estatus_Match'] = df_match.apply(revisar_estatus, axis=1)

# 4. Guardamos el resultado hermoso y digerido en un nuevo Excel
# Filtramos la columna _merge que ya no necesitamos
df_resultado = df_match.drop(columns=['_merge'])
df_resultado.to_excel('Resultado_Match_Amor.xlsx', index=False)

print("¡Listo, mi vida! Tu reporte de diferencias está guardado como 'Resultado_Match_Amor.xlsx'")






































