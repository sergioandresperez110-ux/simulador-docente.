import json
import datetime
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Preparador Concurso Docente 2026",
    page_icon="📚",
    layout="wide",
)

st.title("📚 Asistente IA - Concurso Docente CNSC 2026")

# --- INICIALIZACIÓN DEL HISTORIAL (BASE DE DATOS TEMPORAL) ---
if "pregunta_actual" not in st.session_state:
    st.session_state.pregunta_actual = None
if "puntaje" not in st.session_state:
    st.session_state.puntaje = 0
if "total_respondidas" not in st.session_state:
    st.session_state.total_respondidas = 0
if "historial_simulacros" not in st.session_state:
    st.session_state.historial_simulacros = []
if "historial_temas" not in st.session_state:
    st.session_state.historial_temas = []

with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input("Ingresa tu Gemini API Key:", type="password")
    
    st.divider()
    area_evaluacion = st.selectbox(
        "Área a evaluar:",
        [
            "Lectura Crítica",
            "Razonamiento Cuantitativo",
            "Competencias Pedagógicas (Decreto 1290, Ley 1620)",
            "Conocimientos Específicos: Tecnología e Informática",
            "Conocimientos Específicos: Primaria / General",
        ],
    )
    # NUEVO MODO AÑADIDO AL MENÚ
    modo = st.radio("Modo de uso:", ["Simulacro de Preguntas", "Estudio Guiado", "📊 Mi Progreso (Historial)"])

if not api_key:
    st.warning("Por favor, ingresa tu API Key de Google Gemini en el panel lateral para comenzar.")
    st.stop()

client = genai.Client(api_key=api_key)

def generar_pregunta_cnsc(area):
    system_instruction = """
    Eres un experto evaluador del Concurso Docente de Colombia (CNSC).
    Redacta preguntas de opción múltiple (A, B, C) mediante Casos o Juicio Situacional.
    Formato obligatorio en JSON:
    {
        "contexto": "Situación hipotética de aula o contexto.",
        "enunciado": "La pregunta a resolver.",
        "opciones": {"A": "Opción 1", "B": "Opción 2", "C": "Opción 3"},
        "respuesta_correcta": "A",
        "justificacion": "Explicación detallada de la respuesta correcta."
    }
    """
    prompt = f"Genera una pregunta inédita y compleja para la categoría: '{area}'."
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.3,
        ),
    )
    return json.loads(response.text)

def generar_leccion_estudio(area, tema):
    prompt = f"Crea un módulo de estudio condensado sobre: '{tema}' en el área de '{area}'. Incluye resumen normativo/conceptual, tips para el examen y un ejemplo resuelto."
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
    )
    return response.text

# --- MÓDULO 1: SIMULACRO ---
if modo == "Simulacro de Preguntas":
    st.subheader(f"Simulacro: {area_evaluacion}")
    col1, col2 = st.columns([3, 1])
    with col2:
        st.metric("Puntaje Acumulado", f"{st.session_state.puntaje} / {st.session_state.total_respondidas}")
        if st.button("Generar Nueva Pregunta", use_container_width=True):
            with st.spinner("Redactando caso tipo CNSC..."):
                st.session_state.pregunta_actual = generar_pregunta_cnsc(area_evaluacion)
                st.rerun()

    if st.session_state.pregunta_actual:
        q = st.session_state.pregunta_actual
        st.markdown(f"**Contexto:**\n\n>{q['contexto']}")
        st.markdown(f"**Enunciado:** {q['enunciado']}")
        
        opcion_seleccionada = st.radio(
            "Selecciona la opción:",
            options=list(q["opciones"].keys()),
            format_func=lambda x: f"{x}. {q['opciones'][x]}",
        )
        
        if st.button("Enviar Respuesta"):
            es_correcta = opcion_seleccionada == q["respuesta_correcta"]
            st.session_state.total_respondidas += 1
            
            if es_correcta:
                st.success(f"¡Correcto! La respuesta es la {q['respuesta_correcta']}.")
                st.session_state.puntaje += 1
            else:
                st.error(f"Incorrecto. Era la {q['respuesta_correcta']}.")
            st.info(f"**Justificación:** {q['justificacion']}")
            
            # GUARDAR EN EL HISTORIAL
            registro = {
                "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Área": area_evaluacion,
                "Resultado": "✅ Correcto" if es_correcta else "❌ Incorrecto",
                "Tema/Contexto": q['contexto'][:60] + "..."
            }
            st.session_state.historial_simulacros.append(registro)
            st.session_state.pregunta_actual = None # Limpia para obligar a generar otra
    else:
        st.info("Haz clic en 'Generar Nueva Pregunta' para iniciar el reto.")

# --- MÓDULO 2: ESTUDIO GUIADO ---
elif modo == "Estudio Guiado":
    st.subheader(f"Módulo de Estudio: {area_evaluacion}")
    tema_estudio = st.text_input("Tema específico a repasar:", placeholder="Ej: Ley 1620, Fracciones, Pensamiento Computacional...")
    
    if st.button("Generar Material de Estudio") and tema_estudio:
        with st.spinner("Estructurando contenido..."):
            contenido = generar_leccion_estudio(area_evaluacion, tema_estudio)
            st.markdown(contenido)
            
            # GUARDAR EN EL HISTORIAL
            registro_tema = {
                "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Área": area_evaluacion,
                "Tema Estudiado": tema_estudio
            }
            st.session_state.historial_temas.append(registro_tema)

# --- MÓDULO 3: HISTORIAL Y TRAZABILIDAD ---
elif modo == "📊 Mi Progreso (Historial)":
    st.subheader("Trazabilidad de Estudio")
    st.write("Monitorea tu rendimiento para identificar las áreas del Concurso Docente que necesitan más refuerzo.")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("### 📝 Simulacros Realizados")
        if st.session_state.historial_simulacros:
            df_simulacros = pd.DataFrame(st.session_state.historial_simulacros)
            st.dataframe(df_simulacros, use_container_width=True)
        else:
            st.info("Aún no has respondido preguntas de simulacro.")
            
    with col_b:
        st.markdown("### 📖 Temas Estudiados")
        if st.session_state.historial_temas:
            df_temas = pd.DataFrame(st.session_state.historial_temas)
            st.dataframe(df_temas, use_container_width=True)
        else:
            st.info("Aún no has generado material de estudio.")
