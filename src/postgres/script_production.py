"""
Script creado por: Pablo Dueñas Fernández.
Este script carga y procesa datos de producción fotovoltaica desde un archivo CSV.
Lee el archivo de datos de producción histórica, normaliza los nombres de columnas
y prepara el DataFrame para su integración con otros datos del sistema.
"""

# Se toma el csv de la carpeta data y se pasa a un dataframe de pandas, que posteriormente se enviara a la base de datos en otro script

import pandas as pd
import os

def main():
    df = pd.read_csv(r"C:\Users\pablo\OneDrive - UNIR\TFM\TFM-pasoapaso\postgres\data\CDGVSP_01012023-31122024.csv", sep=";", encoding="latin1")
    # Cambiamos el nombre de las columnas para que sean más manejables
    df.columns = df.columns.str.replace(" ", "_").str.replace(".", "_")
    print(df.head())
    return df

if __name__ == "__main__":
    df = main()
