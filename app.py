import json
import os
import datetime
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CONFIGURACIÓN DE PÁGINA Y DISEÑO CSS ---
st.set_page_config(
    page_title="Preparador Concurso Docente 2026",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; color: #1E3A8A; font-weight: 700; text-align: center; margin-bottom: 0; }
    .sub-header { font-size: 1.1rem; color: #4B5563; text-align: center; margin-bottom: 2rem; }
    .metric-box { background-color: #F3F4F6; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    div[data-testid="stExpander"] { background-color: #F8FAFC; border-radius: 8px; border: 1px solid #E2E8F0; }
</style>
""", unsafe_allow_html=True)

# --- 2. CREDENCIALES Y USUARIOS (Totalmente ocultos para los visitantes) ---
API_KEY = "AQ.Ab8RN6IT6-t3t77qXYzFiVNyakzVr-4cTvUU9Skrh9E_o9r6Tw"
USUARIOS_PERMITIDOS = ["MARCELA2026", "LELY2026", "KARO2026", "CHECHO2026"]
CLAVE_SECRETA = "docente2026"
ARCHIVO_DATOS = "datos_estudio.json"

# --- 3. GESTIÓN DE DATOS PERSISTENTES ---
def cargar_datos():
    # Lee el archivo JSON si existe; si no, crea los perfiles en blanco
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {usr: {"simulacros": [], "temas": [], "puntaje": 0, "total": 0} for usr in USUARIOS_PERMITIDOS}

def guardar_datos(datos):
    # Escribe los avances en el archivo local para que aparezcan mañana
    with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

datos_globales = cargar_datos()

# --- 4. PANTALLA DE INICIO DE SESIÓN ---
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None

if st.session_state.usuario_actual is None:
    st.markdown('<p class="main-header">🎓 Plataforma de Estudio CNSC 2026</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Acceso exclusivo para el grupo de estudio</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.container(border=True):
            st.subheader("🔐 Iniciar Sesión")
            usuario_input = st.selectbox("Selecciona tu usuario:", [""] + USUARIOS_PERMITIDOS)
            clave_input = st.text_input("Contraseña:", type="password")
            
            if st.button("Entrar", type="primary"):
                if usuario_input in USUARIOS_PERMITIDOS and clave_input == CLAVE_SECRETA:
                    st.session_state.usuario_actual = usuario_input
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas.")
    st.stop() # Bloquea el resto de la app hasta que se inicie sesión

# --- 5. INICIALIZACIÓN DE LA APLICACIÓN PRIVADA ---
client = genai.Client(api_key=API_KEY)
usuario = st.session_state.usuario_actual

# Salvaguarda: si un usuario nuevo es agregado al código después, se le crea su espacio
if usuario not in datos_globales:
    datos_globales[usuario] = {"simulacros": [], "temas": [], "puntaje": 0, "total": 0}

if "pregunta_actual" not in st.session_state:
    st.session_state.pregunta_actual = None

# --- MENÚ LATERAL ---
with st.sidebar:
    st.markdown(f"### 👤 ¡Hola, {usuario}!")
    st.caption("Grupo de Estudio CNSC 2026")
    
    if st.button("Cerrar Sesión"):
        st.session_state.usuario_actual = None
        st.rerun()
        
    st.divider()
    modo = st.radio("Navegación:", ["📝 Simulacro de Preguntas", "📖 Estudio Guiado", "📊 Mi Progreso"])
    
    st.divider()
    area_evaluacion = st.selectbox(
        "Área actual:",
        [
            "Lectura Crítica",
            "Razonamiento Cuantitativo",
            "Competencias Pedagógicas (Decreto 1290, Ley 1620)",
            "Conocimientos Específicos: Tecnología e Informática",
            "Conocimientos Específicos: Primaria / General",
        ],
    )

st.markdown(f'<p class="main-header">{area_evaluacion}</p>', unsafe_allow_html=True)
st.divider()

# --- FUNCIONES DE IA ---
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
    prompt = f"Crea un módulo de estudio condensado y bien estructurado sobre: '{tema}' en el área de '{area}'. Utiliza viñetas, negritas y separa los conceptos claramente."
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
    )
    return response.text

# --- MÓDULO: SIMULACRO ---
if modo == "📝 Simulacro de Preguntas":
    col1, col2 = st.columns([3, 1])
    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <h4>Puntaje Acumulado</h4>
            <h2>{datos_globales[usuario]['puntaje']} / {datos_globales[usuario]['total']}</h2>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Generar Nueva Pregunta", type="primary"):
            with st.spinner("Redactando caso tipo CNSC..."):
                st.session_state.pregunta_actual = generar_pregunta_cnsc(area_evaluacion)
                st.rerun()

    with col1:
        if st.session_state.pregunta_actual:
            q = st.session_state.pregunta_actual
            with st.container(border=True):
                st.markdown(f"**Contexto:**\n\n>{q['contexto']}")
                st.markdown(f"**Enunciado:** {q['enunciado']}")
                
                opcion_seleccionada = st.radio(
                    "Selecciona tu respuesta:",
                    options=list(q["opciones"].keys()),
                    format_func=lambda x: f"{x}. {q['opciones'][x]}",
                    index=None
                )
                
                if st.button("Confirmar Respuesta"):
                    if opcion_seleccionada:
                        es_correcta = (opcion_seleccionada == q["respuesta_correcta"])
                        datos_globales[usuario]["total"] += 1
                        
                        if es_correcta:
                            st.success(f"¡Excelente, {usuario}! La correcta es la {q['respuesta_correcta']}.")
                            datos_globales[usuario]["puntaje"] += 1
                        else:
                            st.error(f"Incorrecto. Seleccionaste {opcion_seleccionada}, la correcta era la {q['respuesta_correcta']}.")
                        
                        with st.expander("📚 Ver Explicación Detallada", expanded=True):
                            st.info(q["justificacion"])
                        
                        # Guardar el registro en disco
                        registro = {
                            "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Área": area_evaluacion,
                            "Resultado": "✅ Correcto" if es_correcta else "❌ Incorrecto",
                            "Tema": q['contexto'][:60] + "..."
                        }
                        datos_globales[usuario]["simulacros"].append(registro)
                        guardar_datos(datos_globales)
                        st.session_state.pregunta_actual = None
                    else:
                        st.warning("Selecciona una opción antes de confirmar.")
        else:
            st.info("👈 Selecciona un área y haz clic en 'Generar Nueva Pregunta' en el panel derecho.")

# --- MÓDULO: ESTUDIO GUIADO ---
elif modo == "📖 Estudio Guiado":
    with st.container(border=True):
        tema_estudio = st.text_input("¿Qué concepto específico quieres repasar hoy?", placeholder="Ej: Ley 1620, Fracciones, Pensamiento Computacional...")
        
        if st.button("Construir Material de Estudio", type="primary") and tema_estudio:
            with st.spinner(f"Preparando apuntes de {tema_estudio}..."):
                st.markdown(generar_leccion_estudio(area_evaluacion, tema_estudio))
                
                # Guardar el registro en disco
                registro_tema = {
                    "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Área": area_evaluacion,
                    "Tema Estudiado": tema_estudio
                }
                datos_globales[usuario]["temas"].append(registro_tema)
                guardar_datos(datos_globales)

# --- MÓDULO: HISTORIAL ---
elif modo == "📊 Mi Progreso":
    st.write(f"Sigue tu evolución diaria desde el primer día de estudio, **{usuario}**.")
    
    tab1, tab2 = st.tabs(["📝 Historial de Simulacros", "📖 Temas Repasados"])
    
    with tab1:
        if datos_globales[usuario]["simulacros"]:
            df_simulacros = pd.DataFrame(datos_globales[usuario]["simulacros"])
            st.dataframe(df_simulacros.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Aún no tienes registros de simulacros.")
            
    with tab2:
        if datos_globales[usuario]["temas"]:
            df_temas = pd.DataFrame(datos_globales[usuario]["temas"])
            st.dataframe(df_temas.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Aún no has generado material de estudio.")
