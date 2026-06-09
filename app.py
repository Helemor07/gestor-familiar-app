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

# --- 2. MEMORIA DE SESIÓN (Solo para saber si estamos logueados) ---
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None 
if 'codigo_familia' not in st.session_state:
    st.session_state.codigo_familia = None

#---------------------------------------------------------------------
# PANTALLA 1: IDENTIFICACIÓN GLOBAL
#---------------------------------------------------------------------
if st.session_state.usuario_actual is None:
    st.write("Bienvenid@ a la aplicación de organización para la familia")
    
    # 1. Pedimos la llave de la casa primero
    codigo_ingresado = st.text_input("🔑 Código de Familia (ej. Garcia2026):", type="password")
    
    # 2. Si escriben un código, descargamos la lista de familiares de la nube
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
                    # Lo guardamos en la NUBE para que el resto de móviles lo vean
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
# PANTALLA 2: GESTOR DE TAREAS AVANZADO
#----------------------------------------------------------------------
else:
    st.write(f"¡Hola, **{st.session_state.usuario_actual}**! Estás en la sala: **{st.session_state.codigo_familia}**")

    if st.button("Cerrar sesión"):
        st.session_state.usuario_actual = None
        st.session_state.codigo_familia = None
        st.rerun() 
    
    # --- FORMULARIO CON FECHAS OPCIONALES ---
    with st.form(key="formulario_tareas", clear_on_submit=True):
        nueva_tarea = st.text_input("¿Qué necesitamos hacer?")
        
        # Una casilla para decidir si queremos ponerle límite o es una compra general
        tiene_fecha = st.checkbox("⏰ Esta tarea tiene una fecha/hora límite")

        col_fecha, col_hora = st.columns(2)
        with col_fecha:
            fecha_limite = st.date_input("Fecha límite")
        with col_hora:
            hora_limite = st.time_input("Hora límite")
            
        boton_añadir = st.form_submit_button("Añadir tarea")

        if boton_añadir:
            if nueva_tarea != "":
                # Si han marcado la casilla, guardamos la fecha. Si no, guardamos un texto aviso.
                fecha_str = str(fecha_limite) if tiene_fecha else "Sin fecha"
                hora_str = str(hora_limite) if tiene_fecha else "Sin hora"
                
                datos_tarea = {
                     "descripcion": nueva_tarea,
                     "completada": False,
                     "responsable": "Sin asignar", 
                     "fecha": fecha_str, 
                     "hora": hora_str,
                     "codigo_familia": st.session_state.codigo_familia
                }
                supabase.table("tareas").insert(datos_tarea).execute()
                st.success("¡Tarea añadida a vuestra lista!")
                st.rerun() 
                
    st.subheader("Tareas pendientes:")

    # --- DESCARGAMOS LOS NOMBRES ACTUALIZADOS PARA PODER ASIGNAR ---
    resp_miembros = supabase.table("miembros").select("nombre").eq("codigo_familia", st.session_state.codigo_familia).execute()
    lista_familiares_actual = ["Selecciona..."] + [m["nombre"] for m in resp_miembros.data]

    # --- LEER DESDE LA NUBE ---
    respuesta = supabase.table("tareas").select("*").eq("codigo_familia", st.session_state.codigo_familia).execute()
    
    for tarea in respuesta.data:
        if not tarea["completada"]:
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.write(f"**{tarea['descripcion']}**")
                # Solo mostramos los relojes si realmente tiene fecha
                if tarea['fecha'] != "Sin fecha":
                    st.caption(f"📅 {tarea['fecha']} ⏰ {tarea['hora']}")
                else:
                    st.caption("Libre de horario")

            with col2:
                if tarea["responsable"] == "Sin asignar": 
                    seleccion = st.selectbox ("¿Quién va?", lista_familiares_actual, key=f"asignar_{tarea['id']}")
                    if seleccion != "Selecciona...":
                        supabase.table("tareas").update({"responsable": seleccion}).eq("id", tarea["id"]).execute()
                        st.rerun() 
                else:
                    st.info(f"{tarea['responsable']}")

            with col3:
                if st.button("✅ Hecho", key=f"hecho_{tarea['id']}"):
                    supabase.table("tareas").update({"completada": True}).eq("id", tarea["id"]).execute()
                    st.rerun() 
            
            # --- NUEVO: MENÚ DESPLEGABLE PARA MODIFICAR FECHAS ---
            # Si se cambia una cita médica, pueden abrir este panel y editarla
            with st.expander("✏️ Editar fecha/hora"):
                col_f, col_h, col_b = st.columns(3)
                with col_f:
                    n_fecha = st.date_input("Nueva fecha", key=f"nf_{tarea['id']}")
                with col_h:
                    n_hora = st.time_input("Nueva hora", key=f"nh_{tarea['id']}")
                with col_b:
                    st.write("") # Espaciador para alinear el botón con las cajas
                    if st.button("Guardar cambios", key=f"bsave_{tarea['id']}"):
                        supabase.table("tareas").update({"fecha": str(n_fecha), "hora": str(n_hora)}).eq("id", tarea["id"]).execute()
                        st.rerun()
                
                # Botón de rescate por si quieren quitarle la fecha a una tarea que ya la tenía
                if st.button("Quitar límite de tiempo", key=f"bquit_{tarea['id']}"):
                    supabase.table("tareas").update({"fecha": "Sin fecha", "hora": "Sin hora"}).eq("id", tarea["id"]).execute()
                    st.rerun()