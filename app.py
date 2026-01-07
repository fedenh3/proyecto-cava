import streamlit as st
import pandas as pd
import cava_functions as cf
import altair as alt

# Configuración inicial de la página (Título e ícono)
st.set_page_config(page_title="CAVA Stats", page_icon="⚽", layout="wide")

# Diseño estético (CSS) para una interfaz minimalista y profesional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ CAVA - Sistema de Estadísticas")

# Cargamos los datos básicos desde la lógica de la base de datos
df_torneos = cf.load_torneos()
df_jugadores = cf.load_jugadores()
temporadas = ["Todas"] + sorted(df_torneos['temporada'].unique().tolist(), reverse=True)

# BARRA LATERAL (Filtros globales para toda la App)
with st.sidebar:
    st.header("Filtros")
    sel_temp = st.selectbox("Temporada", temporadas)
    
    if sel_temp == "Todas":
        torneos_list = ["Todos"] + df_torneos['nombre'].unique().tolist()
    else:
        torneos_list = ["Todos"] + df_torneos[df_torneos['temporada'] == sel_temp]['nombre'].tolist()
    
    sel_torneo = st.selectbox("Torneo", torneos_list)

# Definición de las solapas (Tabs) principales
tab0, tab1, tab2 = st.tabs(["📈 Análisis", "🏟️ Partidos", "👤 Jugadores"])

# ---------------------------------------------------------
# SOLAPA 0: DASHBOARD DE ANÁLISIS GLOBAL
# ---------------------------------------------------------
with tab0:
    st.subheader("Resumen de Campaña")
    
    # Obtenemos las métricas globales filtradas
    tid = None
    if sel_torneo != "Todos":
        tid = df_torneos[df_torneos['nombre'] == sel_torneo]['id'].iloc[0]
        
    g_stats = cf.get_global_stats(torneo_id=tid, temporada=sel_temp)
    
    # Cálculo de Efectividad Global para la selección
    efectividad_val = 0
    if g_stats['pj'] > 0:
        pts = (g_stats['pg'] * 3) + g_stats['pe']
        efectividad_val = (pts / (g_stats['pj'] * 3)) * 100
    
    # Fila de tarjetas de métricas
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Partidos", g_stats['pj'])
    m2.metric("Ganados", g_stats['pg'])
    m3.metric("Empatados", g_stats['pe'])
    m4.metric("Perdidos", g_stats['pp'])
    m5.metric("Efectividad", f"{efectividad_val:.1f}%")
    m6.metric("Goles (F/C)", f"{g_stats['gf']} / {g_stats['gc']}")

    st.markdown("---")
    
    # --- FILA DE GRÁFICOS (3 Columnas) ---
    col_g1, col_g2, col_g3 = st.columns(3)
    
    with col_g1:
        st.markdown("##### Rendimiento")
        df_dist = cf.get_result_distribution(torneo_id=tid, temporada=sel_temp)
        if not df_dist.empty and df_dist['Cantidad'].sum() > 0:
            pie = alt.Chart(df_dist).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Cantidad", type="quantitative"),
                color=alt.Color(field="Resultado", scale=alt.Scale(domain=['Ganados', 'Empatados', 'Perdidos'], range=['#28a745', '#ffc107', '#dc3545'])),
                tooltip=["Resultado", "Cantidad"]
            )
            st.altair_chart(pie, use_container_width=True)
        else:
            st.info("Sin datos")

    with col_g2:
        st.markdown("##### Goleadores")
        # Pasamos los filtros a get_top_stat
        df_top_g = cf.get_top_stat("goles_marcados", limit=5, torneo_id=tid, temporada=sel_temp)
        if not df_top_g.empty:
            chart_g = alt.Chart(df_top_g).mark_bar(cornerRadiusEnd=4).encode(
                x=alt.X('Total:Q', title=None),
                y=alt.Y('Jugador:N', sort='-x', title=None),
                color=alt.value("#007bff"),
                tooltip=["Jugador", "Total"]
            )
            st.altair_chart(chart_g, use_container_width=True)
        else:
            st.info("Sin datos")

    with col_g3:
        st.markdown("##### Más Minutos")
        # Pasamos los filtros a get_top_stat (sum_initial=False para ver solo lo filtrado)
        df_top_m = cf.get_top_stat("minutos_jugados", limit=5, sum_initial=False, torneo_id=tid, temporada=sel_temp)
        if not df_top_m.empty:
            chart_m = alt.Chart(df_top_m).mark_bar(cornerRadiusEnd=4).encode(
                x=alt.X('Total:Q', title=None),
                y=alt.Y('Jugador:N', sort='-x', title=None),
                color=alt.value("#17a2b8"),
                tooltip=["Jugador", "Total"]
            )
            st.altair_chart(chart_m, use_container_width=True)
        else:
            st.info("Sin datos")
            
    # --- RACHA DE FORMA ---
    st.markdown("##### Racha Actual")
    df_form = cf.get_recent_form(limit=5, torneo_id=tid, temporada=sel_temp)
    if not df_form.empty:
        # Mostramos bolitas de colores (emojies)
        cols_form = st.columns(len(df_form))
        for idx, row in df_form.iterrows():
            with cols_form[idx]:
                st.markdown(f"<h2 style='text-align: center;'>{row['Resultado']}</h2>", unsafe_allow_html=True)
                st.caption(f"{row['rival']} ({row['goles_favor']}-{row['goles_contra']})")
    else:
        st.write("Sin partidos recientes.")

    st.divider()
    
    # Tabla de DTs filtrada
    st.markdown("##### Efectividad DTs")
    df_dt = cf.get_dt_stats(torneo_id=tid, temporada=sel_temp)
    if not df_dt.empty:
        df_dt_display = df_dt.copy()
        df_dt_display['Efectivid.'] = df_dt_display['Efectividad'].astype(str) + "%"
        st.dataframe(df_dt_display[['Tecnico', 'PJ', 'PG', 'Efectivid.', 'PTS']], 
                     use_container_width=True, hide_index=True)

    st.divider()
    st.write("**Historial contra Rivales**")
    df_rivales = cf.load_rivales()
    if not df_rivales.empty:
        sel_rival = st.selectbox("Seleccionar Rival para ver historial", df_rivales['nombre'].tolist())
        if sel_rival:
            rid = int(df_rivales[df_rivales['nombre'] == sel_rival]['id'].iloc[0])
            r_stats = cf.get_stats_against_rival(rid)
            
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("PJ", r_stats['pj'])
            c2.metric("PG", r_stats['pg'])
            c3.metric("PE", r_stats['pe'])
            c4.metric("PP", r_stats['pp'])
            c5.metric("GF", r_stats['gf'])
            c6.metric("GC", r_stats['gc'])
            
            # Un pequeño gráfico de torta para ver la distribución de resultados contra ese rival
            df_pie = pd.DataFrame({
                'Resultado': ['Ganados', 'Empatados', 'Perdidos'],
                'Cantidad': [r_stats['pg'], r_stats['pe'], r_stats['pp']]
            })
            pie_chart = alt.Chart(df_pie).mark_arc().encode(
                theta=alt.Theta(field="Cantidad", type="quantitative"),
                color=alt.Color(field="Resultado", type="nominal", scale=alt.Scale(range=['#28a745', '#ffc107', '#dc3545']))
            )
            st.altair_chart(pie_chart, use_container_width=True)

