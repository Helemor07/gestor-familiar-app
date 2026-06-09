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
    # Cabecera superior
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.write(f"¡Hola, **{st.session_state.usuario_actual}**! Sala: **{st.session_state.codigo_familia}**")
    with col_header2:
        if st.button("Cerrar sesión"):
            st.session_state.usuario_actual = None
            st.session_state.codigo_familia = None
            st.rerun() 
    
    st.divider()

    # --- CONSULTA CENTRALIZADA DE MIEMBROS ---
    # Colocamos esto aquí arriba para que AMBAS pestañas conozcan la lista de familiares actualizada
    resp_miembros = supabase.table("miembros").select("nombre").eq("codigo_familia", st.session_state.codigo_familia).execute()
    lista_familiares_actual = ["Sin asignar"] + [m["nombre"] for m in resp_miembros.data]
    lista_edicion = ["Selecciona...", "Sin asignar"] + [m["nombre"] for m in resp_miembros.data]

    # Organización en pestañas principales
    tab_añadir, tab_ver = st.tabs(["➕ Añadir Tarea", "📋 Ver Tareas"])

    # ==========================================
    # PESTAÑA 1: FORMULARIO DE CREACIÓN (CON ASIGNACIÓN COMPLETA)
    # ==========================================
    with tab_añadir:
        st.subheader("Crear una nueva tarea")
        with st.form(key="formulario_tareas", clear_on_submit=True):
            nueva_tarea = st.text_input("¿Qué necesitamos hacer?")
            
            # NUEVO: Selector para asignar responsable desde el primer momento
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
                        "responsable": quien_lo_hace, # GUARDAMOS EL NOMBRE SELECCIONADO
                        "fecha": str(fecha_limite) if tiene_fecha else "Sin fecha", 
                        "hora": str(hora_limite) if tiene_hora else "Sin hora",
                        "codigo_familia": st.session_state.codigo_familia
                    }
                    supabase.table("tareas").insert(datos_tarea).execute()
                    st.success(f"¡Tarea '{nueva_tarea}' asignada a {quien_lo_hace} con éxito!")
                    st.rerun()

    # ==========================================
    # PESTAÑA 2: VISUALIZACIÓN Y FILTRADO
    # ==========================================
    with tab_ver:
        # 1. Sistema de filtrado visual
        filtro = st.radio("Filtro de visualización:", ["Mostrar todas las tareas de la familia", "Solo las tareas que me tocan a mí"], horizontal=True)
        st.write("") 

        # 2. Descargar tareas de la nube
        respuesta = supabase.table("tareas").select("*").eq("codigo_familia", st.session_state.codigo_familia).execute()
        lista_tareas = respuesta.data

        # 3. Aplicar el filtro seleccionado
        if filtro == "Solo las tareas que me tocan a mí":
            lista_tareas = [t for t in lista_tareas if t["responsable"] == st.session_state.usuario_actual]

        # 4. Función para dibujar cada tarea
        def dibujar_tarea(tarea):
            if not tarea["completada"]:
                col_info, col_accion = st.columns([4, 1])
                
                with col_info:
                    responsable_tag = f" 👤 {tarea['responsable']}" if tarea['responsable'] != "Sin asignar" else " ⚠️ Sin asignar"
                    st.write(f"**{tarea['descripcion']}** ({responsable_tag})")
                    
                    tiempo_texto = ""
                    if tarea['fecha'] != "Sin fecha":
                        tiempo_texto += f"📅 {tarea['fecha']} "
                    if tarea['hora'] != "Sin hora":
                        tiempo_texto += f"⏰ {tarea['hora']}"
                    if tiempo_texto != "":
                        st.caption(tiempo_texto)

                with col_accion:
                    if st.button("✅ Hecho", key=f"hecho_{tarea['id']}"):
                        supabase.table("tareas").update({"completada": True}).eq("id", tarea["id"]).execute()
                        st.rerun() 
                
                # PANEL DE EDICIÓN Y BORRADO
                with st.expander("✏️ Modificar / Eliminar"):
                    n_desc = st.text_input("Editar descripción:", value=tarea["descripcion"], key=f"ed_{tarea['id']}")
                    
                    try:
                        idx_resp = lista_edicion.index(tarea["responsable"])
                    except ValueError:
                        idx_resp = 0
                    n_resp = st.selectbox("Cambiar responsable:", lista_edicion, index=idx_resp, key=f"er_{tarea['id']}")
                    
                    st.write("Ajustar límites de tiempo:")
                    col_ef, col_eh = st.columns(2)
                    
                    with col_ef:
                        e_tiene_f = st.checkbox("Tiene fecha", value=(tarea["fecha"] != "Sin fecha"), key=f"etf_{tarea['id']}")
                        try:
                            val_f = datetime.datetime.strptime(tarea["fecha"], "%Y-%m-%d").date()
                        except:
                            val_f = datetime.date.today()
                        n_fecha = st.date_input("Nueva fecha", value=val_f, key=f"nf_{tarea['id']}") if e_tiene_f else "Sin fecha"
                    
                    with col_eh:
                        e_tiene_h = st.checkbox("Tiene hora", value=(tarea["hora"] != "Sin hora"), key=f"eth_{tarea['id']}")
                        try:
                            val_h = datetime.datetime.strptime(tarea["hora"], "%H:%M:%S").time()
                        except:
                            val_h = datetime.time(12, 0)
                        n_hora = st.time_input("Nueva hora", value=val_h, key=f"nh_{tarea['id']}") if e_tiene_h else "Sin hora"
                    
                    st.write("")
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("💾 Guardar Cambios", key=f"bsave_{tarea['id']}", use_container_width=True):
                            cambios = {
                                "descripcion": n_desc,
                                "responsable": n_resp if n_resp != "Selecciona..." else "Sin asignar",
                                "fecha": str(n_fecha) if e_tiene_f else "Sin fecha",
                                "hora": str(n_hora) if e_tiene_h else "Sin hora"
                            }
                            supabase.table("tareas").update(cambios).eq("id", tarea["id"]).execute()
                            st.rerun()
                    with col_b2:
                        if st.button("🗑️ Eliminar Tarea", key=f"bdel_{tarea['id']}", use_container_width=True):
                            supabase.table("tareas").delete().eq("id", tarea["id"]).execute()
                            st.rerun()
                st.divider()

        # 5. Renderizar las tareas
        tareas_pendientes = [t for t in lista_tareas if not t["completada"]]
        if len(tareas_pendientes) == 0:
            st.info("No hay tareas pendientes en esta vista. ¡Todo al día! 🎉")
        else:
            for tarea in tareas_pendientes:
                dibujar_tarea(tarea)