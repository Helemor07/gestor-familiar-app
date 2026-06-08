import streamlit as st

#introducción web:
st.title("LA ia.IA MODERNA")
st.write("Bienvenid@ a la aplicación de organización para la familia")

# 1. Iniciamos la memoria
if 'lista_tareas' not in st.session_state:
    st.session_state.lista_tareas = []

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
boton_añadir = ("Añadir tarea nueva")

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

#lista de las personas de la casa
familiares = ["Selecciona...", "Helena", "Blanca", "Antonio", "Juanma", "Domingo"]

# 4. Mostrar las tareas
for i, tarea in enumerate(st.session_state.lista_tareas):
    if not tarea["completada"]:

        #dividimos el espacio en 3 columnas de diferentes tamaños
        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            #columna 1: Mostramos el texto de la tarea
            st.write(f"**{tarea['descripcion']}**")

        with col2:
            #columna 2: quién se encarga de la tarea
            if tarea["responsable"] == "Sin asignar": 
                #si no hay nadie, mostramos un menú desplegable
                seleccion = st.selectbox ("¿Quién va?", familiares, key=f"asignar_{i}")
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