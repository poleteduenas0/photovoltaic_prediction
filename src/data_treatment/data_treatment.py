"""
Script creado por: Pablo Dueñas Fernández.
Este script orquesta el proceso completo de tratamiento de datos del proyecto.
Ejecuta secuencialmente los scripts de análisis de datos AEMET, ESIOS y producción,
coordinando el flujo de procesamiento y asegurando que todos los datos estén
preparados para el modelado predictivo.
"""

import os
import pandas as pd
from sqlalchemy import create_engine
from aemet_data import main as get_aemet_data
from esios_data import main as get_esios_data
from production_data import main as get_production_data

# ejecutamos los script de analisis de datos:

# 1. AEMET
df_aemet = get_aemet_data()
# 2. ESIOS
df_esios_short = get_esios_data()


# informamos de la finalización de los procesos si estos terminan sin errores
print("Todos los procesos de análisis de datos han finalizado.")
print("Juntamos los datos para el modelo de predicción de la producción de energía.")

# 3. Producción
df_production = get_production_data(df_aemet, df_esios_short)

print("Datos de producción obtenidos y guardados en la base de datos.")

