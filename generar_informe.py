import pandas as pd
from pysentimiento import create_analyzer
import os
import re
import json

def run_report_generation():
    """
    Lee los datos del Excel, realiza el análisis de sentimientos 
    y genera el panel HTML interactivo como 'index.html'.
    """
    print("--- INICIANDO GENERACIÓN DE INFORME HTML ---")
    
    try:
        df = pd.read_excel('Comentarios Campaña.xlsx')
        print("Archivo 'Comentarios Campaña.xlsx' cargado con éxito.")
    except FileNotFoundError:
        print("❌ ERROR: No se encontró el archivo 'Comentarios Campaña.xlsx'.")
        return

    # --- Limpieza y preparación de datos ---
    df['created_time_processed'] = pd.to_datetime(df['created_time_processed'])
    df['created_time_colombia'] = df['created_time_processed'] - pd.Timedelta(hours=5)
    df.dropna(subset=['created_time_colombia', 'comment_text', 'post_url'], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # --- NUEVO: Crear etiquetas legibles para cada pauta ---
    unique_posts = df[['post_url', 'platform']].drop_duplicates().reset_index(drop=True)
    post_labels = {}
    for index, row in unique_posts.iterrows():
        post_labels[row['post_url']] = f"Pauta {index + 1} ({row['platform']})"
    df['post_label'] = df['post_url'].map(post_labels)

    # --- Análisis de Sentimientos y Temas ---
    print("Analizando sentimientos y temas...")
    # (El resto del análisis no cambia)
    sentiment_analyzer = create_analyzer(task="sentiment", lang="es")
    df['sentimiento'] = df['comment_text'].apply(lambda text: {"POS": "Positivo", "NEG": "Negativo", "NEU": "Neutro"}.get(sentiment_analyzer.predict(str(text)).output, "Neutro"))
    def classify_topic(comment):
        comment_lower = str(comment).lower()
        if re.search(r'\bia\b|inteligencia artificial|prompts', comment_lower): return 'Críticas a la IA'
        if re.search(r'artista|diseñador|animador|contratar|pagar', comment_lower): return 'Apoyo a Artistas'
        if re.search(r'marketing|marca|audiencia|jefazos', comment_lower): return 'Estrategia de Marketing'
        if re.search(r'bonito|lindo|divino|horrible|feo|calidad|barato', comment_lower): return 'Calidad del Contenido'
        if re.search(r'alquería|pureza|competencia', comment_lower): return 'Mención a Competencia'
        return 'Otros'
    df['tema'] = df['comment_text'].apply(classify_topic)
    print("Análisis completado.")

    # --- Preparar datos para el JSON, incluyendo las nuevas columnas ---
    df_for_json = df[['created_time_colombia', 'comment_text', 'sentimiento', 'tema', 'platform', 'post_url', 'post_label']].copy()
    df_for_json.rename(columns={'created_time_colombia': 'date', 'comment_text': 'comment', 'sentimiento': 'sentiment', 'tema': 'topic'}, inplace=True)
    df_for_json['date'] = df_for_json['date'].dt.strftime('%Y-%m-%dT%H:%M:%S')
    all_data_json = json.dumps(df_for_json.to_dict('records'))

    min_date = df['created_time_colombia'].min().strftime('%Y-%m-%d')
    max_date = df['created_time_colombia'].max().strftime('%Y-%m-%d')
    
    # --- NUEVO: Generar el HTML para el filtro de pautas y la lista de enlaces ---
    post_filter_options = '<option value="Todas">Ver Todas las Pautas</option>'
    post_links_html = '<ul>'
    for url, label in post_labels.items():
        post_filter_options += f'<option value="{url}">{label}</option>'
        post_links_html += f'<li><strong>{label}:</strong> <a href="{url}" target="_blank">{url}</a></li>'
    post_links_html += '</ul>'

    # --- Generar el archivo HTML Dinámico ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel Interactivo de Campañas</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Arial', sans-serif; background: #f4f7f6; }}
            .container {{ max-width: 1400px; margin: 20px auto; }}
            .card {{ background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            .header {{ background: #1e3c72; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .header h1 {{ font-size: 2em; }}
            .filters {{ padding: 15px 20px; display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 20px; }}
            .filters label {{ font-weight: bold; margin-right: 5px; }}
            .filters input, .filters select {{ padding: 8px; border-radius: 5px; border: 1px solid #ccc; }}
            .post-links ul {{ list-style-type: none; padding: 15px 20px; }}
            .post-links li {{ margin-bottom: 8px; font-size: 0.9em; }}
            .post-links a {{ color: #007bff; text-decoration: none; word-break: break-all; }}
            .post-links a:hover {{ text-decoration: underline; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; padding: 20px; }}
            .stat-card {{ padding: 20px; text-align: center; border-left: 5px solid; }}
            /* ... (resto de estilos sin cambios) ... */
            .charts-section, .comments-section {{ padding: 20px; }}
            .section-title {{ font-size: 1.5em; margin-bottom: 20px; text-align: center; color: #333; }}
            .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }}
            .chart-container {{ position: relative; height: 400px; }}
        </style>
    </head>
    <body>
        <script id="data-store" type="application/json">{all_data_json}</script>

        <div class="container">
            <div class="card">
                <div class="header"><h1>📊 Panel Interactivo de Campañas</h1></div>
                <div class="filters">
                    <label for="startDate">Inicio:</label> <input type="date" id="startDate" value="{min_date}"> <input type="time" id="startTime" value="00:00">
                    <label for="endDate">Fin:</label> <input type="date" id="endDate" value="{max_date}"> <input type="time" id="endTime" value="23:59">
                    <label for="platformFilter">Red Social:</label> <select id="platformFilter"><option value="Todas">Todas</option><option value="Facebook">Facebook</option><option value="Instagram">Instagram</option><option value="TikTok">TikTok</option></select>
                    <label for="postFilter">Pauta Específica:</label> <select id="postFilter">{post_filter_options}</select>
                </div>
            </div>
            
            <div class="card post-links">
                <h2 class="section-title">Listado de Pautas Activas</h2>
                {post_links_html}
            </div>

            <div class="card">
                <div id="stats-grid" class="stats-grid"></div>
            </div>
            
            <div class="card charts-section">
                <h2 class="section-title">Análisis General</h2>
                <div class="charts-grid">
                    <div class="chart-container"><canvas id="postCountChart"></canvas></div>
                    <div class="chart-container"><canvas id="sentimentChart"></canvas></div>
                    <div class="chart-container"><canvas id="topicsChart"></canvas></div>
                    <div class="chart-container full-width"><canvas id="sentimentByTopicChart"></canvas></div>
                    <div class="chart-container full-width"><canvas id="dailyChart"></canvas></div>
                    <div class="chart-container full-width"><canvas id="hourlyChart"></canvas></div>
                </div>
            </section>
            
            <div class="card comments-section">
                <h2 class="section-title">💬 Comentarios Filtrados</h2>
                <div id="comments-list"></div>
            </div>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', () => {{
                const dataStoreElement = document.getElementById('data-store');
                const allData = JSON.parse(dataStoreElement.textContent);

                const startDateInput = document.getElementById('startDate');
                const startTimeInput = document.getElementById('startTime');
                const endDateInput = document.getElementById('endDate');
                const endTimeInput = document.getElementById('endTime');
                const platformFilter = document.getElementById('platformFilter');
                const postFilter = document.getElementById('postFilter'); // NUEVO

                const charts = {{
                    postCount: new Chart(document.getElementById('postCountChart'), {{ type: 'doughnut', options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ title: {{ display: true, text: 'Distribución de Pautas por Red Social' }} }} }} }}),
                    sentiment: new Chart(document.getElementById('sentimentChart'), {{ type: 'doughnut', options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ title: {{ display: true, text: 'Distribución de Sentimientos' }} }} }} }}),
                    // ... (resto de inicializaciones de gráficas no cambian)
                }};

                const updateDashboard = () => {{
                    const startFilter = startDateInput.value + 'T' + startTimeInput.value + ':00';
                    const endFilter = endDateInput.value + 'T' + endTimeInput.value + ':59';
                    const selectedPlatform = platformFilter.value;
                    const selectedPost = postFilter.value; // NUEVO

                    let filteredData = allData;

                    // NUEVO: Lógica de filtrado jerárquica
                    if (selectedPost !== 'Todas') {{
                        filteredData = allData.filter(d => d.post_url === selectedPost);
                    }} else if (selectedPlatform !== 'Todas') {{
                        filteredData = allData.filter(d => d.platform === selectedPlatform);
                    }}
                    filteredData = filteredData.filter(d => d.date >= startFilter && d.date <= endFilter);
                    
                    updateStats(filteredData);
                    updateCharts(allData, filteredData); // La nueva gráfica necesita todos los datos
                    updateCommentsList(filteredData);
                }};
                
                // ... (updateStats y updateCommentsList no cambian)
                
                const updateCharts = (totalData, filteredData) => {{
                    // --- NUEVO: Lógica para la gráfica de distribución de pautas ---
                    // Esta gráfica SIEMPRE muestra el total, no se afecta por los filtros
                    const postCounts = totalData.reduce((acc, curr) => {{
                        const platform = curr.platform || 'Desconocido';
                        if (!acc[platform]) {{ acc[platform] = new Set(); }}
                        acc[platform].add(curr.post_url);
                        return acc;
                    }}, {{}});
                    const postCountLabels = Object.keys(postCounts);
                    charts.postCount.data.labels = postCountLabels;
                    charts.postCount.data.datasets = [{{
                        data: postCountLabels.map(p => postCounts[p].size),
                        backgroundColor: ['#007bff', '#28a745', '#dc3545', '#ffc107']
                    }}];
                    charts.postCount.update();
                    
                    // (El resto de las gráficas usan los datos ya filtrados 'filteredData')
                    // ... (resto de la lógica de updateCharts no cambia, solo usa 'filteredData')
                }};

                // --- NUEVO: Lógica para actualizar las opciones del filtro de pautas ---
                const updatePostFilterOptions = () => {{
                    const selectedPlatform = platformFilter.value;
                    const currentPostSelection = postFilter.value;
                    
                    let availablePosts = [];
                    if (selectedPlatform === 'Todas') {{
                        availablePosts = [...new Set(allData.map(d => d.post_url))];
                    }} else {{
                        availablePosts = [...new Set(allData.filter(d => d.platform === selectedPlatform).map(d => d.post_url))];
                    }}
                    
                    const postLabels = Object.fromEntries(allData.map(d => [d.post_url, d.post_label]));

                    postFilter.innerHTML = '<option value="Todas">Ver Todas las Pautas</option>';
                    availablePosts.forEach(url => {{
                        const option = document.createElement('option');
                        option.value = url;
                        option.textContent = postLabels[url] || url;
                        postFilter.appendChild(option);
                    }});

                    if (availablePosts.includes(currentPostSelection)) {{
                        postFilter.value = currentPostSelection;
                    }} else {{
                        postFilter.value = 'Todas';
                    }}
                }};

                // Añadir los event listeners
                startDateInput.addEventListener('change', updateDashboard);
                startTimeInput.addEventListener('change', updateDashboard);
                endDateInput.addEventListener('change', updateDashboard);
                endTimeInput.addEventListener('change', updateDashboard);
                platformFilter.addEventListener('change', () => {{
                    updatePostFilterOptions();
                    updateDashboard();
                }});
                postFilter.addEventListener('change', updateDashboard);
                
                // Carga inicial
                updateDashboard();
            }});
        </script>
    </body>
    </html>
    """
    
    report_filename = 'index.html'
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Panel interactivo generado con éxito. Se guardó como '{report_filename}'.")

if __name__ == "__main__":
    run_report_generation()
