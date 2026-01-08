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
        fecha = st.date_input("Fecha", value=date.today())
        condicion = st.radio("Condición", ["Local", "Visitante"], horizontal=True)
        
    with col2:
        df_torneos = cf.load_torneos()
        torneo_opts = df_torneos['nombre'].tolist() if not df_torneos.empty else []
        sel_torneo = st.selectbox("Torneo", torneo_opts)
        
        df_rivales = cf.load_rivales()
        rival_opts = df_rivales['nombre'].tolist() if not df_rivales.empty else []
        sel_rival = st.selectbox("Rival", rival_opts)
        
    c1, c2 = st.columns(2)
    gf = c1.number_input("Goles A Favor", 0, 20, 0)
    gc = c2.number_input("Goles En Contra", 0, 20, 0)
    
    st.divider()
    
    # 2. Planilla de Jugadores
    st.subheader("📋 Planilla de Jugadores")
    st.info("Ingresa los minutos y estadísticas de quienes jugaron. Deja en 0 los que no.")
    
    # Cargar base de jugadores
    if 'editor_df' not in st.session_state:
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
            st.warning("No hay jugadores en la base de datos")
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
            "minutos": st.column_config.NumberColumn("Minutos", min_value=0, max_value=90, step=1, help="0 = No jugó"),
            "goles": st.column_config.NumberColumn("⚽ Goles", min_value=0, max_value=10),
            "amarillas": st.column_config.NumberColumn("🟨 Amarillas", min_value=0, max_value=2),
            "rojas": st.column_config.NumberColumn("🟥 Rojas", min_value=0, max_value=1),
        },
        hide_index=True,
        use_container_width=True,
        height=600
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
        except:
            st.error("Error identificando Torneo o Rival. Revisa la base de datos.")
            return

        match_data = {
            'id_torneo': int(tid),
            'id_rival': int(rid),
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
            del st.session_state['base_players']
        else:
            st.error(f"Error al guardar: {msg}")

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
        opt = st.sidebar.radio("Menú", ["Cargar Partido", "Usuarios"])
        
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state['logged_in'] = False
            st.rerun()
            
        if opt == "Cargar Partido":
            render_match_loader()
        elif opt == "Usuarios":
            render_user_mgmt()
