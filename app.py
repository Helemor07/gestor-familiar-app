import streamlit as st

#introducción web:
st.title("LA ia.IA MODERNA")

# 1. Iniciamos la memoria
if 'lista_tareas' not in st.session_state:
    st.session_state.lista_tareas = []
if 'usuario_actual' not in st.session_state:
    st.session_state.usuraio_actual = None #"None" significa que nadie ha entrado aún

#memoria dinámica para los miembros de la familia
if 'familaires' not in st.session_state:
    #se empieza con la opción por defecto
    st.session_state.familaires = ["Selecciona..."]

#---------------------------------------------------------------------
#pantalla 1: identificación y registro
#---------------------------------------------------------------------
if st.session_state.usuario_actual is None:
    st.write("Bienvenid@ a la aplicación de organización para la familia")

    st.subheader("Ya tengo perfil")
    #el desplegable lee de la memoria dinámica, no de una lista fija
    usuario_seleccionado = st.selectbox("Elige tu nombre:", st.session_state.familiares)

    if st.button("Entrar"):
        if usuario_seleccionado != "Selecciona...":
            st.session_state.usuario_actual = usuario_seleccionado
            st.rerurn()
        else:
            st.warning("Selecciona tu nombre o crea uno nuevo abajo.")
    st.divider() #línea separadora visual

    st.subheader("Soy nuev@")
    #caja de texto para añadir nombres al sistema
    nuevo_familiar = st.text_input("Escribe tu nombre para registrarte:")

    if st.button("Registrar y Entrar"):
        if nuevo_familiar != "":
            #si el nombre no estaba en la lista, lo añadimos para siempre
            if nuevo_familiar not in st.session_state.familaires:
                st.session_state.familiares.append(nuevo_familiar)

            #directamente dejamos pasar adentro
            st.session_state.usuario_actual = nuevo_familiar
            st.rerurn()
        else:
            st.warning("Por favor, identifícate primero")

#----------------------------------------------------------------------
#pantalla 2: gestor de tareas
#----------------------------------------------------------------------

else:
    st.write(f"¡Hola, **{st.session_state.usuario_actual}** Bienvenid@ a tu panel.")

    if st.button("Cerrar sesión"):
        st.session_state.usuario_actual = None
        st.rerurn()
    
#----------------------------------------------------------------------
#creamos formulario que se limpia solo
#----------------------------------------------------------------------
with st.form(key="formulario_tareas", clear_on_submit=True):
    nueva_tarea = st.text_input("¿Qué necesitamos hacer?")

    #dividimos el espacio del formulario en dos para poner la fecha y la hora al lado
    col_fecha, col_hora = st.columns(2)
    with col_fecha:
        fecha_limite = st.date_input("Fecha límite")
    with col_hora:
        hora_limite = st.time_input("Hora límite")
        #Botón para añadir
    boton_añadir = st.form_submit_button("Añadir nueva tarea")

    if boton_añadir:
        if nueva_tarea != "":
            # creamos el diccionario
            tarea_estructurada = {
                 "descripcion": nueva_tarea,
                 "completada": False,
                 "responsable": "Sin asignar", #empezamos sin nadie asignado
                 "fecha": str(fecha_limite), #convertimos a texto
                 "hora": str(hora_limite) #convertimos a texto
            }
        # añadimos el diccionario (NO EL TEXTO SUELTO)
            st.session_state.lista_tareas.append(tarea_estructurada)
            st.success(f"¡Has añadido: '{nueva_tarea}' a la lista!")
#-----------------------------------------------------------------------
st.subheader("Tareas pendientes:")

#Mostrar las tareas
for i, tarea in enumerate(st.session_state.lista_tareas):
    if not tarea["completada"]:

        #dividimos el espacio en 3 columnas de diferentes tamaños
        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            #columna 1: Mostramos el texto, la fecha y la hora de la tarea
            st.write(f"**{tarea['descripcion']}**")
            st.caption(f"📅 {tarea['fecha']} ⏰ {tarea['hora']}")

        with col2:
            #columna 2: quién se encarga de la tarea
            if tarea["responsable"] == "Sin asignar": 
                #si no hay nadie, mostramos un menú desplegable
                seleccion = st.selectbox ("¿Quién va?", st.session_state.familiares, key=f"asignar_{i}")
                if seleccion != "Selecciona...":
                    tarea["responsable"] = seleccion
                    st.rerun() #recargamos para guardar el cambio
            else:
                #si ya hay alguien, mostramos su nombre en azul
                st.info(f"{tarea['responsable']}")

        with col3:
            #columna 3_ en vez de un checkbox, usamos un botón verde para terminarla
            if st.button("✅ Hecho", key=f"hecho_{i}"):
                tarea["completada"] = True
                st.rerun() # Fuerza a recargar la página al marcar