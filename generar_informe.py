import pandas as pd
from pysentimiento import create_analyzer
import os
import re
import json

def run_report_generation():
    """
    Lee los datos del Excel, realiza el análisis de sentimientos y temas,
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

    # <<<--- MODIFICACIÓN 1: MEJORA EN LA LÓGICA DE LISTADO DE PAUTAS ---<<<
    # Se obtienen todas las pautas únicas y se cuenta cuántos comentarios tiene cada una.
    unique_posts = df[['post_url', 'platform']].drop_duplicates()
    comment_counts = df.groupby('post_url').size().reset_index(name='comment_count')
    
    # Se unen los datos y se rellenan con 0 las pautas sin comentarios.
    unique_posts = pd.merge(unique_posts, comment_counts, on='post_url', how='left').fillna(0)
    unique_posts['comment_count'] = unique_posts['comment_count'].astype(int)
    
    # Se ordena por cantidad de comentarios de forma descendente.
    unique_posts.sort_values(by='comment_count', ascending=False, inplace=True)
    unique_posts.reset_index(drop=True, inplace=True)
    
    # Se crea una etiqueta legible para cada pauta.
    post_labels = {}
    for index, row in unique_posts.iterrows():
        post_labels[row['post_url']] = f"Pauta {index + 1} ({row['platform']})"
    
    df['post_label'] = df['post_url'].map(post_labels)
    unique_posts['post_label'] = unique_posts['post_url'].map(post_labels)
    
    # Se prepara el JSON con la información completa de todas las pautas para el HTML.
    all_posts_json = json.dumps(unique_posts.to_dict('records'))
    # --- FIN DE MODIFICACIÓN 1 ---

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

    df_for_json = df[['created_time_colombia', 'comment_text', 'sentimiento', 'tema', 'platform', 'post_url', 'post_label']].copy()
    df_for_json.rename(columns={'created_time_colombia': 'date', 'comment_text': 'comment', 'sentimiento': 'sentiment', 'tema': 'topic'}, inplace=True)
    df_for_json['date'] = df_for_json['date'].dt.strftime('%Y-%m-%dT%H:%M:%S')
    all_data_json = json.dumps(df_for_json.to_dict('records'))

    min_date = df['created_time_colombia'].min().strftime('%Y-%m-%d')
    max_date = df['created_time_colombia'].max().strftime('%Y-%m-%d')
    
    post_filter_options = '<option value="Todas">Ver Todas las Pautas</option>'
    for url, label in post_labels.items():
        post_filter_options += f'<option value="{url}">{label}</option>'

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
            body {{ font-family: 'Arial', sans-serif; background: #f4f7f6; color: #333; }}
            .container {{ max-width: 1400px; margin: 20px auto; }}
            .card {{ background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            .header {{ background: #1e3c72; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .header h1 {{ font-size: 2em; }}
            .filters {{ padding: 15px 20px; display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 20px; }}
            .filters label {{ font-weight: bold; margin-right: 5px; }}
            .filters input, .filters select {{ padding: 8px; border-radius: 5px; border: 1px solid #ccc; }}
            .post-links table {{ width: 100%; border-collapse: collapse; }}
            .post-links th, .post-links td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
            .post-links th {{ background-color: #f8f9fa; }}
            .post-links a {{ color: #007bff; text-decoration: none; font-weight: bold; }}
            .post-links a:hover {{ text-decoration: underline; }}
            .pagination-controls {{ text-align: center; padding: 15px; }}
            .pagination-controls button, .filter-btn {{ padding: 8px 16px; margin: 0 5px; cursor: pointer; border: 1px solid #ccc; background-color: #fff; border-radius: 5px; font-weight: bold; }}
            .pagination-controls button:disabled {{ cursor: not-allowed; background-color: #f8f9fa; color: #aaa; }}
            .pagination-controls span {{ margin: 0 10px; font-weight: bold; vertical-align: middle; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; padding: 20px; }}
            .stat-card {{ padding: 20px; text-align: center; border-left: 5px solid; }}
            .stat-card.total {{ border-left-color: #007bff; }} .stat-card.positive {{ border-left-color: #28a745; }} .stat-card.negative {{ border-left-color: #dc3545; }} .stat-card.neutral {{ border-left-color: #ffc107; }}
            .stat-number {{ font-size: 2.5em; font-weight: bold; margin-bottom: 5px; }}
            .positive-text {{ color: #28a745; }} .negative-text {{ color: #dc3545; }} .neutral-text {{ color: #ffc107; }} .total-text {{ color: #007bff; }}
            .charts-section, .comments-section {{ padding: 20px; }}
            .section-title {{ font-size: 1.5em; margin-bottom: 20px; text-align: center; color: #333; }}
            .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }}
            .chart-container {{ position: relative; height: 400px; }} .chart-container.full-width {{ grid-column: 1 / -1; }}
            .comment-item {{ margin-bottom: 10px; padding: 15px; border-radius: 8px; border-left: 5px solid; word-wrap: break-word; }}
            .comment-positive {{ border-left-color: #28a745; background: #f0fff4; }} .comment-negative {{ border-left-color: #dc3545; background: #fff5f5; }} .comment-neutral {{ border-left-color: #ffc107; background: #fffbeb; }}
            .comment-meta {{ margin-bottom: 8px; font-size: 0.9em; display: flex; justify-content: space-between; align-items: center; }}
            .comment-date {{ color: #6c757d; font-style: italic; }}
            .comments-controls {{ display: flex; justify-content: center; align-items: center; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }}
            .filter-btn.active {{ background-color: #007bff; color: white; border-color: #007bff; }}
            @media (max-width: 900px) {{ .charts-grid {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
        <script id="data-store" type="application/json">{all_data_json}</script>
        <script id="posts-data-store" type="application/json">{all_posts_json}</script>

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
                <div id="post-links-table"></div>
                <div id="post-links-pagination" class="pagination-controls"></div>
            </div>

            <div class="card"><div id="stats-grid" class="stats-grid"></div></div>
            
            <div class="card charts-section">
                <h2 class="section-title">Análisis General</h2>
                <div class="charts-grid">
                    <div class="chart-container"><canvas id="postCountChart"></canvas></div><div class="chart-container"><canvas id="sentimentChart"></canvas></div><div class="chart-container"><canvas id="topicsChart"></canvas></div>
                    <div class="chart-container full-width"><canvas id="sentimentByTopicChart"></canvas></div><div class="chart-container full-width"><canvas id="dailyChart"></canvas></div><div class="chart-container full-width"><canvas id="hourlyChart"></canvas></div>
                </div>
            </div>
            
            <div class="card comments-section">
                <h2 class="section-title">💬 Comentarios Filtrados</h2>
                <div id="comments-controls" class="comments-controls"></div>
                <div id="comments-list"></div>
                <div id="comments-pagination" class="pagination-controls"></div>
            </div>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', () => {{
                // <<<--- MODIFICACIÓN 2: LÓGICA JS PARA NUEVAS FUNCIONALIDADES ---<<<
                const allData = JSON.parse(document.getElementById('data-store').textContent);
                const allPostsData = JSON.parse(document.getElementById('posts-data-store').textContent); // Carga todos los posts
                
                const startDateInput = document.getElementById('startDate'), startTimeInput = document.getElementById('startTime');
                const endDateInput = document.getElementById('endDate'), endTimeInput = document.getElementById('endTime');
                const platformFilter = document.getElementById('platformFilter'), postFilter = document.getElementById('postFilter');

                const charts = {{ /* ... (sin cambios aquí) ... */ }};
                // Copia el contenido del objeto 'charts' de tu código original aquí
                Object.assign(charts, {{
                    postCount: new Chart(document.getElementById('postCountChart'), {{ type: 'doughnut', options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ title: {{ display: true, text: 'Distribución de Pautas por Red Social' }} }} }} }}),
                    sentiment: new Chart(document.getElementById('sentimentChart'), {{ type: 'doughnut', options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ title: {{ display: true, text: 'Distribución de Sentimientos' }} }} }} }}),
                    topics: new Chart(document.getElementById('topicsChart'), {{ type: 'bar', options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: {{ legend: {{ display: false }}, title: {{ display: true, text: 'Temas Principales' }} }} }} }}),
                    sentimentByTopic: new Chart(document.getElementById('sentimentByTopicChart'), {{ type: 'bar', options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y', scales: {{ x: {{ stacked: true }}, y: {{ stacked: true }} }}, plugins: {{ title: {{ display: true, text: 'Sentimiento por Tema' }} }} }} }}),
                    daily: new Chart(document.getElementById('dailyChart'), {{ type: 'bar', options: {{ responsive: true, maintainAspectRatio: false, scales: {{ x: {{ stacked: true }}, y: {{ stacked: true }} }}, plugins: {{ title: {{ display: true, text: 'Volumen de Comentarios por Día' }} }} }} }}),
                    hourly: new Chart(document.getElementById('hourlyChart'), {{ type: 'bar', options: {{ responsive: true, maintainAspectRatio: false, scales: {{ x: {{ stacked: true }}, y: {{ stacked: true, position: 'left', title: {{ display: true, text: 'Comentarios por Hora' }} }}, y1: {{ position: 'right', grid: {{ drawOnChartArea: false }}, title: {{ display: true, text: 'Total Acumulado' }} }} }}, plugins: {{ title: {{ display: true, text: 'Volumen de Comentarios por Hora' }} }} }} }})
                }});


                let postLinksCurrentPage = 1;
                const POST_LINKS_PER_PAGE = 5;
                let commentsCurrentPage = 1;
                const COMMENTS_PER_PAGE = 10;
                let commentsSentimentFilter = 'Todos';

                const updatePostLinks = () => {{
                    const selectedPlatform = platformFilter.value;
                    // Ahora filtra desde 'allPostsData', que tiene todas las pautas
                    const postsToShow = (selectedPlatform === 'Todas') ? allPostsData : allPostsData.filter(p => p.platform === selectedPlatform);
                    
                    const tableDiv = document.getElementById('post-links-table');
                    const paginationDiv = document.getElementById('post-links-pagination');
                    tableDiv.innerHTML = ''; paginationDiv.innerHTML = '';
                    if (postsToShow.length === 0) return;

                    const totalPages = Math.ceil(postsToShow.length / POST_LINKS_PER_PAGE);
                    if (postLinksCurrentPage > totalPages) postLinksCurrentPage = 1;

                    const startIndex = (postLinksCurrentPage - 1) * POST_LINKS_PER_PAGE;
                    const paginatedPosts = postsToShow.slice(startIndex, startIndex + POST_LINKS_PER_PAGE);

                    // Se añade la columna "Total Comentarios"
                    let tableHTML = '<table><tr><th>Pauta</th><th>Total Comentarios</th><th>Enlace</th></tr>';
                    paginatedPosts.forEach(p => {{
                        tableHTML += `<tr><td>${{p.post_label}}</td><td><b>${{p.comment_count}}</b></td><td><a href="${{p.post_url}}" target="_blank">Ver Pauta</a></td></tr>`;
                    }});
                    tableHTML += '</table>';
                    tableDiv.innerHTML = tableHTML;

                    if (totalPages > 1) {{
                        paginationDiv.innerHTML = `<button id="prevPageBtn" ${{ (postLinksCurrentPage === 1) ? 'disabled' : '' }}>Anterior</button><span>Página ${{postLinksCurrentPage}} de ${{totalPages}}</span><button id="nextPageBtn" ${{ (postLinksCurrentPage === totalPages) ? 'disabled' : '' }}>Siguiente</button>`;
                        document.getElementById('prevPageBtn')?.addEventListener('click', () => {{ if (postLinksCurrentPage > 1) {{ postLinksCurrentPage--; updatePostLinks(); }} }});
                        document.getElementById('nextPageBtn')?.addEventListener('click', () => {{ if (postLinksCurrentPage < totalPages) {{ postLinksCurrentPage++; updatePostLinks(); }} }});
                    }}
                }};
                
                const updateDashboard = () => {{
                    const startFilter = `${{startDateInput.value}}T${{startTimeInput.value}}:00`;
                    const endFilter = `${{endDateInput.value}}T${{endTimeInput.value}}:59`;
                    const selectedPlatform = platformFilter.value;
                    const selectedPost = postFilter.value;
                    
                    let filteredData = allData.filter(d => d.date >= startFilter && d.date <= endFilter);
                    if (selectedPost !== 'Todas') {{
                        filteredData = filteredData.filter(d => d.post_url === selectedPost);
                    }} else if (selectedPlatform !== 'Todas') {{
                        filteredData = filteredData.filter(d => d.platform === selectedPlatform);
                    }}
                    
                    updateStats(filteredData);
                    updateCharts(allPostsData, filteredData); // Se pasa allPostsData para el conteo de pautas
                    updateCommentsList(filteredData);
                }};
                
                const updateStats = (data) => {{ const total = data.length; const sentiments = data.reduce((acc, curr) => {{ acc[curr.sentiment] = (acc[curr.sentiment] || 0) + 1; return acc; }}, {{}}); const pos = sentiments['Positivo'] || 0; const neg = sentiments['Negativo'] || 0; const neu = sentiments['Neutro'] || 0; document.getElementById('stats-grid').innerHTML = `<div class="stat-card total"><div class="stat-number total-text">${{total}}</div><div>Total Comentarios</div></div><div class="stat-card positive"><div class="stat-number positive-text">${{pos}}</div><div>Positivos (${{(total > 0 ? (pos / total * 100) : 0).toFixed(1)}}%)</div></div><div class="stat-card negative"><div class="stat-number negative-text">${{neg}}</div><div>Negativos (${{(total > 0 ? (neg / total * 100) : 0).toFixed(1)}}%)</div></div><div class="stat-card neutral"><div class="stat-number neutral-text">${{neu}}</div><div>Neutros (${{(total > 0 ? (neu / total * 100) : 0).toFixed(1)}}%)</div></div>`; }};
                
                const updateCommentsList = (data) => {{
                    const dataToShow = (commentsSentimentFilter === 'Todos') ? data : data.filter(d => d.sentiment === commentsSentimentFilter);
                    dataToShow.sort((a, b) => b.date.localeCompare(a.date));

                    const controlsDiv = document.getElementById('comments-controls');
                    const listDiv = document.getElementById('comments-list');
                    const paginationDiv = document.getElementById('comments-pagination');
                    listDiv.innerHTML = ''; paginationDiv.innerHTML = '';
                    
                    // Renderizar botones de filtro
                    controlsDiv.innerHTML = ['Todos', 'Positivo', 'Negativo', 'Neutro'].map(s => 
                        `<button class="filter-btn ${{commentsSentimentFilter === s ? 'active' : ''}}" data-sentiment="${{s}}">${{s}}</button>`
                    ).join('');
                    
                    controlsDiv.querySelectorAll('.filter-btn').forEach(btn => {{
                        btn.addEventListener('click', (e) => {{
                            commentsSentimentFilter = e.target.dataset.sentiment;
                            commentsCurrentPage = 1;
                            updateCommentsList(data);
                        }});
                    }});

                    if (dataToShow.length === 0) {{
                        listDiv.innerHTML = "<p style='text-align:center;'>No hay comentarios para mostrar.</p>";
                        return;
                    }}

                    const totalPages = Math.ceil(dataToShow.length / COMMENTS_PER_PAGE);
                    if (commentsCurrentPage > totalPages) commentsCurrentPage = 1;

                    const startIndex = (commentsCurrentPage - 1) * COMMENTS_PER_PAGE;
                    const paginatedComments = dataToShow.slice(startIndex, startIndex + COMMENTS_PER_PAGE);

                    const sentimentToCss = {{ 'Positivo': 'positive', 'Negativo': 'negative', 'Neutro': 'neutral' }};
                    let listHtml = '';
                    paginatedComments.forEach(d => {{
                        const escapedComment = d.comment.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                        const formattedDate = new Date(d.date).toLocaleString('es-CO', {{ day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute:'2-digit' }});
                        listHtml += `<div class="comment-item comment-${{sentimentToCss[d.sentiment]}}">
                                        <div class="comment-meta">
                                            <strong>[${{d.sentiment.toUpperCase()}}] (Tema: ${{d.topic}})</strong>
                                            <span class="comment-date">${{formattedDate}}</span>
                                        </div>
                                        <div>${{escapedComment}}</div>
                                    </div>`;
                    }});
                    listDiv.innerHTML = listHtml;

                    if (totalPages > 1) {{
                        paginationDiv.innerHTML = `<button id="prevCommentPageBtn" ${{ (commentsCurrentPage === 1) ? 'disabled' : '' }}>Anterior</button><span>Página ${{commentsCurrentPage}} de ${{totalPages}}</span><button id="nextCommentPageBtn" ${{ (commentsCurrentPage === totalPages) ? 'disabled' : '' }}>Siguiente</button>`;
                        document.getElementById('prevCommentPageBtn')?.addEventListener('click', () => {{ if (commentsCurrentPage > 1) {{ commentsCurrentPage--; updateCommentsList(data); }} }});
                        document.getElementById('nextCommentPageBtn')?.addEventListener('click', () => {{ if (commentsCurrentPage < totalPages) {{ commentsCurrentPage++; updateCommentsList(data); }} }});
                    }}
                }};

                const updateCharts = (postsData, filteredData) => {{ 
                    const postCounts = postsData.reduce((acc, curr) => {{ acc[curr.platform] = (acc[curr.platform] || 0) + 1; return acc; }}, {{}}); const postCountLabels = Object.keys(postCounts); charts.postCount.data.labels = postCountLabels; charts.postCount.data.datasets = [{{ data: postCountLabels.map(p => postCounts[p]), backgroundColor: ['#007bff', '#6f42c1', '#dc3545', '#ffc107', '#28a745'] }}]; charts.postCount.update(); 
                    /* ... (resto del código de updateCharts sin cambios) ... */ 
                    const sentimentCounts = filteredData.reduce((acc, curr) => {{ acc[curr.sentiment] = (acc[curr.sentiment] || 0) + 1; return acc; }}, {{}}); charts.sentiment.data.labels = ['Positivo', 'Negativo', 'Neutro']; charts.sentiment.data.datasets = [{{ data: [sentimentCounts['Positivo']||0, sentimentCounts['Negativo']||0, sentimentCounts['Neutro']||0], backgroundColor: ['#28a745', '#dc3545', '#ffc107'] }}]; charts.sentiment.update(); const topicCounts = filteredData.reduce((acc, curr) => {{ acc[curr.topic] = (acc[curr.topic] || 0) + 1; return acc; }}, {{}}); const sortedTopics = Object.entries(topicCounts).sort((a, b) => b[1] - a[1]); charts.topics.data.labels = sortedTopics.map(d => d[0]); charts.topics.data.datasets = [{{ label: 'Comentarios', data: sortedTopics.map(d => d[1]), backgroundColor: '#3498db' }}]; charts.topics.update(); const sbtCounts = filteredData.reduce((acc, curr) => {{ if (!acc[curr.topic]) acc[curr.topic] = {{ Positivo: 0, Negativo: 0, Neutro: 0 }}; acc[curr.topic][curr.sentiment]++; return acc; }}, {{}}); const sbtLabels = Object.keys(sbtCounts).sort((a,b) => (sbtCounts[b].Positivo + sbtCounts[b].Negativo + sbtCounts[b].Neutro) - (sbtCounts[a].Positivo + sbtCounts[a].Negativo + sbtCounts[a].Neutro)); charts.sentimentByTopic.data.labels = sbtLabels; charts.sentimentByTopic.data.datasets = [ {{ label: 'Positivo', data: sbtLabels.map(l => sbtCounts[l].Positivo), backgroundColor: '#28a745' }}, {{ label: 'Negativo', data: sbtLabels.map(l => sbtCounts[l].Negativo), backgroundColor: '#dc3545' }}, {{ label: 'Neutro', data: sbtLabels.map(l => sbtCounts[l].Neutro), backgroundColor: '#ffc107' }} ]; charts.sentimentByTopic.update(); const dailyCounts = filteredData.reduce((acc, curr) => {{ const day = curr.date.substring(0, 10); if (!acc[day]) {{ acc[day] = {{ Positivo: 0, Negativo: 0, Neutro: 0 }}; }} acc[day][curr.sentiment]++; return acc; }}, {{}}); const sortedDays = Object.keys(dailyCounts).sort(); charts.daily.data.labels = sortedDays.map(d => new Date(d+'T00:00:00').toLocaleDateString('es-CO', {{ year: 'numeric', month: 'short', day: 'numeric' }})); charts.daily.data.datasets = [ {{ label: 'Positivo', data: sortedDays.map(d => dailyCounts[d].Positivo), backgroundColor: '#28a745' }}, {{ label: 'Negativo', data: sortedDays.map(d => dailyCounts[d].Negativo), backgroundColor: '#dc3545' }}, {{ label: 'Neutro', data: sortedDays.map(d => dailyCounts[d].Neutro), backgroundColor: '#ffc107' }} ]; charts.daily.update(); const hourlyCounts = filteredData.reduce((acc, curr) => {{ const hour = curr.date.substring(0, 13) + ':00:00'; if (!acc[hour]) acc[hour] = {{ Positivo: 0, Negativo: 0, Neutro: 0, Total: 0 }}; acc[hour][curr.sentiment]++; acc[hour].Total++; return acc; }}, {{}}); const sortedHours = Object.keys(hourlyCounts).sort(); let cumulative = 0; const cumulativeData = sortedHours.map(h => {{ cumulative += hourlyCounts[h].Total; return cumulative; }}); charts.hourly.data.labels = sortedHours.map(h => new Date(h).toLocaleString('es-CO', {{ day: '2-digit', month: 'short', hour: '2-digit', minute:'2-digit' }})); charts.hourly.data.datasets = [ {{ label: 'Positivo', data: sortedHours.map(h => hourlyCounts[h].Positivo), backgroundColor: '#28a745', yAxisID: 'y' }}, {{ label: 'Negativo', data: sortedHours.map(h => hourlyCounts[h].Negativo), backgroundColor: '#dc3545', yAxisID: 'y' }}, {{ label: 'Neutro', data: sortedHours.map(h => hourlyCounts[h].Neutro), backgroundColor: '#ffc107', yAxisID: 'y' }}, {{ label: 'Acumulado', type: 'line', data: cumulativeData, borderColor: '#007bff', yAxisID: 'y1' }} ]; charts.hourly.update(); 
                }};
                
                const updatePostFilterOptions = () => {{ const selectedPlatform = platformFilter.value; const currentPostSelection = postFilter.value; let postsToShow = (selectedPlatform === 'Todas') ? allPostsData : allPostsData.filter(p => p.platform === selectedPlatform); postFilter.innerHTML = '<option value="Todas">Ver Todas las Pautas</option>'; postsToShow.forEach(p => {{ postFilter.innerHTML += `<option value="${{p.post_url}}">${{p.post_label}}</option>`; }}); if (postsToShow.some(p => p.url === currentPostSelection)) {{ postFilter.value = currentPostSelection; }} else {{ postFilter.value = 'Todas'; }} }};

                platformFilter.addEventListener('change', () => {{ updatePostFilterOptions(); postLinksCurrentPage = 1; updatePostLinks(); updateDashboard(); }});
                postFilter.addEventListener('change', updateDashboard);
                startDateInput.addEventListener('change', updateDashboard); startTimeInput.addEventListener('change', updateDashboard);
                endDateInput.addEventListener('change', updateDashboard); endTimeInput.addEventListener('change', updateDashboard);
                
                updatePostLinks();
                updateDashboard();
                // --- FIN DE MODIFICACIÓN 2 ---
            }});
        </script>
    </body>
    </html>
    """
    
    report_filename = 'index.html'
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Panel interactivo mejorado generado con éxito. Se guardó como '{report_filename}'.")

if __name__ == "__main__":
    run_report_generation()
