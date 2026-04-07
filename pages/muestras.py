import pandas as pd

# 1. Cargamos el archivo (asegúrate de que el nombre coincida)
file_path = 'traspasos_consumo.xlsx'
df = pd.read_excel(file_path)

# 2. Definimos cuáles son las columnas de información fija
columnas_fijas = ['DESCRIPCION', 'CODIGO']

# 3. Transformamos la tabla (Melt)
# Esto pasará las ciudades a una sola columna llamada 'nombre del envio'
df_unpivoted = df.melt(
    id_vars=columnas_fijas, 
    var_name='nombre del envio', 
    value_name='cantidad'
)

# 4. Quitamos los que están en cero o vacíos (NaN)
df_final = df_unpivoted[df_unpivoted['cantidad'] > 0].copy()

# 5. Reordenamos y renombramos las columnas para que queden como pediste
df_final = df_final[['nombre del envio', 'DESCRIPCION', 'cantidad']]
df_final.columns = ['nombre del envio', 'descripcion producto', 'cantidad']

# 6. Guardamos el resultado
df_final.to_excel('carga_lista.xlsx', index=False)

print("¡Listo, amor! Tu archivo para cargar ya quedó filtrado y ordenado.")
  







































