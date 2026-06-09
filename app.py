import streamlit as st
from supabase import create_client, Client

# --- 1. CONEXIÓN A LA BASE DE DATOS ---
@st.cache_resource
def iniciar_conexion():
    url = st.secrets["supabase"]["URL"]
    key = st.secrets["supabase"]["KEY"]
    return create_client(url, key)

supabase = iniciar_conexion()

st.title("LA ia.IA MODERNA")

# --- 2. MEMORIA DE USUARIO Y FAMILIA ---
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None 
if 'codigo_familia' not in st.session_state:
    st.session_state.codigo_familia = None # NUEVA MEMORIA PARA LA HABITACIÓN
if 'familiares' not in st.session_state:
    st.session_state.familiares = ["Selecciona..."]

#---------------------------------------------------------------------
# PANTALLA 1: IDENTIFICACIÓN Y REGISTRO (Ahora con columnas)
#---------------------------------------------------------------------
if st.session_state.usuario_actual is None:
    st.write("Bienvenid@ a la aplicación de organización para la familia")
    
    # 1. Todo el mundo necesita la llave de la casa
    codigo_ingresado = st.text_input("🔑 Código de Familia (ej. Garcia2026):", type="password")
    
    st.divider()
    
    # Dividimos la pantalla en dos mitades para un diseño más limpio
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        st.subheader("Ya tengo perfil")
        usuario_seleccionado = st.selectbox("Elige tu nombre:", st.session_state.familiares)

        if st.button("Entrar", key="btn_entrar"):
            if usuario_seleccionado != "Selecciona..." and codigo_ingresado != "":
                st.session_state.usuario_actual = usuario_seleccionado
                st.session_state.codigo_familia = codigo_ingresado
                st.rerun()
            else:
                st.warning("Selecciona tu nombre y escribe el Código de Familia.")
                
    with col_der:
        st.subheader("Soy nuev@")
        nuevo_familiar = st.text_input("Escribe tu nombre:")

        if st.button("Registrar y Entrar", key="btn_registrar"):
            if nuevo_familiar != "" and codigo_ingresado != "":
                if nuevo_familiar not in st.session_state.familiares:
                    st.session_state.familiares.append(nuevo_familiar)
                st.session_state.usuario_actual = nuevo_familiar
                st.session_state.codigo_familia = codigo_ingresado
                st.rerun() 
            else:
                st.warning("Escribe tu nombre y el Código de Familia.")

#----------------------------------------------------------------------
# PANTALLA 2: GESTOR DE TAREAS PRIVADO
#----------------------------------------------------------------------
else:
    # Mostramos en qué habitación estamos
    st.write(f"¡Hola, **{st.session_state.usuario_actual}**! Estás en la sala de la familia: **{st.session_state.codigo_familia}**")

    if st.button("Cerrar sesión"):
        st.session_state.usuario_actual = None
        st.session_state.codigo_familia = None
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
                datos_tarea = {
                     "descripcion": nueva_tarea,
                     "completada": False,
                     "responsable": "Sin asignar", 
                     "fecha": str(fecha_limite), 
                     "hora": str(hora_limite),
                     "codigo_familia": st.session_state.codigo_familia # INYECTAMOS LA ETIQUETA
                }
                supabase.table("tareas").insert(datos_tarea).execute()
                st.success(f"¡Has añadido: '{nueva_tarea}' a vuestra lista privada!")
                st.rerun() 
                
    st.subheader("Tareas pendientes:")

    # --- LEER DESDE LA NUBE (FILTRADO POR FAMILIA) ---
    # La instrucción .eq() es el filtro mágico que aísla vuestros datos
    respuesta = supabase.table("tareas").select("*").eq("codigo_familia", st.session_state.codigo_familia).execute()
    lista_tareas_nube = respuesta.data

    for tarea in lista_tareas_nube:
        if not tarea["completada"]:
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.write(f"**{tarea['descripcion']}**")
                st.caption(f"📅 {tarea['fecha']} ⏰ {tarea['hora']}")

            with col2:
                if tarea["responsable"] == "Sin asignar": 
                    seleccion = st.selectbox ("¿Quién va?", st.session_state.familiares, key=f"asignar_{tarea['id']}")
                    if seleccion != "Selecciona...":
                        supabase.table("tareas").update({"responsable": seleccion}).eq("id", tarea["id"]).execute()
                        st.rerun() 
                else:
                    st.info(f"{tarea['responsable']}")

            with col3:
                if st.button("✅ Hecho", key=f"hecho_{tarea['id']}"):
                    supabase.table("tareas").update({"completada": True}).eq("id", tarea["id"]).execute()
                    st.rerun()