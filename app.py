import streamlit as st
from supabase import create_client, Client

# --- 1. CONEXIÓN A LA BASE DE DATOS
#usamos cache para que la web no se conecte desde cero cada vez que se pulsa un botój
@st.cache_resource
def iniciar_conexion():
    url = st.secrets["supabase"]["URL"]
    key = st.secrets["supabase"]["KEY"]
    return create_client(url, key)
supabase = iniciar_conexion()
#introducción web:
st.title("LA ia.IA MODERNA")

# --- 2. MEMORIA DE USUARIO (Esta sí se queda en la web) ---
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None 

if 'familiares' not in st.session_state:
    st.session_state.familiares = ["Selecciona..."]

#---------------------------------------------------------------------
# PANTALLA 1: IDENTIFICACIÓN Y REGISTRO
#---------------------------------------------------------------------
if st.session_state.usuario_actual is None:
    st.write("Bienvenid@ a la aplicación de organización para la familia")

    st.subheader("Ya tengo perfil")
    usuario_seleccionado = st.selectbox("Elige tu nombre:", st.session_state.familiares)

    if st.button("Entrar"):
        if usuario_seleccionado != "Selecciona...":
            st.session_state.usuario_actual = usuario_seleccionado
            st.rerun()
        else:
            st.warning("Selecciona tu nombre o crea uno nuevo abajo.")
    
    st.divider() 

    st.subheader("Soy nuev@")
    nuevo_familiar = st.text_input("Escribe tu nombre para registrarte:")

    if st.button("Registrar y Entrar"):
        if nuevo_familiar != "":
            if nuevo_familiar not in st.session_state.familiares:
                st.session_state.familiares.append(nuevo_familiar)
            st.session_state.usuario_actual = nuevo_familiar
            st.rerun() 
        else:
            st.warning("Por favor, identifícate primero")

#----------------------------------------------------------------------
# PANTALLA 2: GESTOR DE TAREAS EN LA NUBE
#----------------------------------------------------------------------
else:
    st.write(f"¡Hola, **{st.session_state.usuario_actual}**! Bienvenid@ a tu panel.")

    if st.button("Cerrar sesión"):
        st.session_state.usuario_actual = None
        st.rerun() 
    
    # --- FORMULARIO ---
    with st.form(key="formulario_tareas", clear_on_submit=True):
        nueva_tarea = st.text_input("¿Qué necesitamos hacer?")

        col_fecha, col_hora = st.columns(2)
        with col_fecha:
            fecha_limite = st.date_input("Fecha límite")
        with col_hora:
            hora_limite = st.time_input("Hora límite")
            
        boton_añadir = st.form_submit_button("Añadir nueva tarea")

        if boton_añadir:
            if nueva_tarea != "":
                # 1. Empaquetamos los datos exactamente con los nombres de tus columnas
                datos_tarea = {
                     "descripcion": nueva_tarea,
                     "completada": False,
                     "responsable": "Sin asignar", 
                     "fecha": str(fecha_limite), 
                     "hora": str(hora_limite) 
                }
                # 2. Los INYECTAMOS en Supabase
                supabase.table("tareas").insert(datos_tarea).execute()
                st.success(f"¡Has añadido: '{nueva_tarea}' a la nube!")
                st.rerun() # Recargamos para que aparezca abajo
                
    st.subheader("Tareas pendientes:")

    # --- LEER DESDE LA NUBE ---
    # Pedimos a Supabase todas las filas de la tabla "tareas"
    respuesta = supabase.table("tareas").select("*").execute()
    lista_tareas_nube = respuesta.data

    # Mostrar las tareas
    for tarea in lista_tareas_nube:
        if not tarea["completada"]:
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.write(f"**{tarea['descripcion']}**")
                st.caption(f"📅 {tarea['fecha']} ⏰ {tarea['hora']}")

            with col2:
                if tarea["responsable"] == "Sin asignar": 
                    # Usamos el ID real de Supabase como clave para que no haya fallos
                    seleccion = st.selectbox ("¿Quién va?", st.session_state.familiares, key=f"asignar_{tarea['id']}")
                    if seleccion != "Selecciona...":
                        # ACTUALIZAR EN SUPABASE: Cambiamos al responsable
                        supabase.table("tareas").update({"responsable": seleccion}).eq("id", tarea["id"]).execute()
                        st.rerun() 
                else:
                    st.info(f"{tarea['responsable']}")

            with col3:
                if st.button("✅ Hecho", key=f"hecho_{tarea['id']}"):
                    # ACTUALIZAR EN SUPABASE: Marcamos como completada
                    supabase.table("tareas").update({"completada": True}).eq("id", tarea["id"]).execute()
                    st.rerun()