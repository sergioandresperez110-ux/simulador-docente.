import json
import os
import datetime
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="Plataforma Experta CNSC 2026", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    .header-title { font-size: 2.2rem; font-weight: 800; border-bottom: 3px solid #3B82F6; padding-bottom: 10px; margin-bottom: 20px;}
    .norma-box { border-left: 5px solid #2563EB; padding: 15px; margin: 15px 0; background-color: rgba(37, 99, 235, 0.08); border-radius: 4px; }
    .pregunta-card { border: 1px solid #E2E8F0; padding: 20px; border-radius: 8px; margin-bottom: 15px; }
    .stTextInput>div>div>input { border-radius: 8px; }
    .link-list { margin-top: 10px; padding-left: 20px; }
    .resultado-box { background-color: #F0FDF4; border-left: 5px solid #22C55E; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .stButton>button { width: 100%; text-align: left; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 2. CREDENCIALES Y MAPA EXACTO DE DOCUMENTOS ---
API_KEY = "AQ.Ab8RN6IT6-t3t77qXYzFiVNyakzVr-4cTvUU9Skrh9E_o9r6Tw"
USUARIOS_PERMITIDOS = ["MARCELA2026", "LELY2026", "KARO2026", "CHECHO2026"]
CLAVE_SECRETA = "docente2026"
ARCHIVO_DATOS = "datos_estudio_maestro_v9.json"

BIBLIOTECA_ESPECIFICA = {
    "Aptitud Numérica": [
        "https://drive.google.com/file/d/1Egd7aH0tH4zZEPYxRn5mx3ybbbMIP5c5/view?usp=sharing",
        "https://drive.google.com/file/d/1qZY6h0TJtwsgd5OLFqYYvT-bX2nE9bsg/view?usp=sharing",
        "https://drive.google.com/file/d/1BpDRyk-YMYGlUYCLcACZ4XqEoCwmYpHj/view?usp=sharing",
        "https://drive.google.com/file/d/1C-G_-ZCUXYco1-UXaPkHBMUku5fogHND/view?usp=sharing",
        "https://drive.google.com/file/d/1zE8UhhVrRgJaxBYrdufKRRjoNcX62GKY/view?usp=sharing"
    ],
    "Aptitud Verbal": [
        "https://drive.google.com/file/d/1TKm0OLhdmzGf49jCXc6cAjhIv5WLDd51/view?usp=sharing",
        "https://drive.google.com/file/d/12wof-_M6lZjFA5zhRLLKFDR7sYc-N5eG/view?usp=sharing",
        "https://drive.google.com/file/d/11zvg5XF_acqN_QughE5q0dKVBxjfffOO/view?usp=sharing",
        "https://drive.google.com/file/d/1v0thrQ1E591S4WN8R6tNn1-gHty5m_YD/view?usp=sharing",
        "https://drive.google.com/file/d/1He89LzxdKeAIYTOL-gz1GN6aOq06It6g/view?usp=sharing"
    ],
    "Legislación Educativa": [
        "https://drive.google.com/file/d/1XiFzhOT2PqgTJkQFpDw7xxORGImxx9eZ/view?usp=sharing",
        "https://drive.google.com/file/d/1t7EdXUBpoDhSuxbKli0JHBX0aq6tqrbq/view?usp=sharing",
        "https://drive.google.com/file/d/1JKBVhWP1MxNleGBs_wrnkhk2phUDe_UF/view?usp=sharing",
        "https://drive.google.com/file/d/1XxToRrFgBjfK5NODMGDsB5a84lDXsRpy/view?usp=sharing"
    ],
    "Pedagogía": [
        "https://drive.google.com/file/d/1zxGPqEZzxHihSJe2uPNwRAlEGPHkfiPj/view?usp=sharing",
        "https://drive.google.com/file/d/1VfX_aBH-8aA_tvB9TbZEP66wVcd7fAW4/view?usp=sharing",
        "https://drive.google.com/file/d/14bU0pvjB0Q6mxE3N6WACXoNrW-Eq7GNu/view?usp=sharing",
        "https://drive.google.com/file/d/1cWhENR5TQVwrymzbNOggSzOzTrFirZRf/view?usp=sharing"
    ],
    "Psicotécnica y Casos": [
        "https://drive.google.com/file/d/1o1iyEAq9MgkvsiyqpkaWSpnd5Xx731-d/view?usp=sharing",
        "https://drive.google.com/file/d/13jBZlJFzm4Zr54tXaZwJMNalyJt0fQMT/view?usp=sharing",
        "https://drive.google.com/file/d/1q9N39H0hPiGrHVsi6U2jU7kyE6mSIMSE/view?usp=sharing",
        "https://drive.google.com/file/d/13C3BqLLw3ppoBVKJM5lDB-b54pfW8Zqz/view?usp=sharing"
    ],
    "Tecnología e Informática": [
        "https://docs.google.com/document/d/1KXsLDV_48tQnphfTedD2GesfhoztrDBW/edit?usp=sharing",
        "https://docs.google.com/document/d/1l5gyiJJXAT0x2xwAgQox1gQo24fLXjEp/edit?usp=sharing",
        "https://drive.google.com/file/d/15MtwY1NPnKhbLo_7uY_uCE8R83HWiNJq/view?usp=sharing"
    ]
}

def obtener_enlaces_por_area(area):
    area_lower = area.lower()
    if any(palabra in area_lower for palabra in ["porcentaje", "regla", "sucesion", "ecuacion", "abstracto", "grafica", "numérica"]):
        return BIBLIOTECA_ESPECIFICA["Aptitud Numérica"], "Aptitud Numérica"
    elif any(palabra in area_lower for palabra in ["sinonimo", "antonimo", "analogia", "lectora", "oraciones", "verbal"]):
        return BIBLIOTECA_ESPECIFICA["Aptitud Verbal"], "Aptitud Verbal"
    elif any(palabra in area_lower for palabra in ["ley", "decreto", "guia", "legislacion"]):
        return BIBLIOTECA_ESPECIFICA["Legislación Educativa"], "Legislación Educativa"
    elif any(palabra in area_lower for palabra in ["pedagogica", "funciones", "inclusion", "pedagogia"]):
        return BIBLIOTECA_ESPECIFICA["Pedagogía"], "Pedagogía"
    elif any(palabra in area_lower for palabra in ["tecnologia", "informatica"]):
        return BIBLIOTECA_ESPECIFICA["Tecnología e Informática"], "Tecnología e Informática"
    else:
        return BIBLIOTECA_ESPECIFICA["Psicotécnica y Casos"], "Psicotécnica y Casos"

def renderizar_caja_documentos(enlaces, nombre_cat):
    html_links = "".join([f"<li><a href='{link}' target='_blank'>📄 Documento de {nombre_cat} {i+1}</a></li>" for i, link in enumerate(enlaces)])
    return f"""
    <div class="norma-box">
        <b>🔍 Respaldo Oficial ({nombre_cat}):</b> Estudia este tema directamente desde tus archivos exactos de Drive:
        <ul class="link-list">
            {html_links}
        </ul>
    </div>
    """

# --- 3. BASE DE DATOS LOCAL ---
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {usr: {"historial_examenes": [], "diario_estudio": {}} for usr in USUARIOS_PERMITIDOS}

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

datos_globales = cargar_datos()

# --- 4. LOGIN ---
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None

if st.session_state.usuario_actual is None:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="header-title">🏛️ Acceso Seguro CNSC 2026</div>', unsafe_allow_html=True)
        usuario_input = st.text_input("Usuario (ID):").strip().upper()
        clave_input = st.text_input("Contraseña:", type="password")
        if st.button("Iniciar Sesión", type="primary", use_container_width=True):
            if usuario_input in USUARIOS_PERMITIDOS and clave_input == CLAVE_SECRETA:
                st.session_state.usuario_actual = usuario_input
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")
    st.stop()

client = genai.Client(api_key=API_KEY)
usuario = st.session_state.usuario_actual

for key in ["examen_activo", "tema_activo", "contenido_tema", "ejemplos_extra", "links_activos", "preguntas_mini", "resultado_mini"]:
    if key not in st.session_state:
        st.session_state[key] = None

if "respuestas_mini" not in st.session_state: st.session_state.respuestas_mini = {}

# --- MENÚ LATERAL ---
with st.sidebar:
    st.markdown(f"### 👨‍🏫 Docente: {usuario}")
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.usuario_actual = None
        st.rerun()
    st.divider()
    modo = st.radio("Navegación:", [
        "🗺️ Temario Detallado (Tema a Tema)", 
        "📝 Simulacro Oficial (20 Preguntas)", 
        "📅 Historial y Progreso"
    ])

# --- PROMPTS MAESTROS PURGADOS ---
PROMPT_TEORIA_ESPECIFICA = """
Actúa como un preparador experto de alto nivel para el Concurso Docente de Colombia.
Desarrolla una clase magistral EXCLUSIVAMENTE sobre este tema específico: '{tema}'.

REGLAS ESTRICTAS E INQUEBRANTABLES:
1. TEORÍA CLARA Y DIRECTA: Explica la lógica detrás del concepto.
2. VARIEDAD DE EJEMPLOS (MÍNIMO 3 DIFERENTES): Presenta al menos 3 problemas diferentes con niveles de dificultad progresiva.
3. PASO A PASO DETALLADO: Muestra el procedimiento matemático o legal línea por línea.
4. FORMATO OBLIGATORIO: ESTÁ ESTRICTAMENTE PROHIBIDO usar formato matemático complejo. Usa ÚNICAMENTE texto plano y espacios claros (ejemplo: 400 x 0.15 = 60) para que el texto sea completamente legible en la pantalla sin amontonarse.
"""

def obtener_instruccion_json(tema_exacto):
    return f"""
    Eres un evaluador de la CNSC. Genera EXACTAMENTE 10 preguntas complejas de opción múltiple exclusivas del tema: {tema_exacto}.
    Devuelve ÚNICAMENTE un arreglo JSON válido, sin bloques de código Markdown alrededor.
    Las justificaciones DEBEN ser detalladas en texto plano sin formato matemático complejo.
    Formato:
    [
      {{
        "id": 1,
        "contexto": "Situación...",
        "enunciado": "Pregunta...",
        "opciones": {{"A": "...", "B": "...", "C": "..."}},
        "correcta": "A",
        "justificacion": "Explicación lógica paso a paso usando texto simple...",
        "cita_legal": "Regla matemática o artículo legal"
      }}
    ]
    """

# --- FUNCIONES NÚCLEO ---
def generar_teoria_y_ejemplos(tema_exacto):
    st.session_state.preguntas_mini = None
    st.session_state.resultado_mini = None
    st.session_state.respuestas_mini = {}
    st.session_state.ejemplos_extra = None
    
    with st.spinner(f"Redactando clase y ejemplos paso a paso exclusivamente de {tema_exacto}..."):
        resp_texto = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=PROMPT_TEORIA_ESPECIFICA.format(tema=tema_exacto)
        )
    
    enlaces, nom_cat = obtener_enlaces_por_area(tema_exacto)
    st.session_state.tema_activo = tema_exacto
    st.session_state.contenido_tema = resp_texto.text
    st.session_state.links_activos = renderizar_caja_documentos(enlaces, nom_cat)
    
    fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    datos_globales[usuario]["diario_estudio"][f"{fecha_hoy} - {tema_exacto}"] = resp_texto.text
    guardar_datos(datos_globales)

def generar_mini_simulacro_json(tema_exacto):
    with st.spinner(f"Construyendo 10 preguntas interactivas tipo CNSC para: {tema_exacto}..."):
        try:
            resp_json = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=f"Genera 10 preguntas JSON puras sobre: {tema_exacto}. Solo entrega la lista de objetos JSON.",
                config=types.GenerateContentConfig(
                    system_instruction=obtener_instruccion_json(tema_exacto),
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )
            
            # Limpiador técnico estricto para extraer solo la estructura JSON
            texto_bruto = resp_json.text
            inicio_json = texto_bruto.find('[')
            fin_json = texto_bruto.rfind(']') + 1
            if inicio_json != -1 and fin_json != 0:
                texto_limpio = texto_bruto[inicio_json:fin_json]
            else:
                texto_limpio = texto_bruto.replace("```json", "").replace("