# ---------------------------------------------------------
# SOLAPA 1: LISTADO DE PARTIDOS
# ---------------------------------------------------------
with tab1:
    st.subheader("Historial de Partidos")
    df_partidos = cf.load_partidos(torneo_id=tid)
    
    if df_partidos.empty:
        st.info("No hay partidos registrados para los filtros seleccionados.")
    else:
        # Mostramos una tabla con el detalle de cada partido
        cols_show = ['nro_fecha', 'rival_nombre', 'condicion', 'goles_favor', 'goles_contra', 'torneo_nombre']
        st.dataframe(df_partidos[cols_show], use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# SOLAPA 2: FICHAS DE JUGADORES
# ---------------------------------------------------------
with tab2:
    st.subheader("Estadísticas por Jugador")
    
    if not df_jugadores.empty:
        df_jugadores['full_name'] = df_jugadores['apellido'] + ", " + df_jugadores['nombre']
        sel_player_name = st.selectbox("Seleccionar Jugador", sorted(df_jugadores['full_name'].tolist()))
        
        if sel_player_name:
            selected_row = df_jugadores[df_jugadores['full_name'] == sel_player_name].iloc[0]
            pid = int(selected_row['id'])
            
            # Traemos las estadísticas calculadas y el log de partidos
            stats = cf.get_player_stats(pid)
            match_log = cf.get_player_matches(pid)
            
            if not stats.empty:
                 s = stats.iloc[0]
                 pos_name = selected_row.get('posicion_nombre', 'N/A')
                 st.write(f"**Posición:** {pos_name}")
                 if pd.notna(selected_row['comentarios_gf']):
                     st.info(f"💡 {selected_row['comentarios_gf']}")
                 
                 pj = int(s['pj']) if s['pj'] else 0
                 mins = int(s['minutos']) if s['minutos'] else 0
                 goles = int(s['goles']) if s['goles'] else 0
                 recibidos = int(s['recibidos']) if s.get('recibidos') else 0
                 titular = int(s['titular']) if s['titular'] else 0
                 
                 c1, c2, c3, c4, c5 = st.columns(5)
                 c1.metric("Partidos", pj)
                 c2.metric("Minutos", mins)
                 c3.metric("Goles", goles)
                 c4.metric("Recibidos", recibidos)
                 c5.metric("Titular", titular)
                 
                 st.divider()
                 st.write("**Historial de partidos detallado**")
                 st.dataframe(match_log, hide_index=True, use_container_width=True)
