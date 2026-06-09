import streamlit as st
from supabase import create_client, Client
import datetime

# --- 1. CONEXIÓN A LA BASE DE DATOS ---
@st.cache_resource
def iniciar_conexion():
    url = st.secrets["supabase"]["URL"]
    key = st.secrets["supabase"]["KEY"]
    return create_client(url, key)

supabase = iniciar_conexion()

st.title("LA ia.IA MODERNA")

# --- 2. MEMORIA DE SESIÓN ---
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None 
if 'codigo_familia' not in st.session_state:
    st.session_state.codigo_familia = None
# NUEVO: El mensajero para guardar avisos entre recargas de pantalla
if 'notificacion_ver' not in st.session_state:
    st.session_state.notificacion_ver = None

#---------------------------------------------------------------------
# PANTALLA 1: IDENTIFICACIÓN GLOBAL
#---------------------------------------------------------------------
if st.session_state.usuario_actual is None:
    st.write("Bienvenid@ a la aplicación de organización para la familia")
    
    codigo_ingresado = st.text_input("🔑 Código de Familia (ej. Garcia2026):", type="password")
    
    if codigo_ingresado:
        resp_miembros = supabase.table("miembros").select("nombre").eq("codigo_familia", codigo_ingresado).execute()
        nombres_bd = [m["nombre"] for m in resp_miembros.data]
        opciones_login = ["Selecciona..."] + nombres_bd
        
        st.divider()
        col_izq, col_der = st.columns(2)
        
        with col_izq:
            st.subheader("Ya tengo perfil")
            usuario_seleccionado = st.selectbox("Elige tu nombre:", opciones_login)

            if st.button("Entrar", key="btn_entrar"):
                if usuario_seleccionado != "Selecciona...":
                    st.session_state.usuario_actual = usuario_seleccionado
                    st.session_state.codigo_familia = codigo_ingresado
                    st.rerun()
                else:
                    st.warning("Selecciona tu nombre para entrar.")
                    
        with col_der:
            st.subheader("Soy nuev@")
            nuevo_familiar = st.text_input("Escribe tu nombre:")

            if st.button("Registrar y Entrar", key="btn_registrar"):
                if nuevo_familiar != "":
                    if nuevo_familiar not in nombres_bd:
                        supabase.table("miembros").insert({
                            "nombre": nuevo_familiar, 
                            "codigo_familia": codigo_ingresado
                        }).execute()
                        
                    st.session_state.usuario_actual = nuevo_familiar
                    st.session_state.codigo_familia = codigo_ingresado
                    st.rerun() 
                else:
                    st.warning("Escribe tu nombre primero.")

#----------------------------------------------------------------------
# PANTALLA 2: GESTOR DE TAREAS CENTRALIZADO
#----------------------------------------------------------------------
else:
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.write(f"¡Hola, **{st.session_state.usuario_actual}**! Sala: **{st.session_state.codigo_familia}**")
    with col_header2:
        if st.button("Cerrar sesión"):
            st.session_state.usuario_actual = None
            st.session_state.codigo_familia = None
            st.rerun() 
    
    st.divider()

    resp_miembros = supabase.table("miembros").select("nombre").eq("codigo_familia", st.session_state.codigo_familia).execute()
    lista_familiares_actual = ["Sin asignar"] + [m["nombre"] for m in resp_miembros.data]
    lista_edicion = ["Selecciona...", "Sin asignar"] + [m["nombre"] for m in resp_miembros.data]

    tab_añadir, tab_ver = st.tabs(["➕ Añadir Tarea", "📋 Ver Tareas"])

    # ==========================================
    # PESTAÑA 1: FORMULARIO DE CREACIÓN
    # ==========================================
    with tab_añadir:
        st.subheader("Crear una nueva tarea")
        with st.form(key="formulario_tareas", clear_on_submit=True):
            nueva_tarea = st.text_input("¿Qué necesitamos hacer?")
            
            quien_lo_hace = st.selectbox("👤 ¿Quién se encargará de esta tarea?", lista_familiares_actual)
            
            st.write("¿Quieres añadir límites de tiempo? (Modifica y marca la casilla para activarlos)")
            col_fecha, col_hora = st.columns(2)
            
            with col_fecha:
                fecha_limite = st.date_input("Selecciona Fecha")
                tiene_fecha = st.checkbox("📅 Activar y guardar esta fecha")
                
            with col_hora:
                hora_limite = st.time_input("Selecciona Hora", value=datetime.time(12, 0))
                tiene_hora = st.checkbox("⏰ Activar y guardar esta hora")
                
            st.write("")
            boton_añadir = st.form_submit_button("Añadir tarea a la base de datos")

            if boton_añadir:
                if nueva_tarea != "":
                    datos_tarea = {
                        "descripcion": nueva_tarea,
                        "completada": False,
                        "responsable": quien_lo_hace,
                        "fecha": str(fecha_limite) if tiene_fecha else "Sin fecha", 
                        "hora": str(hora_limite) if tiene_hora else "Sin hora",
                        "codigo_familia": st.session_state.codigo_familia
                    }
                    supabase.table("tareas").insert(datos_tarea).execute()
                    st.success("¡La tarea