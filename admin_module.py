import streamlit as st
import pandas as pd
from datetime import date
import cava_functions as cf

def login_form():
    st.markdown("### 🔒 Acceso Restringido")
    
    with st.form("login"):
        user = st.text_input("Usuario")
        passw = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")
        
        if submitted:
            # Validar con DB
            ok, data = cf.login_user(user, passw)
            if ok:
                st.session_state['logged_in'] = True
                st.session_state['user_info'] = data
                st.success(f"¡Bienvenido {data.get('nombre')}!")
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

def render_match_loader():
    st.header("📝 Cargar Nuevo Partido")
    
    # 1. Datos del Partido
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Nro. Fecha", value=date.today())
        condicion = st.radio("Condición", ["Local", "Visitante"], horizontal=True)
        
    with col2:
        df_torneos = cf.load_torneos()
        torneo_opts = df_torneos['nombre'].tolist() if not df_torneos.empty else []
        if not torneo_opts:
            st.warning("⚠️ No hay torneos. Creá uno primero en 'Gestión de Datos'.")
            return
        sel_torneo = st.selectbox("Torneo", torneo_opts)
        
        df_rivales = cf.load_rivales()
        rival_opts = df_rivales['nombre'].tolist() if not df_rivales.empty else []
        if not rival_opts:
            st.warning("⚠️ No hay rivales. Agregá uno primero en 'Gestión de Datos'.")
            return
        sel_rival = st.selectbox("Rival", rival_opts)

    # DT del partido
    df_tecnicos = cf.load_tecnicos()
    tecnico_opts = ["Sin DT"] + (df_tecnicos['nombre'].tolist() if not df_tecnicos.empty else [])
    sel_tecnico = st.selectbox("Director Técnico", tecnico_opts)
    
    # Árbitro del partido
    df_arbitros = cf.load_arbitros()
    arbitro_opts = ["Sin árbitro"] + (df_arbitros['nombre'].tolist() if not df_arbitros.empty else [])
    sel_arbitro = st.selectbox("Árbitro", arbitro_opts)
        
    c1, c2 = st.columns(2)
    gf = c1.number_input("Goles A Favor", 0, 20, 0)
    gc = c2.number_input("Goles En Contra", 0, 20, 0)
    
    st.divider()
    
    # 2. Planilla de Jugadores
    st.subheader("📋 Planilla de Jugadores")
    st.info("Ingresa los minutos y estadísticas de quienes jugaron. Deja en 0 los que no.")
    
    # Cargar base de jugadores
    if 'base_players' not in st.session_state:
        df_j = cf.load_jugadores()
        # Preparamos el DF para edición
        if not df_j.empty:
            df_edit = df_j[['id', 'nombre', 'apellido', 'posicion_nombre']].copy()
            df_edit['minutos'] = 0
            df_edit['goles'] = 0
            df_edit['amarillas'] = 0
            df_edit['rojas'] = 0
            # Formato visual
            df_edit['Nombre Completo'] = df_edit['nombre'] + " " + df_edit['apellido']
            # Ordenamos por apellido
            df_edit = df_edit.sort_values('apellido')
            # Guardamos base
            st.session_state['base_players'] = df_edit
        else:
            st.warning("No hay jugadores en la base de datos. Agregá jugadores en 'Gestión de Datos'.")
            return

    # Usamos data_editor
    # Filtramos columnas para mostrar solo lo editable y el nombre
    df_input = st.session_state['base_players'][['id', 'Nombre Completo', 'posicion_nombre', 'minutos', 'goles', 'amarillas', 'rojas']]
    
    edited_df = st.data_editor(
        df_input, 
        column_config={
            "id": None, # Ocultar ID
            "Nombre Completo": st.column_config.TextColumn("Jugador", disabled=True),
            "posicion_nombre": st.column_config.TextColumn("Pos", disabled=True),
            "minutos": st.column_config.NumberColumn("Minutos", min_value=0, max_value=120, step=1, help="0 = No jugó"),
            "goles": st.column_config.NumberColumn("⚽ Goles", min_value=0, max_value=10),
            "amarillas": st.column_config.NumberColumn("🟨 Amarillas", min_value=0, max_value=2),
            "rojas": st.column_config.NumberColumn("🟥 Rojas", min_value=0, max_value=1),
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )
    
    if st.button("💾 Guardar Partido", type="primary"):
        # Validaciones
        goles_ingresados = edited_df['goles'].sum()
        if goles_ingresados != gf:
            st.error(f"⚠️ Error: Cargaste {goles_ingresados} goles en la planilla, pero el resultado dice {gf} a favor.")
            return
            
        # Preparar IDs
        try:
            tid = df_torneos[df_torneos['nombre'] == sel_torneo]['id'].iloc[0]
            rid = df_rivales[df_rivales['nombre'] == sel_rival]['id'].iloc[0]
            # Árbitro es opcional
            aid = None
            if sel_arbitro != "Sin árbitro" and not df_arbitros.empty:
                arb_row = df_arbitros[df_arbitros['nombre'] == sel_arbitro]
                if not arb_row.empty:
                    aid = int(arb_row['id'].iloc[0])
        except:
            st.error("Error identificando Torneo o Rival. Revisa la base de datos.")
            return

        match_data = {
            'id_torneo': int(tid),
            'id_rival': int(rid),
            'id_arbitro': aid,
            'fecha': str(fecha),
            'condicion': condicion[0], # 'L' o 'V'
            'gf': int(gf),
            'gc': int(gc)
        }
        
        success, msg = cf.save_match(match_data, edited_df)
        if success:
            st.balloons()
            st.success(msg)
            # Limpiar estado para recargar
            if 'base_players' in st.session_state:
                del st.session_state['base_players']
        else:
            st.error(f"Error al guardar: {msg}")

# ==============================================================================
# GESTIÓN DE DATOS
# ==============================================================================

def render_data_management():
    st.header("📊 Gestión de Datos")
    st.write("Administrá torneos, rivales, técnicos, árbitros y jugadores para preparar la temporada.")
    
    tabs = st.tabs(["📅 Torneos", "🏟️ Rivales", "👔 Técnicos", "⚖️ Árbitros", "👥 Jugadores"])
    
    # --- TAB TORNEOS ---
    with tabs[0]:
        st.subheader("Torneos")
        
        # Mostrar existentes
        df_torneos = cf.load_torneos()
        if not df_torneos.empty:
            st.dataframe(df_torneos[['nombre', 'temporada']], use_container_width=True, hide_index=True)
        else:
            st.info("No hay torneos registrados.")
        
        # Crear nuevo
        st.markdown("##### ➕ Crear Nuevo Torneo")
        with st.form("new_torneo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            t_nombre = col1.text_input("Nombre del Torneo", placeholder="Ej: Apertura")
            t_temp = col2.text_input("Temporada/Año", placeholder="Ej: 2026")
            
            if st.form_submit_button("Crear Torneo", type="primary"):
                if t_nombre and t_temp:
                    ok, msg = cf.create_torneo(t_nombre.strip(), t_temp.strip())
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Completá nombre y temporada")
    
    # --- TAB RIVALES ---
    with tabs[1]:
        st.subheader("Rivales / Equipos")
        
        df_rivales = cf.load_rivales()
        if not df_rivales.empty:
            st.dataframe(df_rivales[['nombre']], use_container_width=True, hide_index=True)
        else:
            st.info("No hay rivales registrados.")
        
        st.markdown("##### ➕ Agregar Nuevo Rival")
        with st.form("new_rival", clear_on_submit=True):
            r_nombre = st.text_input("Nombre del Equipo", placeholder="Ej: Club Atlético Rival")
            
            if st.form_submit_button("Agregar Rival", type="primary"):
                if r_nombre:
                    ok, msg = cf.create_rival(r_nombre.strip().upper())
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Ingresá el nombre del rival")
    
    # --- TAB TÉCNICOS ---
    with tabs[2]:
        st.subheader("Directores Técnicos")
        
        df_tecnicos = cf.load_tecnicos()
        if not df_tecnicos.empty:
            st.dataframe(df_tecnicos[['nombre']], use_container_width=True, hide_index=True)
        else:
            st.info("No hay técnicos registrados.")
        
        st.markdown("##### ➕ Agregar Nuevo Técnico")
        with st.form("new_tecnico", clear_on_submit=True):
            dt_nombre = st.text_input("Nombre Completo", placeholder="Ej: Juan Pérez")
            
            if st.form_submit_button("Agregar Técnico", type="primary"):
                if dt_nombre:
                    ok, msg = cf.create_tecnico(dt_nombre.strip())
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Ingresá el nombre del técnico")
    
    # --- TAB ÁRBITROS ---
    with tabs[3]:
        st.subheader("Árbitros")
        
        df_arbitros = cf.load_arbitros()
        if not df_arbitros.empty:
            st.dataframe(df_arbitros[['nombre']], use_container_width=True, hide_index=True)
        else:
            st.info("No hay árbitros registrados.")
        
        st.markdown("##### ➕ Agregar Nuevo Árbitro")
        with st.form("new_arbitro", clear_on_submit=True):
            arb_nombre = st.text_input("Nombre Completo", placeholder="Ej: Pablo Echavarría")
            
            if st.form_submit_button("Agregar Árbitro", type="primary"):
                if arb_nombre:
                    ok, msg = cf.create_arbitro(arb_nombre.strip())
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Ingresá el nombre del árbitro")
    
    # --- TAB JUGADORES ---
    with tabs[4]:
        st.subheader("Plantel de Jugadores")
        
        df_jugadores = cf.load_jugadores()
        df_posiciones = cf.load_posiciones()
        
        # Vista del plantel actual
        if not df_jugadores.empty:
            st.write(f"**Total: {len(df_jugadores)} jugadores**")
            df_show = df_jugadores[['apellido', 'nombre', 'posicion_nombre']].copy()
            df_show.columns = ['Apellido', 'Nombre', 'Posición']
            st.dataframe(df_show, use_container_width=True, hide_index=True, height=300)
        else:
            st.info("No hay jugadores en el plantel.")
        
        st.markdown("---")
        
        # Crear nuevo jugador
        st.markdown("##### ➕ Agregar Nuevo Jugador")
        with st.form("new_jugador", clear_on_submit=True):
            col1, col2 = st.columns(2)
            j_nombre = col1.text_input("Nombre", placeholder="Ej: Juan")
            j_apellido = col2.text_input("Apellido", placeholder="Ej: Pérez")
            
            pos_opts = ["Sin posición"] + (df_posiciones['nombre'].tolist() if not df_posiciones.empty else [])
            j_pos = st.selectbox("Posición", pos_opts)
            
            j_comentario = st.text_area("Comentarios (opcional)", placeholder="Notas sobre el jugador...")
            
            if st.form_submit_button("Agregar Jugador", type="primary"):
                if j_nombre and j_apellido:
                    # Obtener ID de posición
                    pos_id = None
                    if j_pos != "Sin posición" and not df_posiciones.empty:
                        pos_row = df_posiciones[df_posiciones['nombre'] == j_pos]
                        if not pos_row.empty:
                            pos_id = int(pos_row['id'].iloc[0])
                    
                    ok, msg = cf.create_jugador(
                        j_nombre.strip(), 
                        j_apellido.strip().upper(), 
                        pos_id,
                        j_comentario.strip() if j_comentario else None
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Completá nombre y apellido")
        
        # Crear nueva posición (oculto en expander)
        with st.expander("🏷️ Agregar nueva posición"):
            with st.form("new_posicion", clear_on_submit=True):
                p_nombre = st.text_input("Nombre de Posición", placeholder="Ej: DEL, VOL, DEF, ARQ...")
                if st.form_submit_button("Crear Posición"):
                    if p_nombre:
                        ok, msg = cf.create_posicion(p_nombre.strip().upper())
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

def render_user_mgmt():
    st.header("👥 Gestión de Usuarios")
    
    with st.expander("Crear Nuevo Administrador"):
        with st.form("new_user"):
            u_name = st.text_input("Nombre Real")
            u_user = st.text_input("Username")
            u_pass = st.text_input("Contraseña", type="password")
            
            if st.form_submit_button("Crear Usuario"):
                if u_user and u_pass:
                    ok, msg = cf.create_user(u_user, u_pass, u_name)
                    if ok: st.success(msg)
                    else: st.error(msg)
                else:
                    st.warning("Completa todos los campos")

def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        
    if not st.session_state['logged_in']:
        login_form()
    else:
        # Sidebar Admin
        st.sidebar.divider()
        st.sidebar.title("🛠️ Admin Panel")
        opt = st.sidebar.radio("Menú", ["📝 Cargar Partido", "📊 Gestión de Datos", "👥 Usuarios"])
        
        if st.sidebar.button("🚪 Cerrar Sesión"):
            st.session_state['logged_in'] = False
            if 'base_players' in st.session_state:
                del st.session_state['base_players']
            st.rerun()
            
        if opt == "📝 Cargar Partido":
            render_match_loader()
        elif opt == "📊 Gestión de Datos":
            render_data_management()
        elif opt == "👥 Usuarios":
            render_user_mgmt()

