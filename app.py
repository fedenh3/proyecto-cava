import streamlit as st
import pandas as pd
import altair as alt
import cava_functions as cf

# --- Page Config ---
st.set_page_config(page_title="CAVA Stats", layout="wide", page_icon="⚽")

# --- Custom CSS ---
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .stMetric {
        background: rgba(255, 255, 255, 0.4);
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    h1, h2, h3 {
        color: #1b5e20;
        font-family: 'Outfit', sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #e8f5e9;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2e7d32 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# === MAIN APP ===
st.title("⚽ Estadísticas C.A. Victoriano Arenas")

# Sidebar: Filters
st.sidebar.header("Filtros")
df_torneos = cf.load_torneos()

# Filter by Temporada
temporadas = ["Todas"]
if not df_torneos.empty:
    temporadas += sorted(df_torneos['temporada'].unique().tolist(), reverse=True)

sel_temporada = st.sidebar.selectbox("Temporada", temporadas)

# Filter by Torneo
avail_torneos = df_torneos
if sel_temporada != "Todas":
    avail_torneos = df_torneos[df_torneos['temporada'] == sel_temporada]

# Torneo Options
torneo_opts_display = ["Todos"]
torneo_map = {}
if not avail_torneos.empty:
    torneo_map = dict(zip(avail_torneos['id'], avail_torneos['nombre']))
    sorted_ids = sorted(avail_torneos['id'].unique(), reverse=True)
    torneo_opts_display += [torneo_map[i] for i in sorted_ids]

sel_torneo_name = st.sidebar.selectbox("Torneo", torneo_opts_display)
sel_torneo_id = None
if sel_torneo_name != "Todos":
    for tid, name in torneo_map.items():
        if name == sel_torneo_name:
            sel_torneo_id = tid
            break

# === TABS ===
tab0, tab1, tab2, tab3 = st.tabs(["📈 Análisis", "📊 Resumen y Partidos", "🏃 Jugadores", "➕ Carga"])

# === TAB 0: ANÁLISIS (DASHBOARD) ===
with tab0:
    st.subheader("Dashboard General")
    st.write(f"Mostrando datos de: **{sel_temporada}** / **{sel_torneo_name}**")
    
    # 1. Global Metrics
    g_stats = cf.get_global_stats(sel_torneo_id, sel_temporada)
    
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("PJ", g_stats.get('pj', 0))
    m2.metric("PG", g_stats.get('pg', 0))
    m3.metric("PE", g_stats.get('pe', 0))
    m4.metric("PP", g_stats.get('pp', 0))
    m5.metric("G. Favor", g_stats.get('gf', 0))
    m6.metric("G. Contra", g_stats.get('gc', 0))
    
    st.divider()
    
    # 2. Charts
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.write("##### 🏆 Top Goleadores")
        df_top_goals = cf.get_top_stat("goles_marcados", 10, True)
        if not df_top_goals.empty:
            st.bar_chart(df_top_goals.set_index("Jugador"), color="#2e7d32")
        else:
            st.info("No hay datos de goles.")
            
    with col_chart2:
        st.write("##### ⏳ Top Presencias (Minutos)")
        df_top_mins = cf.get_top_stat("minutos_jugados", 10, False)
        if not df_top_mins.empty:
            st.bar_chart(df_top_mins.set_index("Jugador"), color="#1565c0")
        else:
            st.info("No hay datos de minutos.")
    
    # 3. Distribution Chart
    st.divider()
    st.write("##### 📊 Distribución de Resultados")
    if g_stats.get('pj', 0) > 0:
        res_data = pd.DataFrame({
            "Resultado": ["Ganados", "Empatados", "Perdidos"],
            "Cantidad": [g_stats['pg'], g_stats['pe'], g_stats['pp']]
        })
        chart_res = alt.Chart(res_data).mark_arc().encode(
            theta=alt.Theta(field="Cantidad", type="quantitative"),
            color=alt.Color(field="Resultado", type="nominal", scale=alt.Scale(range=["#4caf50", "#ffeb3b", "#f44336"])),
            tooltip=["Resultado", "Cantidad"]
        ).properties(width=400, height=300)
        st.altair_chart(chart_res, use_container_width=True)

# === TAB 1: Resumen y Partidos (PUBLIC) ===
with tab1:
    st.subheader("Historial de Partidos")
    df_p = cf.load_partidos(sel_torneo_id, sel_temporada)
    
    if not df_p.empty:
        st.dataframe(df_p, use_container_width=True, hide_index=True)
    else:
        st.info("No hay partidos registrados con esos filtros.")

# === TAB 2: Jugadores (PUBLIC) ===
with tab2:
    st.subheader("Estadísticas Individuales")
    df_jugadores = cf.load_jugadores()
    
    if not df_jugadores.empty:
        df_jugadores['nombre'] = df_jugadores['nombre'].fillna('')
        df_jugadores['apellido'] = df_jugadores['apellido'].fillna('')
        df_jugadores['full_name'] = df_jugadores['apellido'] + " " + df_jugadores['nombre']
        
        sel_player_name = st.selectbox("Buscar Jugador", df_jugadores['full_name'].unique())
        
        if sel_player_name:
            selected_row = df_jugadores[df_jugadores['full_name'] == sel_player_name].iloc[0]
            pid = int(selected_row['id'])
            
            init_g = selected_row.get('goles_iniciales', 0)
            if pd.isna(init_g): init_g = 0
            
            stats = cf.get_player_stats(pid, initial_goals=init_g)
            match_log = cf.get_player_matches(pid)
            
            if not stats.empty:
                 s = stats.iloc[0]
                 pj = int(s['pj']) if s['pj'] else 0
                 mins = int(s['minutos']) if s['minutos'] else 0
                 goles = int(s['goles']) if s['goles'] else 0
                 recibidos = int(s['recibidos']) if s.get('recibidos') else 0
                 titular = int(s['titular']) if s['titular'] else 0
                 
                 c1, c2, c3, c4, c5 = st.columns(5)
                 c1.metric("Partidos", pj)
                 c2.metric("Minutos", mins)
                 c3.metric("Goles", goles, help=f"Incluye {int(init_g)} goles históricos.")
                 c4.metric("Recibidos", recibidos)
                 c5.metric("Titular", titular)
            
            st.write("##### Historial del Jugador")
            if not match_log.empty:
                st.dataframe(match_log, use_container_width=True)
            else:
                st.info("No hay partidos registrados para este jugador.")
    else:
        st.warning("No hay jugadores cargados en la base de datos.")

# === TAB 3: Carga (SIMPLE) ===
with tab3:
    st.subheader("Carga de Partidos")
    
    with st.form("nuevo_partido"):
        col_a, col_b = st.columns(2)
        with col_a:
            fecha = st.date_input("Fecha del Partido")
            torneo_id = st.selectbox("Torneo", options=df_torneos['id'].tolist() if not df_torneos.empty else [], 
                                     format_func=lambda x: torneo_map.get(x, "N/A"))
            condicion = st.selectbox("Condición", ["L", "V", "N"])
        
        with col_b:
            rival_nombre = st.text_input("Rival (Nuevo o Existente)")
            gf = st.number_input("Goles a Favor", min_value=0, step=1)
            gc = st.number_input("Goles en Contra", min_value=0, step=1)
        
        submit_partido = st.form_submit_button("💾 Guardar Partido")
        
        if submit_partido:
            if not all([fecha, torneo_id, rival_nombre]):
                st.error("Completa todos los campos obligatorios")
            else:
                rival_id = cf.get_rival_id_by_name(rival_nombre)
                if not rival_id:
                    st.info(f"Rival '{rival_nombre}' no existe. Creándolo...")
                    rival_id = cf.create_rival(rival_nombre)
                
                if rival_id:
                    ok = cf.save_match(str(fecha), torneo_id, rival_id, condicion, gf, gc)
                    if ok:
                        st.success("✅ Partido guardado exitosamente!")
                    else:
                        st.error("❌ Error al guardar partido")
                else:
                    st.error("Error creando rival")
