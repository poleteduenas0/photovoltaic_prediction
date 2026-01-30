"""
Script creado por: Pablo Dueñas Fernández.
Este script implementa una interfaz web interactiva usando Streamlit para visualizar
y analizar datos meteorológicos, de producción fotovoltaica y del mercado eléctrico.
Permite ejecutar modelos de predicción LSTM y visualizar los resultados a través
de gráficos interactivos y métricas en tiempo real.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Configuración de la página
st.set_page_config(
    page_title="Predicción de Excedente Fotovoltaico",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #0D47A1;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .metric-label {
        font-size: 1rem;
        color: #555;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 5px 5px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E88E5;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Función para conectar a la base de datos PostgreSQL
@st.cache_resource
def get_db_connection():
    load_dotenv()
    conn_str = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"\
               f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    return create_engine(conn_str)

# Función para obtener datos de una tabla
@st.cache_data(ttl=300)
def get_table_data(table_name, start_date=None, end_date=None):
    engine = get_db_connection()
    
    if start_date and end_date:
        # Determinar el nombre de la columna de fecha según la tabla
        date_column = "fecha" if "aemet" in table_name or "esios" in table_name else "fecha"
        query = f"SELECT * FROM {table_name} WHERE {date_column} BETWEEN '{start_date}' AND '{end_date}' ORDER BY {date_column}"
    else:
        query = f"SELECT * FROM {table_name} ORDER BY fecha"
    
    try:
        df = pd.read_sql(query, engine)
        # Convertir columna de fecha a datetime
        if "fecha" in df.columns:
            df["fecha"] = pd.to_datetime(df["fecha"])
        elif "fecha" in df.columns:
            df["fecha"] = pd.to_datetime(df["fecha"])
        return df
    except Exception as e:
        st.error(f"Error al obtener datos de {table_name}: {str(e)}")
        return pd.DataFrame()

# Función para obtener las columnas numéricas de un DataFrame
def get_numeric_columns(df):
    return df.select_dtypes(include=[np.number]).columns.tolist()

# Función para crear gráficos de series temporales
def plot_time_series(df, x_col, y_cols, title):
    if len(y_cols) == 0:
        return None
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    for i, col in enumerate(y_cols):
        # Usar el eje secundario para la segunda variable en adelante
        use_secondary_y = i > 0
        
        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df[col],
                name=col,
                line=dict(width=2),
                mode='lines'
            ),
            secondary_y=use_secondary_y
        )
    
    fig.update_layout(
        title=title,
        xaxis_title="Fecha",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_white",
        height=500,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    # Actualizar títulos de ejes Y
    if len(y_cols) > 0:
        fig.update_yaxes(title_text=y_cols[0], secondary_y=False)
    if len(y_cols) > 1:
        fig.update_yaxes(title_text=y_cols[1], secondary_y=True)
    
    return fig

# Función para ejecutar el script de predicción
def run_prediction_script(days_to_predict):
    try:
        script_path = r"C:\Users\pablo\OneDrive - UNIR\TFM\TFM-pasoapaso\models\model_developer.py"
        env_path = r"C:\Users\pablo\OneDrive - UNIR\TFM\TFM-pasoapaso\.venv\Scripts\python.exe"
        # Verificar si el archivo existe
        if not os.path.exists(script_path):
            return False, f"No se encontró el script en la ruta: {script_path}"
        
        # Ejecutar el script
        process = subprocess.Popen(
            [env_path, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            return False, f"Error al ejecutar el script: {stderr}"
        
        # Limpiar la caché de datos para que se actualicen en la próxima carga
        get_table_data.clear()
        
        return True, "Predicción ejecutada correctamente. Los datos se han actualizado."
    
    except Exception as e:
        return False, f"Error al ejecutar la predicción: {str(e)}"

# Función para mostrar métricas en tarjetas
def display_metrics(df, metric_cols, date_col):
    if df.empty or len(metric_cols) == 0:
        st.warning("No hay datos disponibles para mostrar métricas")
        return
    
    # Obtener los últimos valores
    latest_data = df.iloc[-1]
    
    # Crear columnas para las métricas
    cols = st.columns(len(metric_cols))
    
    for i, col_name in enumerate(metric_cols):
        with cols[i]:
            st.markdown(f"""
            <div class="card">
                <div class="metric-label">{col_name}</div>
                <div class="metric-value">{latest_data[col_name]:.2f}</div>
                <div class="metric-label">Última actualización: {latest_data[date_col].strftime('%d/%m/%Y')}</div>
            </div>
            """, unsafe_allow_html=True)

# Función para obtener fechas desde variables de entorno
def get_env_dates():
    load_dotenv()
    start_date_str = os.getenv("AEMET_START_DATE")
    end_date_str = os.getenv("AEMET_END_DATE")
    
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else (datetime.now() - timedelta(days=30)).date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else datetime.now().date()
    except ValueError:
        # Si hay un error en el formato de fecha, usar valores por defecto
        start_date = (datetime.now() - timedelta(days=30)).date()
        end_date = datetime.now().date()
    
    return start_date, end_date

# Título principal
st.markdown('<h1 class="main-header">Predicción de Excedente de Producción Fotovoltaica</h1>', unsafe_allow_html=True)

# Obtener fechas de inicio y fin desde variables de entorno
env_start_date, env_end_date = get_env_dates()

# Crear pestañas
tabs = st.tabs(["📊 Datos AEMET", "⚡ Datos Producción", "💰 Datos ESIOS", "🔮 Forecast"])

# Pestaña 1: Datos AEMET
with tabs[0]:
    st.markdown('<h2 class="sub-header">Datos Meteorológicos (AEMET)</h2>', unsafe_allow_html=True)
    
    # Selector de rango de fechas
    col1, col2 = st.columns(2)
    with col1:
        start_date_aemet = st.date_input("Fecha inicial", 
                                         value=env_start_date,
                                         key="aemet_start")
    with col2:
        end_date_aemet = st.date_input("Fecha final", 
                                       value=env_end_date,
                                       key="aemet_end")
    
    # Cargar datos
    aemet_data = get_table_data("aemet_data_treated", start_date_aemet, end_date_aemet)
    
    if not aemet_data.empty:
        # Mostrar métricas principales
        display_metrics(aemet_data, ['sol', 'tmax', 'tmed'], 'fecha')
        
        # Selector de variables para gráfico
        st.markdown('<h3 class="sub-header">Visualización de Variables</h3>', unsafe_allow_html=True)
        numeric_cols = get_numeric_columns(aemet_data)
        selected_cols_aemet = st.multiselect(
            "Seleccione variables para visualizar",
            options=numeric_cols,
            default=['sol', 'tmed'] if 'sol' in numeric_cols and 'tmed' in numeric_cols else numeric_cols[:2],
            key="aemet_vars"
        )
        
        # Crear gráfico
        if selected_cols_aemet:
            fig_aemet = plot_time_series(aemet_data, 'fecha', selected_cols_aemet, 
                                         "Evolución de Variables Meteorológicas")
            st.plotly_chart(fig_aemet, use_container_width=True)
        
        # Mostrar tabla de datos
        with st.expander("Ver datos en tabla"):
            st.dataframe(aemet_data, use_container_width=True)
    else:
        st.warning("No hay datos disponibles para el rango de fechas seleccionado")

# Pestaña 2: Datos Producción
with tabs[1]:
    st.markdown('<h2 class="sub-header">Datos de Producción Fotovoltaica</h2>', unsafe_allow_html=True)
    
    # Selector de rango de fechas
    col1, col2 = st.columns(2)
    with col1:
        start_date_prod = st.date_input("Fecha inicial", 
                                        value=env_start_date,
                                        key="prod_start")
    with col2:
        end_date_prod = st.date_input("Fecha final", 
                                      value=env_end_date,
                                      key="prod_end")
    
    # Cargar datos
    prod_data = get_table_data("production_data_treated", start_date_prod, end_date_prod)
    
    if not prod_data.empty:
        # Mostrar métricas principales
        display_metrics(prod_data, ['Totalproduction'], 'fecha')
        
        # Selector de variables para gráfico
        st.markdown('<h3 class="sub-header">Visualización de Variables</h3>', unsafe_allow_html=True)
        numeric_cols = get_numeric_columns(prod_data)
        selected_cols_prod = st.multiselect(
            "Seleccione variables para visualizar",
            options=numeric_cols,
            default=['Totalproduction'] if 'Totalproduction' in numeric_cols else numeric_cols[:1],
            key="prod_vars"
        )
        
        # Crear gráfico
        if selected_cols_prod:
            fig_prod = plot_time_series(prod_data, 'fecha', selected_cols_prod, 
                                        "Evolución de Producción Fotovoltaica")
            st.plotly_chart(fig_prod, use_container_width=True)
        
        # Mostrar tabla de datos
        with st.expander("Ver datos en tabla"):
            st.dataframe(prod_data, use_container_width=True)
    else:
        st.warning("No hay datos disponibles para el rango de fechas seleccionado")

# Pestaña 3: Datos ESIOS
with tabs[2]:
    st.markdown('<h2 class="sub-header">Datos del Mercado Eléctrico (ESIOS)</h2>', unsafe_allow_html=True)
    
    # Selector de rango de fechas
    col1, col2 = st.columns(2)
    with col1:
        start_date_esios = st.date_input("Fecha inicial", 
                                         value=env_start_date,
                                         key="esios_start")
    with col2:
        end_date_esios = st.date_input("Fecha final", 
                                       value=env_end_date,
                                       key="esios_end")
    
    # Cargar datos
    esios_data = get_table_data("esios_data_treated", start_date_esios, end_date_esios)
    
    if not esios_data.empty:
        # Mostrar métricas principales
        display_metrics(esios_data, ['precio_excedente'], 'fecha')
        
        # Selector de variables para gráfico
        st.markdown('<h3 class="sub-header">Visualización de Variables</h3>', unsafe_allow_html=True)
        numeric_cols = get_numeric_columns(esios_data)
        selected_cols_esios = st.multiselect(
            "Seleccione variables para visualizar",
            options=numeric_cols,
            default=['precio_excedente'] if 'precio_excedente' in numeric_cols else numeric_cols[:2],
            key="esios_vars"
        )
        
        # Crear gráfico
        if selected_cols_esios:
            fig_esios = plot_time_series(esios_data, 'fecha', selected_cols_esios, 
                                         "Evolución de Precios del Mercado Eléctrico")
            st.plotly_chart(fig_esios, use_container_width=True)
        
        # Mostrar tabla de datos
        with st.expander("Ver datos en tabla"):
            st.dataframe(esios_data, use_container_width=True)
    else:
        st.warning("No hay datos disponibles para el rango de fechas seleccionado")

# Pestaña 4: Forecast
with tabs[3]:
    st.markdown('<h2 class="sub-header">Predicciones y Forecast</h2>', unsafe_allow_html=True)
    
    # Sección de configuración de predicción
    st.markdown('<h3 class="sub-header">Configuración de Predicción</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        days_to_predict = st.slider("Días a predecir", min_value=1, max_value=30, value=7)
    
    with col2:
        if st.button("Lanzar Predicción", type="primary"):
            with st.spinner("Ejecutando modelos de predicción..."):
                success, message = run_prediction_script(days_to_predict)
                if success:
                    st.success(message)
                    # Forzar recarga de la página para actualizar datos
                else:
                    st.error(message)
    
    # Cargar datos de predicciones
    st.markdown('<h3 class="sub-header">Resultados de Predicciones</h3>', unsafe_allow_html=True)
    
    # Crear pestañas para cada tipo de predicción
    forecast_tabs = st.tabs(["☀️ Predicción Sol", "⚡ Predicción Producción", "💰 Predicción Precio Excedente"])
    
    # Pestaña de predicción de sol
    with forecast_tabs[0]:
        # Cargar datos de predicción de sol
        sol_forecast = get_table_data("aemet_forecast_sol")
        
        if not sol_forecast.empty:
            # Mostrar gráfico de predicción
            fig_sol = px.line(sol_forecast, x='fecha', y='sol', 
                             title="Predicción de Horas de Sol",
                             labels={'sol': 'Horas de Sol', 'fecha': 'Fecha'},
                             line_shape='spline')
            
            fig_sol.update_layout(
                template="plotly_white",
                height=500,
                margin=dict(l=20, r=20, t=50, b=20)
            )
            
            st.plotly_chart(fig_sol, use_container_width=True)
            
            # Mostrar tabla de predicción
            with st.expander("Ver datos de predicción"):
                st.dataframe(sol_forecast, use_container_width=True)
        else:
            st.warning("No hay datos de predicción disponibles para horas de sol")
    
    # Pestaña de predicción de producción
    with forecast_tabs[1]:
        # Cargar datos de predicción de producción
        prod_forecast = get_table_data("production_forecast_Totalproduction")
        
        if not prod_forecast.empty:
            # Mostrar gráfico de predicción
            fig_prod = px.line(prod_forecast, x='fecha', y='Totalproduction', 
                              title="Predicción de Producción Fotovoltaica",
                              labels={'Totalproduction': 'Producción Total', 'fecha': 'Fecha'},
                              line_shape='spline')
            
            fig_prod.update_layout(
                template="plotly_white",
                height=500,
                margin=dict(l=20, r=20, t=50, b=20)
            )
            
            st.plotly_chart(fig_prod, use_container_width=True)
            
            # Mostrar tabla de predicción
            with st.expander("Ver datos de predicción"):
                st.dataframe(prod_forecast, use_container_width=True)
        else:
            st.warning("No hay datos de predicción disponibles para producción fotovoltaica")
    
    # Pestaña de predicción de precio excedente
    with forecast_tabs[2]:
        # Cargar datos de predicción de precio excedente
        precio_forecast = get_table_data("esios_forecast_precio_excedente")
        
        if not precio_forecast.empty:
            # Mostrar gráfico de predicción
            fig_precio = px.line(precio_forecast, x='fecha', y='precio_excedente', 
                                title="Predicción de Precio de Excedente",
                                labels={'precio_excedente': 'Precio Excedente', 'fecha': 'Fecha'},
                                line_shape='spline')
            
            fig_precio.update_layout(
                template="plotly_white",
                height=500,
                margin=dict(l=20, r=20, t=50, b=20)
            )
            
            st.plotly_chart(fig_precio, use_container_width=True)
            
            # Mostrar tabla de predicción
            with st.expander("Ver datos de predicción"):
                st.dataframe(precio_forecast, use_container_width=True)
        else:
            st.warning("No hay datos de predicción disponibles para precio de excedente")
                                        
# Información adicional en el sidebar
with st.sidebar:
    st.image("https://www.unir.net/wp-content/uploads/2020/03/logo-unir-universidad-online.png", width=200)
    st.markdown("### TFM - Predicción de Excedente Fotovoltaico")
    st.markdown("Esta aplicación permite visualizar y predecir valores relacionados con la producción fotovoltaica, nivel de sol y precio de venta de excedente.")
    
    st.markdown("---")
    st.markdown("### Información del Sistema")
    
    # Mostrar estado de conexión a la base de datos
    try:
        engine = get_db_connection()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result:
                st.success("✅ Conexión a PostgreSQL establecida")
            else:
                st.error("❌ Error de conexión a PostgreSQL")
    except Exception as e:
        st.error(f"❌ Error de conexión a PostgreSQL: {str(e)}")
    
    st.markdown("---")
    st.markdown("### Modelos LSTM")
    st.markdown("""
    Los modelos utilizados para las predicciones son redes neuronales recurrentes LSTM bidireccionales con las siguientes características:
    
    - Capa LSTM bidireccional (128 unidades)
    - Regularización con Dropout (0.3)
    - Segunda capa LSTM (64 unidades)
    - Capa densa con activación ReLU
    - Optimizador Adam con tasa adaptativa
    """)
    
    st.markdown("---")
    st.caption("© 2025 - Desarrollado para TFM UNIR")
