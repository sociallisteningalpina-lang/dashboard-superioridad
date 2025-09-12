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
    
    # --- 1. Cargar y procesar los datos ---
    try:
        # Lee el archivo desde la misma carpeta (ruta relativa)
        df = pd.read_excel('Comentarios Campaña.xlsx')
        print("Archivo 'Superioridad lactea.xlsx' cargado con éxito.")
    except FileNotFoundError:
        print("❌ ERROR: No se encontró el archivo 'Superioridad lactea.xlsx'. Asegúrate de que el script de extracción se haya ejecutado primero.")
        return # Detiene la ejecución si no hay datos

    # Limpieza y transformación
    df.drop_duplicates(subset=['comment_text', 'created_time_processed'], inplace=True, ignore_index=True)
    df['created_time_processed'] = pd.to_datetime(df['created_time_processed'])
    df['created_time_colombia'] = df['created_time_processed'] - pd.Timedelta(hours=5)
    df.dropna(subset=['comment_text'], inplace=True)

    # <-- LÍNEA CLAVE PARA CORREGIR EL ERROR DE FECHAS INVÁLIDAS -->
    df.dropna(subset=['created_time_colombia'], inplace=True)

    df = df[df['comment_text'].str.strip() != '']
    df.reset_index(drop=True, inplace=True) # Reiniciar el índice después de eliminar filas

    # Análisis de Sentimientos y Temas
    print("Analizando sentimientos y temas...")
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

    # --- 2. Preparar datos para incrustar en HTML ---
    df_for_json = df[['created_time_colombia', 'comment_text', 'sentimiento', 'tema']].copy()
    df_for_json.rename(columns={'created_time_colombia': 'date', 'comment_text': 'comment', 'sentimiento': 'sentiment', 'tema': 'topic'}, inplace=True)
    df_for_json['date'] = df_for_json['date'].dt.strftime('%Y-%m-%dT%H:%M:%S')

    all_data_json = json.dumps(df_for_json.to_dict('records'))
    min_date = df['created_time_colombia'].min().strftime('%Y-%m-%d')
    max_date = df['created_time_colombia'].max().strftime('%Y-%m-%d')

    # --- 3. Generar el archivo HTML Dinámico ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel Interactivo: Campaña de Nutrición</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Arial', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
            .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ font-size: 2.5em; }}
            .filters {{ padding: 20px 30px; background: #f8f9fa; display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 15px; border-bottom: 1px solid #dee2e6; }}
            .filters label {{ font-weight: bold; margin-left: 10px; }}
            .filters input[type="date"], .filters input[type="time"] {{ padding: 8px; border-radius: 5px; border: 1px solid #ccc; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; padding: 30px; background: #f8f9fa; }}
            .stat-card {{ background: white; padding: 25px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); text-align: center; }}
            .stat-number {{ font-size: 3em; font-weight: bold; margin-bottom: 10px; }}
            .positive {{ color: #28a745; }} .negative {{ color: #dc3545; }} .neutral {{ color: #ffc107; }} .total {{ color: #007bff; }}
            .charts-section, .insights-section, .comments-section {{ padding: 30px; }}
            .section-title {{ font-size: 1.8em; margin-bottom: 25px; text-align: center; color: #333; }}
            .charts-grid {{ display: grid; grid-template-columns: 1fr 1.5fr; gap: 30px; align-items: start; margin-bottom: 30px;}}
            .chart-container {{ background: white; padding: 25px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); position: relative; height: 400px; }}
            .chart-container.full-width {{ grid-column: 1 / -1; }}
            .insights-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
            .insight-card {{ background: #f0f2f5; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; }}
            .comment-item {{ margin: 15px 0; padding: 15px; border-radius: 10px; border-left: 5px solid; word-wrap: break-word; }}
            .comment-positive {{ border-left-color: #28a745; background: #d4edda; }} .comment-negative {{ border-left-color: #dc3545; background: #f8d7da; }} .comment-neutral {{ border-left-color: #ffc107; background: #fff3cd; }}
            @media (max-width: 900px) {{ 
                .charts-grid {{ grid-template-columns: 1fr; }} 
            }}
        </style>
    </head>
    <body>
        <script id="data-store" type="application/json">
            {all_data_json}
        </script>

        <div class="container">
            <div class="header"><h1>🥛 Panel Interactivo: Campaña de Nutrición</h1></div>
            
            <div class="filters">
                <label for="startDate">Fecha Inicio:</label>
                <input type="date" id="startDate" value="{min_date}">
                <input type="time" id="startTime" value="00:00">
                <label for="endDate">Fecha Fin:</label>
                <input type="date" id="endDate" value="{max_date}">
                <input type="time" id="endTime" value="23:59">
            </div>

            <div id="stats-grid" class="stats-grid"></div>
            
            <section class="charts-section">
                <h2 class="section-title">Análisis de Sentimientos y Temas</h2>
                <div class="charts-grid">
                    <div class="chart-container"><canvas id="sentimentChart"></canvas></div>
                    <div class="chart-container"><canvas id="topicsChart"></canvas></div>
                    <div class="chart-container full-width"><canvas id="sentimentByTopicChart"></canvas></div>
                    <div class="chart-container full-width"><canvas id="hourlyChart"></canvas></div>
                </div>
            </section>

            <section id="insights-section" class="insights-section" style="background: #f8f9fa;"></section>
            
            <section class="comments-section">
                <h2 class="section-title">💬 Comentarios Filtrados</h2>
                <div id="comments-list"></div>
            </section>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', () => {{
                const dataStoreElement = document.getElementById('data-store');
                const allData = JSON.parse(dataStoreElement.textContent);

                const startDateInput = document.getElementById('startDate');
                const startTimeInput = document.getElementById('startTime');
                const endDateInput = document.getElementById('endDate');
                const endTimeInput = document.getElementById('endTime');

                const charts = {{
                    sentiment: new Chart(document.getElementById('sentimentChart'), {{ type: 'doughnut', options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ title: {{ display: true, text: 'Distribución de Sentimientos' }} }} }} }}),
                    topics: new Chart(document.getElementById('topicsChart'), {{ type: 'bar', options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: {{ legend: {{ display: false }}, title: {{ display: true, text: 'Temas Principales' }} }} }} }}),
                    sentimentByTopic: new Chart(document.getElementById('sentimentByTopicChart'), {{ type: 'bar', options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y', scales: {{ x: {{ stacked: true }}, y: {{ stacked: true }} }}, plugins: {{ title: {{ display: true, text: 'Sentimiento por Tema' }} }} }} }}),
                    hourly: new Chart(document.getElementById('hourlyChart'), {{ type: 'bar', options: {{ responsive: true, maintainAspectRatio: false, scales: {{ x: {{ stacked: true }}, y: {{ stacked: true, position: 'left', title: {{ display: true, text: 'Comentarios por Hora' }} }}, y1: {{ position: 'right', grid: {{ drawOnChartArea: false }}, title: {{ display: true, text: 'Total Acumulado' }} }} }}, plugins: {{ title: {{ display: true, text: 'Volumen de Comentarios por Hora' }} }} }} }})
                }};

                const updateDashboard = () => {{
                    const startFilter = startDateInput.value + 'T' + startTimeInput.value + ':00';
                    const endFilter = endDateInput.value + 'T' + endTimeInput.value + ':59';
                    const filteredData = allData.filter(d => d.date >= startFilter && d.date <= endFilter);
                    
                    updateStats(filteredData);
                    updateCharts(filteredData);
                    updateInsights(filteredData);
                    updateCommentsList(filteredData);
                }};
                
                const updateStats = (data) => {{
                    const total = data.length;
                    const sentiments = data.reduce((acc, curr) => {{ acc[curr.sentiment] = (acc[curr.sentiment] || 0) + 1; return acc; }}, {{}});
                    const pos = sentiments['Positivo'] || 0;
                    const neg = sentiments['Negativo'] || 0;
                    const neu = sentiments['Neutro'] || 0;
                    document.getElementById('stats-grid').innerHTML = `
                        <div class="stat-card"><div class="stat-number total">${{total}}</div><div>Total Comentarios</div></div>
                        <div class="stat-card"><div class="stat-number positive">${{pos}}</div><div>Positivos (${{(total > 0 ? (pos / total * 100) : 0).toFixed(1)}}%)</div></div>
                        <div class="stat-card"><div class="stat-number negative">${{neg}}</div><div>Negativos (${{(total > 0 ? (neg / total * 100) : 0).toFixed(1)}}%)</div></div>
                        <div class="stat-card"><div class="stat-number neutral">${{neu}}</div><div>Neutros (${{(total > 0 ? (neu / total * 100) : 0).toFixed(1)}}%)</div></div>
                    `;
                }};

                const updateInsights = (data) => {{
                    if (data.length === 0) {{
                        document.getElementById('insights-section').innerHTML = '<h2 class="section-title">💡 Conclusiones Clave</h2><p style="text-align:center;">No hay datos para el rango de fechas seleccionado.</p>';
                        return;
                    }}
                    const sentiments = data.reduce((acc, curr) => {{ acc[curr.sentiment] = (acc[curr.sentiment] || 0) + 1; return acc; }}, {{}});
                    const topics = data.reduce((acc, curr) => {{ acc[curr.topic] = (acc[curr.topic] || 0) + 1; return acc; }}, {{}});
                    const predominantSentiment = Object.keys(sentiments).length > 0 ? Object.keys(sentiments).reduce((a, b) => sentiments[a] > sentiments[b] ? a : b) : "N/A";
                    const topTopic = Object.keys(topics).length > 0 ? Object.keys(topics).reduce((a, b) => topics[a] > topics[b] ? a : b) : "N/A";
                    document.getElementById('insights-section').innerHTML = `
                        <h2 class="section-title">💡 Conclusiones Clave</h2>
                        <div class="insights-grid">
                            <div class="insight-card"><p>El sentimiento predominante fue <strong>${{predominantSentiment}}</strong>, con un <strong>${{(sentiments[predominantSentiment] / data.length * 100).toFixed(1)}}%</strong> de los comentarios.</p></div>
                            <div class="insight-card"><p>El tema principal fue <strong>'${{topTopic}}'</strong>, representando el <strong>${{(topics[topTopic] / data.length * 100).toFixed(1)}}%</strong> de la discusión.</p></div>
                            <div class="insight-card"><p>Se analizaron <strong>${{data.length}}</strong> comentarios en el período seleccionado.</p></div>
                        </div>
                    `;
                }};

                const updateCommentsList = (data) => {{
                    const sentimentToCss = {{ 'Positivo': 'positive', 'Negativo': 'negative', 'Neutro': 'neutral' }};
                    const listHtml = data.sort((a, b) => b.date.localeCompare(a.date)).slice(0, 200).map((d, i) => {{
                        const escapedComment = d.comment.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                        return `<div class="comment-item comment-${{sentimentToCss[d.sentiment]}}">
                                    <div class="comment-header"><strong>[${{d.sentiment.toUpperCase()}}] (Tema: ${{d.topic}})</strong> - ${{escapedComment}}</div>
                                </div>`;
                    }}).join('');
                    document.getElementById('comments-list').innerHTML = listHtml || "<p style='text-align:center;'>No hay comentarios en este rango de fechas.</p>";
                }};

                const updateCharts = (data) => {{
                    const sentimentCounts = data.reduce((acc, curr) => {{ acc[curr.sentiment] = (acc[curr.sentiment] || 0) + 1; return acc; }}, {{}});
                    charts.sentiment.data.labels = ['Positivo', 'Negativo', 'Neutro'];
                    charts.sentiment.data.datasets = [{{ data: [sentimentCounts['Positivo']||0, sentimentCounts['Negativo']||0, sentimentCounts['Neutro']||0], backgroundColor: ['#28a745', '#dc3545', '#ffc107'] }}];
                    charts.sentiment.update();
                    const topicCounts = data.reduce((acc, curr) => {{ acc[curr.topic] = (acc[curr.topic] || 0) + 1; return acc; }}, {{}});
                    const sortedTopics = Object.entries(topicCounts).sort((a, b) => b[1] - a[1]);
                    charts.topics.data.labels = sortedTopics.map(d => d[0]);
                    charts.topics.data.datasets = [{{ label: 'Comentarios', data: sortedTopics.map(d => d[1]), backgroundColor: '#3498db' }}];
                    charts.topics.update();
                    const sbtCounts = data.reduce((acc, curr) => {{ if (!acc[curr.topic]) acc[curr.topic] = {{ Positivo: 0, Negativo: 0, Neutro: 0 }}; acc[curr.topic][curr.sentiment]++; return acc; }}, {{}});
                    const sbtLabels = Object.keys(sbtCounts).sort((a,b) => (sbtCounts[b].Positivo + sbtCounts[b].Negativo + sbtCounts[b].Neutro) - (sbtCounts[a].Positivo + sbtCounts[a].Negativo + sbtCounts[a].Neutro));
                    charts.sentimentByTopic.data.labels = sbtLabels;
                    charts.sentimentByTopic.data.datasets = [ {{ label: 'Positivo', data: sbtLabels.map(l => sbtCounts[l].Positivo), backgroundColor: '#28a745' }}, {{ label: 'Negativo', data: sbtLabels.map(l => sbtCounts[l].Negativo), backgroundColor: '#dc3545' }}, {{ label: 'Neutro', data: sbtLabels.map(l => sbtCounts[l].Neutro), backgroundColor: '#ffc107' }} ];
                    charts.sentimentByTopic.update();
                    const hourlyCounts = data.reduce((acc, curr) => {{ const hour = curr.date.substring(0, 13) + ':00:00'; if (!acc[hour]) acc[hour] = {{ Positivo: 0, Negativo: 0, Neutro: 0, Total: 0 }}; acc[hour][curr.sentiment]++; acc[hour].Total++; return acc; }}, {{}});
                    const sortedHours = Object.keys(hourlyCounts).sort();
                    let cumulative = 0;
                    const cumulativeData = sortedHours.map(h => {{ cumulative += hourlyCounts[h].Total; return cumulative; }});
                    charts.hourly.data.labels = sortedHours.map(h => new Date(h).toLocaleString('es-CO', {{ day: '2-digit', month: 'short', hour: '2-digit', minute:'2-digit' }}));
                    charts.hourly.data.datasets = [ {{ label: 'Positivo', data: sortedHours.map(h => hourlyCounts[h].Positivo), backgroundColor: '#28a745', yAxisID: 'y' }}, {{ label: 'Negativo', data: sortedHours.map(h => hourlyCounts[h].Negativo), backgroundColor: '#dc3545', yAxisID: 'y' }}, {{ label: 'Neutro', data: sortedHours.map(h => hourlyCounts[h].Neutro), backgroundColor: '#ffc107', yAxisID: 'y' }}, {{ label: 'Acumulado', type: 'line', data: cumulativeData, borderColor: '#007bff', yAxisID: 'y1' }} ];
                    charts.hourly.update();
                }};

                startDateInput.addEventListener('change', updateDashboard);
                startTimeInput.addEventListener('change', updateDashboard);
                endDateInput.addEventListener('change', updateDashboard);
                endTimeInput.addEventListener('change', updateDashboard);
                
                updateDashboard();
            }});
        </script>
    </body>
    </html>
    """

    # --- 4. Guardar el archivo HTML final ---
    # Guarda el archivo como 'index.html' para que sea compatible con GitHub Pages
    report_filename = 'index.html'
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Panel interactivo generado con éxito. Se guardó como '{report_filename}'.")
    print("--- GENERACIÓN DE INFORME TERMINADA ---")


# Este bloque solo se ejecutará si corres el script directamente en tu PC para probarlo
if __name__ == "__main__":
    run_report_generation()

