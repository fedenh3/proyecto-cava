import streamlit as st
import pandas as pd
import altair as alt
import cava_functions as cf

# --- UI Layout ---
st.set_page_config(page_title="CAVA Stats", layout="wide")

st.title("⚽ Estadísticas C.A. Victoriano Arenas")

# Sidebar
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
    # Map ID to Name for display
    torneo_map = dict(zip(avail_torneos['id'], avail_torneos['nombre']))
    # Sort by ID descending typically or name? Let's use ID desc
    sorted_ids = sorted(avail_torneos['id'].unique(), reverse=True)
    torneo_opts_display += [torneo_map[i] for i in sorted_ids]

sel_torneo_name = st.sidebar.selectbox("Torneo", torneo_opts_display)
sel_torneo_id = None
if sel_torneo_name != "Todos":
    # Reverse lookup
    for tid, name in torneo_map.items():
        if name == sel_torneo_name:
            sel_torneo_id = tid
            break

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Resumen y Partidos", "🏃 Jugadores", "➕ Carga (Futuro)"])

with tab1:
    st.subheader("Historial de Partidos")
    df_partidos = cf.load_partidos(sel_torneo_id, sel_temporada if sel_temporada != "Todas" else None)
    
    # Metrics
    if not df_partidos.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Partidos Jugados", len(df_partidos))
        wins = len(df_partidos[df_partidos['goles_favor'] > df_partidos['goles_contra']])
        draws = len(df_partidos[df_partidos['goles_favor'] == df_partidos['goles_contra']])
        losses = len(df_partidos[df_partidos['goles_favor'] < df_partidos['goles_contra']])
        
        col2.metric("Victorias", wins)
        col3.metric("Empates", draws)
        col4.metric("Derrotas", losses)
    
        st.dataframe(df_partidos, use_container_width=True)
    else:
        st.info("No se encontraron partidos con los filtros seleccionados.")

with tab2:
    st.subheader("Estadísticas Individuales")
    df_jugadores = cf.load_jugadores()
    
    if not df_jugadores.empty:
        # Handle potential None values in text
        df_jugadores['nombre'] = df_jugadores['nombre'].fillna('')
        df_jugadores['apellido'] = df_jugadores['apellido'].fillna('')
        df_jugadores['full_name'] = df_jugadores['apellido'] + " " + df_jugadores['nombre']
        
        sel_player_name = st.selectbox("Buscar Jugador", df_jugadores['full_name'].unique())
        
        if sel_player_name:
            selected_row = df_jugadores[df_jugadores['full_name'] == sel_player_name].iloc[0]
            pid = int(selected_row['id'])
            
            # Get initial goals if any
            init_g = selected_row.get('goles_iniciales', 0)
            if pd.isna(init_g): init_g = 0
            
            stats = cf.get_player_stats(pid, initial_goals=init_g)
            match_log = cf.get_player_matches(pid)
            
            # Player KPIs
            if not stats.empty:
                 s = stats.iloc[0]
                 # Safely handle None valus from SQL SUM()
                 pj = int(s['pj']) if s['pj'] else 0
                 mins = int(s['minutos']) if s['minutos'] else 0
                 goles = int(s['goles']) if s['goles'] else 0
                 titular = int(s['titular']) if s['titular'] else 0
                 
                 c1, c2, c3, c4 = st.columns(4)
                 c1.metric("Partidos", pj)
                 c2.metric("Minutos", mins)
                 c3.metric("Goles", goles, help=f"Incluye {int(init_g)} goles históricos/iniciales.")
                 c4.metric("Titular", titular)
            
            st.write("##### Historial del Jugador")
            if not match_log.empty:
                st.dataframe(match_log, use_container_width=True)
            else:
                st.info("No hay partidos registrados para este jugador.")
    else:
        st.warning("No hay jugadores cargados en la base de datos.")

with tab3:
    st.header("Cargar Nuevo Partido")
    st.info("ℹ️ Usa esta pestaña desde tu PC local para agregar partidos a la base de datos.")
    
    with st.form("match_form"):
        c1, c2 = st.columns(2)
        
        # Date
        fecha = c1.date_input("Fecha del Partido")
        
        # Torneo Selector (Reload fresh)
        # Note: df_torneos is already loaded at top. 
        # If we just added one, we might need reload? Streamlit reruns script on interaction so it should be fine if we assume 'reload on refresh'.
        
        t_opts = df_torneos.copy()
        if not t_opts.empty:
            t_opts['display'] = t_opts['nombre'] + " (" + t_opts['temporada'] + ")"
            sid_torneo = c2.selectbox("Torneo", t_opts['id'], format_func=lambda x: t_opts[t_opts['id'] == x]['display'].values[0])
        else:
            sid_torneo = None
            c2.warning("No hay torneos. Carga torneos en DB primero.")
        
        c3, c4 = st.columns(2)
        
        df_rivales = cf.load_rivales()
        rival_names = []
        if not df_rivales.empty:
            rival_names = df_rivales['nombre'].tolist()
        
        rival_selection = c3.selectbox("Rival Existente", ["Seleccionar..."] + rival_names)
        
        new_rival = c3.text_input("O Nuevo Rival (Escribir nombre)", help="Si seleccionas un rival arriba, deja esto vacío.")
        
        condicion = c4.selectbox("Condición", ["L", "V", "N"])
        
        c5, c6 = st.columns(2)
        gf = c5.number_input("Goles CAVA", min_value=0, step=1)
        gc = c6.number_input("Goles Rival", min_value=0, step=1)
        
        submitted = st.form_submit_button("Guardar Partido")
        
        if submitted:
            # Logic to save
            real_rival_id = None
            
            # 1. Handle Rival
            if new_rival:
                # Check if exists
                existing_id = cf.get_rival_id_by_name(new_rival)
                if existing_id:
                     real_rival_id = existing_id
                else:
                     real_rival_id = cf.create_rival(new_rival)
                     if real_rival_id:
                         st.success(f"Rival '{new_rival}' creado.")
                     else:
                         st.error("Error creando rival.")
            elif rival_selection and rival_selection != "Seleccionar...":
                 real_rival_id = df_rivales[df_rivales['nombre'] == rival_selection].iloc[0]['id']
            
            if not real_rival_id:
                st.error("Por favor selecciona o escribe un rival.")
            elif not sid_torneo:
                st.error("Seleccione un torneo válido.")
            else:
                # 2. Insert Match
                ok = cf.save_match(fecha, sid_torneo, real_rival_id, condicion, gf, gc)
                if ok:
                    st.success("✅ Partido guardado exitosamente!")
                    # Rerun manually if needed, or let user refresh
                else:
                    st.error("Error al guardar el partido.")
