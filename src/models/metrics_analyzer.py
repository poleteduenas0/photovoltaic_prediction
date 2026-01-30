"""
Script creado por: Pablo Dueñas Fernández.
Este script analiza y visualiza las métricas de rendimiento de todos los modelos
implementados (LSTM, BiLSTM, ARIMA, ARMAX) para comparar su efectividad en diferentes
tipos de datos (AEMET, producción, ESIOS).
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
from sqlalchemy import create_engine

def load_metrics_from_csv():
    """Cargar métricas desde archivo CSV consolidado"""
    consolidated_file = 'models/metrics_results/all_models_metrics.csv'
    
    if os.path.exists(consolidated_file):
        df_metrics = pd.read_csv(consolidated_file)
        print(f"Métricas cargadas desde CSV: {len(df_metrics)} registros")
        return df_metrics
    else:
        print("No se encontró archivo de métricas consolidado")
        return pd.DataFrame()

def load_metrics_from_db():
    """Cargar métricas desde base de datos"""
    try:
        load_dotenv()
        conn_str = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"\
                   f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        engine = create_engine(conn_str)
        
        df_metrics = pd.read_sql("SELECT * FROM model_performance_metrics ORDER BY timestamp", engine)
        print(f"Métricas cargadas desde BD: {len(df_metrics)} registros")
        return df_metrics
    except Exception as e:
        print(f"Error al cargar métricas desde BD: {e}")
        return pd.DataFrame()

def create_comparison_visualizations(df_metrics):
    """Crear visualizaciones de comparación de modelos"""
    
    # Crear directorio para visualizaciones
    os.makedirs('models/visualizations/comparison', exist_ok=True)
    
    # 1. Comparación general por modelo - Figura más grande para acomodar todos los modelos
    plt.figure(figsize=(20, 16))
    
    # MAE por modelo y tipo de datos
    plt.subplot(2, 3, 1)
    df_pivot_mae = df_metrics.pivot_table(
        values='mae', 
        index='data_type', 
        columns='model', 
        aggfunc='mean'
    )
    sns.heatmap(df_pivot_mae, annot=True, fmt='.4f', cmap='RdYlBu_r', cbar_kws={'shrink': 0.8})
    plt.title('MAE por Modelo y Tipo de Datos', fontsize=12)
    plt.ylabel('Tipo de Datos')
    plt.xlabel('Modelo')
    plt.xticks(rotation=45, ha='right')
    
    # RMSE por modelo y tipo de datos
    plt.subplot(2, 3, 2)
    df_pivot_rmse = df_metrics.pivot_table(
        values='rmse', 
        index='data_type', 
        columns='model', 
        aggfunc='mean'
    )
    sns.heatmap(df_pivot_rmse, annot=True, fmt='.4f', cmap='RdYlBu_r', cbar_kws={'shrink': 0.8})
    plt.title('RMSE por Modelo y Tipo de Datos', fontsize=12)
    plt.ylabel('Tipo de Datos')
    plt.xlabel('Modelo')
    plt.xticks(rotation=45, ha='right')
    
    # MSE por modelo y tipo de datos
    plt.subplot(2, 3, 3)
    df_pivot_mse = df_metrics.pivot_table(
        values='mse', 
        index='data_type', 
        columns='model', 
        aggfunc='mean'
    )
    sns.heatmap(df_pivot_mse, annot=True, fmt='.4f', cmap='RdYlBu_r', cbar_kws={'shrink': 0.8})
    plt.title('MSE por Modelo y Tipo de Datos', fontsize=12)
    plt.ylabel('Tipo de Datos')
    plt.xlabel('Modelo')
    plt.xticks(rotation=45, ha='right')
    
    # Gráficos de barras para cada métrica
    metrics_to_plot = ['mae', 'rmse', 'mse']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']  # Colores para diferentes modelos
    
    for i, metric in enumerate(metrics_to_plot):
        plt.subplot(2, 3, 4 + i)
        df_avg = df_metrics.groupby(['model', 'data_type'])[metric].mean().reset_index()
        
        # Crear gráfico de barras agrupadas
        data_types = df_avg['data_type'].unique()
        models = df_avg['model'].unique()
        x = np.arange(len(data_types))
        width = 0.8 / len(models)
        
        for j, model in enumerate(models):
            model_data = df_avg[df_avg['model'] == model]
            values = [model_data[model_data['data_type'] == dt][metric].values[0] 
                     if len(model_data[model_data['data_type'] == dt]) > 0 else 0 
                     for dt in data_types]
            color = colors[j % len(colors)]
            plt.bar(x + j * width, values, width, label=model, alpha=0.8, color=color)
        
        plt.title(f'{metric.upper()} por Modelo', fontsize=12)
        plt.xlabel('Tipo de Datos')
        plt.ylabel(metric.upper())
        plt.xticks(x + width * (len(models) - 1) / 2, data_types, rotation=45, ha='right')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('models/visualizations/comparison/models_comparison_overview.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Comparación por familia de modelos
    plt.figure(figsize=(18, 12))
    
    # Agrupar modelos por familia
    neural_models = df_metrics[df_metrics['model'].isin(['LSTM', 'BiLSTM'])]
    classical_models = df_metrics[df_metrics['model'].isin(['ARIMA', 'ARMAX'])]
    
    for i, (family_name, family_data) in enumerate([('Neural Networks', neural_models), 
                                                    ('Classical Models', classical_models)]):
        if not family_data.empty:
            for j, metric in enumerate(['mae', 'rmse', 'mse']):
                plt.subplot(2, 3, i*3 + j + 1)
                
                df_avg = family_data.groupby(['model', 'data_type'])[metric].mean().reset_index()
                
                data_types = df_avg['data_type'].unique()
                models = df_avg['model'].unique()
                x = np.arange(len(data_types))
                width = 0.8 / len(models)
                
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
                for k, model in enumerate(models):
                    model_data = df_avg[df_avg['model'] == model]
                    values = [model_data[model_data['data_type'] == dt][metric].values[0] 
                             if len(model_data[model_data['data_type'] == dt]) > 0 else 0 
                             for dt in data_types]
                    plt.bar(x + k * width, values, width, label=model, 
                           alpha=0.8, color=colors[k % len(colors)])
                
                plt.title(f'{family_name} - {metric.upper()}')
                plt.xlabel('Tipo de Datos')
                plt.ylabel(metric.upper())
                plt.xticks(x + width * (len(models) - 1) / 2, data_types)
                plt.legend()
                plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('models/visualizations/comparison/models_by_family_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Ranking general de todos los modelos
    plt.figure(figsize=(16, 10))
    
    for i, metric in enumerate(['mae', 'rmse', 'mse']):
        plt.subplot(2, 2, i + 1)
        
        # Calcular promedio por modelo across all data types
        model_avg = df_metrics.groupby('model')[metric].mean().sort_values()
        
        colors = plt.cm.viridis(np.linspace(0, 1, len(model_avg)))
        bars = plt.barh(range(len(model_avg)), model_avg.values, color=colors)
        
        plt.yticks(range(len(model_avg)), model_avg.index)
        plt.xlabel(f'{metric.upper()} (menor es mejor)')
        plt.title(f'Ranking General - {metric.upper()}')
        plt.grid(True, alpha=0.3, axis='x')
        
        # Añadir valores en las barras
        for j, (model, value) in enumerate(model_avg.items()):
            plt.text(value + max(model_avg.values) * 0.01, j, f'{value:.4f}', 
                    va='center', fontsize=9)
    
    # Tabla resumen de rankings
    plt.subplot(2, 2, 4)
    plt.axis('off')
    
    ranking_data = []
    for metric in ['mae', 'rmse', 'mse']:
        model_avg = df_metrics.groupby('model')[metric].mean().sort_values()
        for rank, (model, value) in enumerate(model_avg.items(), 1):
            ranking_data.append({'Modelo': model, 'Métrica': metric.upper(), 
                                'Ranking': rank, 'Valor': f'{value:.4f}'})
    
    ranking_df = pd.DataFrame(ranking_data)
    pivot_ranking = ranking_df.pivot(index='Modelo', columns='Métrica', values='Ranking')
    
    table = plt.table(cellText=pivot_ranking.values,
                     rowLabels=pivot_ranking.index,
                     colLabels=pivot_ranking.columns,
                     cellLoc='center',
                     loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    plt.title('Tabla de Rankings (1=mejor)')
    
    plt.tight_layout()
    plt.savefig('models/visualizations/comparison/models_overall_ranking.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Comparación específica LSTM vs BiLSTM
    lstm_bilstm_data = df_metrics[df_metrics['model'].isin(['LSTM', 'BiLSTM'])]
    
    if not lstm_bilstm_data.empty:
        plt.figure(figsize=(15, 10))
        
        for i, metric in enumerate(['mae', 'rmse', 'mse']):
            plt.subplot(2, 3, i + 1)
            
            # Gráfico de barras comparativo LSTM vs BiLSTM
            df_comparison = lstm_bilstm_data.groupby(['model', 'data_type'])[metric].mean().reset_index()
            
            data_types = df_comparison['data_type'].unique()
            x = np.arange(len(data_types))
            width = 0.35
            
            lstm_values = [df_comparison[(df_comparison['model'] == 'LSTM') & 
                                       (df_comparison['data_type'] == dt)][metric].values[0] 
                          if len(df_comparison[(df_comparison['model'] == 'LSTM') & 
                                             (df_comparison['data_type'] == dt)]) > 0 else 0 
                          for dt in data_types]
            
            bilstm_values = [df_comparison[(df_comparison['model'] == 'BiLSTM') & 
                                         (df_comparison['data_type'] == dt)][metric].values[0] 
                            if len(df_comparison[(df_comparison['model'] == 'BiLSTM') & 
                                               (df_comparison['data_type'] == dt)]) > 0 else 0 
                            for dt in data_types]
            
            plt.bar(x - width/2, lstm_values, width, label='LSTM', alpha=0.8, color='#1f77b4')
            plt.bar(x + width/2, bilstm_values, width, label='BiLSTM', alpha=0.8, color='#ff7f0e')
            
            plt.title(f'{metric.upper()} - LSTM vs BiLSTM')
            plt.xlabel('Tipo de Datos')
            plt.ylabel(metric.upper())
            plt.xticks(x, data_types)
            plt.legend()
            plt.grid(True, alpha=0.3)
        
        # Gráfico de mejora porcentual BiLSTM vs LSTM
        plt.subplot(2, 3, 4)
        improvement_data = []
        
        for data_type in data_types:
            for metric in ['mae', 'rmse', 'mse']:
                lstm_val = lstm_bilstm_data[(lstm_bilstm_data['model'] == 'LSTM') & 
                                          (lstm_bilstm_data['data_type'] == data_type)][metric].mean()
                bilstm_val = lstm_bilstm_data[(lstm_bilstm_data['model'] == 'BiLSTM') & 
                                            (lstm_bilstm_data['data_type'] == data_type)][metric].mean()
                
                if not pd.isna(lstm_val) and not pd.isna(bilstm_val) and lstm_val != 0:
                    improvement = ((lstm_val - bilstm_val) / lstm_val) * 100
                    improvement_data.append({
                        'data_type': data_type,
                        'metric': metric,
                        'improvement': improvement
                    })
        
        if improvement_data:
            df_improvement = pd.DataFrame(improvement_data)
            pivot_improvement = df_improvement.pivot(index='data_type', columns='metric', values='improvement')
            
            sns.heatmap(pivot_improvement, annot=True, fmt='.2f', cmap='RdYlGn', center=0,
                       cbar_kws={'label': 'Mejora % (positivo = BiLSTM mejor)'})
            plt.title('Mejora Porcentual BiLSTM vs LSTM')
            plt.ylabel('Tipo de Datos')
            plt.xlabel('Métrica')
        
        # Tabla resumen de comparación
        plt.subplot(2, 3, 5)
        plt.axis('off')
        
        comparison_stats = lstm_bilstm_data.groupby(['model', 'data_type'])[['mae', 'rmse', 'mse']].mean().round(4)
        
        table_text = "Comparación LSTM vs BiLSTM\n\n"
        for data_type in data_types:
            table_text += f"{data_type.upper()}:\n"
            for model in ['LSTM', 'BiLSTM']:
                if (model, data_type) in comparison_stats.index:
                    stats = comparison_stats.loc[(model, data_type)]
                    table_text += f"  {model}: MAE={stats['mae']:.4f}, RMSE={stats['rmse']:.4f}\n"
            table_text += "\n"
        
        plt.text(0.1, 0.9, table_text, fontsize=10, verticalalignment='top', 
                fontfamily='monospace', transform=plt.gca().transAxes)
        plt.title('Resumen Comparativo')
        
        plt.tight_layout()
        plt.savefig('models/visualizations/comparison/lstm_vs_bilstm_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    print("Visualizaciones de comparación creadas en 'models/visualizations/comparison/'")

def generate_metrics_summary_csv(df_metrics):
    """Generar CSV resumen con estadísticas de todos los modelos"""
    
    # Estadísticas por modelo y tipo de datos
    summary_stats = df_metrics.groupby(['model', 'data_type', 'target_variable']).agg({
        'mae': ['mean', 'std', 'min', 'max'],
        'rmse': ['mean', 'std', 'min', 'max'],
        'mse': ['mean', 'std', 'min', 'max']
    }).round(6)
    
    # Aplanar columnas multinivel
    summary_stats.columns = ['_'.join(col).strip() for col in summary_stats.columns.values]
    summary_stats = summary_stats.reset_index()
    
    # Guardar resumen
    os.makedirs('models/metrics_results', exist_ok=True)
    summary_file = 'models/metrics_results/models_summary_statistics.csv'
    summary_stats.to_csv(summary_file, index=False)
    
    # Ranking de modelos por métrica
    ranking_data = []
    for data_type in df_metrics['data_type'].unique():
        subset = df_metrics[df_metrics['data_type'] == data_type]
        avg_metrics = subset.groupby('model')[['mae', 'rmse', 'mse']].mean()
        
        for metric in ['mae', 'rmse', 'mse']:
            ranked = avg_metrics.sort_values(metric)
            for rank, (model, values) in enumerate(ranked.iterrows(), 1):
                ranking_data.append({
                    'data_type': data_type,
                    'metric': metric,
                    'rank': rank,
                    'model': model,
                    'value': values[metric]
                })
    
    ranking_df = pd.DataFrame(ranking_data)
    ranking_file = 'models/metrics_results/models_ranking.csv'
    ranking_df.to_csv(ranking_file, index=False)
    
    # Generar tabla específica de comparación LSTM vs BiLSTM
    lstm_bilstm_comparison = df_metrics[df_metrics['model'].isin(['LSTM', 'BiLSTM'])]
    if not lstm_bilstm_comparison.empty:
        comparison_summary = lstm_bilstm_comparison.groupby(['model', 'data_type'])[['mae', 'rmse', 'mse']].agg(['mean', 'std']).round(6)
        comparison_summary.columns = ['_'.join(col).strip() for col in comparison_summary.columns.values]
        comparison_summary = comparison_summary.reset_index()
        
        comparison_file = 'models/metrics_results/lstm_vs_bilstm_comparison.csv'
        comparison_summary.to_csv(comparison_file, index=False)
        print(f"Comparación LSTM vs BiLSTM guardada en: {comparison_file}")
    
    # Generar análisis por familia de modelos
    family_analysis = []
    
    neural_models = df_metrics[df_metrics['model'].isin(['LSTM', 'BiLSTM'])]
    classical_models = df_metrics[df_metrics['model'].isin(['ARIMA', 'ARMAX'])]
    
    for family_name, family_data in [('Neural Networks', neural_models), 
                                     ('Classical Models', classical_models)]:
        if not family_data.empty:
            for data_type in family_data['data_type'].unique():
                subset = family_data[family_data['data_type'] == data_type]
                for metric in ['mae', 'rmse', 'mse']:
                    avg_value = subset[metric].mean()
                    std_value = subset[metric].std()
                    best_model = subset.loc[subset[metric].idxmin(), 'model']
                    
                    family_analysis.append({
                        'family': family_name,
                        'data_type': data_type,
                        'metric': metric,
                        'mean': avg_value,
                        'std': std_value,
                        'best_model': best_model
                    })
    
    family_df = pd.DataFrame(family_analysis)
    family_file = 'models/metrics_results/models_family_analysis.csv'
    family_df.to_csv(family_file, index=False)
    
    print(f"Análisis por familia de modelos guardado en: {family_file}")
    print(f"Resumen estadístico guardado en: {summary_file}")
    print(f"Ranking de modelos guardado en: {ranking_file}")
    
    return summary_stats, ranking_df

def main():
    """Función principal para análisis de métricas"""
    print("=== Analizador de Métricas de Modelos (LSTM, BiLSTM, ARIMA, ARMAX) ===")
    
    # Cargar métricas (priorizar CSV, luego BD)
    df_metrics = load_metrics_from_csv()
    
    if df_metrics.empty:
        print("Intentando cargar desde base de datos...")
        df_metrics = load_metrics_from_db()
    
    if df_metrics.empty:
        print("No se encontraron métricas para analizar")
        return
    
    # Mostrar información general
    print(f"\nDatos cargados:")
    print(f"- Total de registros: {len(df_metrics)}")
    print(f"- Modelos: {sorted(df_metrics['model'].unique())}")
    print(f"- Tipos de datos: {sorted(df_metrics['data_type'].unique())}")
    print(f"- Variables objetivo: {sorted(df_metrics['target_variable'].unique())}")
    
    # Mostrar conteo por modelo
    print(f"\nConteo de registros por modelo:")
    model_counts = df_metrics['model'].value_counts()
    for model, count in model_counts.items():
        print(f"- {model}: {count} registros")
    
    # Crear visualizaciones
    print("\nCreando visualizaciones...")
    create_comparison_visualizations(df_metrics)
    
    # Generar resúmenes CSV
    print("\nGenerando resúmenes estadísticos...")
    summary_stats, ranking_df = generate_metrics_summary_csv(df_metrics)
    
    # Mostrar mejores modelos por tipo de datos
    print("\n=== Mejores Modelos por Tipo de Datos (RMSE) ===")
    for data_type in sorted(df_metrics['data_type'].unique()):
        best_model = ranking_df[
            (ranking_df['data_type'] == data_type) & 
            (ranking_df['metric'] == 'rmse') & 
            (ranking_df['rank'] == 1)
        ]
        if not best_model.empty:
            model_name = best_model.iloc[0]['model']
            rmse_value = best_model.iloc[0]['value']
            print(f"- {data_type.capitalize()}: {model_name} (RMSE: {rmse_value:.4f})")
    
    # Comparación específica LSTM vs BiLSTM
    lstm_bilstm_data = df_metrics[df_metrics['model'].isin(['LSTM', 'BiLSTM'])]
    if not lstm_bilstm_data.empty:
        print("\n=== Comparación LSTM vs BiLSTM ===")
        for data_type in sorted(lstm_bilstm_data['data_type'].unique()):
            print(f"\n{data_type.upper()}:")
            for metric in ['mae', 'rmse', 'mse']:
                lstm_val = lstm_bilstm_data[(lstm_bilstm_data['model'] == 'LSTM') & 
                                          (lstm_bilstm_data['data_type'] == data_type)][metric].mean()
                bilstm_val = lstm_bilstm_data[(lstm_bilstm_data['model'] == 'BiLSTM') & 
                                            (lstm_bilstm_data['data_type'] == data_type)][metric].mean()
                
                if not pd.isna(lstm_val) and not pd.isna(bilstm_val):
                    improvement = ((lstm_val - bilstm_val) / lstm_val) * 100 if lstm_val != 0 else 0
                    better = "BiLSTM" if bilstm_val < lstm_val else "LSTM"
                    print(f"  {metric.upper()}: LSTM={lstm_val:.4f}, BiLSTM={bilstm_val:.4f} "
                          f"(Mejora: {improvement:+.2f}%, Mejor: {better})")
    
    # Análisis por familia de modelos
    neural_models = df_metrics[df_metrics['model'].isin(['LSTM', 'BiLSTM'])]
    classical_models = df_metrics[df_metrics['model'].isin(['ARIMA', 'ARMAX'])]
    
    if not neural_models.empty and not classical_models.empty:
        print("\n=== Comparación por Familias de Modelos ===")
        
        for data_type in sorted(df_metrics['data_type'].unique()):
            print(f"\n{data_type.upper()}:")
            
            neural_subset = neural_models[neural_models['data_type'] == data_type]
            classical_subset = classical_models[classical_models['data_type'] == data_type]
            
            for metric in ['mae', 'rmse', 'mse']:
                if not neural_subset.empty and not classical_subset.empty:
                    neural_avg = neural_subset[metric].mean()
                    classical_avg = classical_subset[metric].mean()
                    
                    better_family = "Redes Neuronales" if neural_avg < classical_avg else "Modelos Clásicos"
                    improvement = abs((neural_avg - classical_avg) / max(neural_avg, classical_avg) * 100)
                    
                    print(f"  {metric.upper()}: Neural={neural_avg:.4f}, Classical={classical_avg:.4f} "
                          f"(Mejor: {better_family}, Diferencia: {improvement:.2f}%)")
    
    # Ranking general
    print("\n=== Ranking General de Todos los Modelos ===")
    for metric in ['mae', 'rmse', 'mse']:
        model_avg = df_metrics.groupby('model')[metric].mean().sort_values()
        print(f"\n{metric.upper()} (menor es mejor):")
        for rank, (model, value) in enumerate(model_avg.items(), 1):
            print(f"  {rank}. {model}: {value:.4f}")
    
    print("\nAnálisis completado. Revisa los archivos generados:")
    print("- models/visualizations/comparison/")
    print("- models/metrics_results/")

if __name__ == "__main__":
    main()
