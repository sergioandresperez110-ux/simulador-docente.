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
    .temario-card { background-color: rgba(255, 255, 255, 0.03); border: 1px solid #334155; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .stTextInput>div>div>input { border-radius: 8px; }
    .link-list { margin-top: 10px; padding-left: 20px; }
    .resultado-box { background-color: #F0FDF4; border-left: 5px solid #22C55E; padding: 20px; border-radius: 8px; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

# --- 2. CREDENCIALES Y MAPA EXACTO DE DOCUMENTOS ---
API_KEY = "AQ.Ab8RN6IT6-t3t77qXYzFiVNyakzVr-4cTvUU9Skrh9E_o9r6Tw"
USUARIOS_PERMITIDOS = ["MARCELA2026", "LELY2026", "KARO2026", "CHECHO2026"]
CLAVE_SECRETA = "docente2026"
ARCHIVO_DATOS = "datos_estudio_maestro_v5.json"

BIBLIOTECA_ESPECIFICA = {
    "Aptitud Numérica": [
        "https://drive.google.com/file/d/1Egd7aH0tH4zZEPYxRn5mx3ybbbMIP5c5/view?usp=sharing",
        "https://drive.google.com/file/d/1qZY6h0TJtwsgd5OLFqYYvT-bX2nE9bsg/view?usp=sharing",
        "https://drive.google.com/file/d/1BpDRyk-YMYGlUYCLcACZ4XqEoCwmYpHj/view?usp=sharing",
        "https://drive.google.com/file/d/1C-G_-ZCUXYco1-UXaPkHBMUku5fogHND/view?usp=sharing",
        "https://drive.google.com/file/d/1zE8UhhVrRgJaxBYrdufKRRjoNcX62GKY/view?usp=sharing",
        "https://drive.google.com/file/d/1YTsI18oi-A1KKgkG20kl5ndVbhy98P24/view?usp=sharing",
        "https://drive.google.com/file/d/1cagSZH7Iuh_uX1jO0cVW7U9CAj2j_DTV/view?usp=sharing"
    ],
    "Aptitud Verbal": [
        "https://drive.google.com/file/d/1TKm0OLhdmzGf49jCXc6cAjhIv5WLDd51/view?usp=sharing",
        "https://drive.google.com/file/d/12wof-_M6lZjFA5zhRLLKFDR7sYc-N5eG/view?usp=sharing",
        "https://drive.google.com/file/d/11zvg5XF_acqN_QughE5q0dKVBxjfffOO/view?usp=sharing",
        "https://drive.google.com/file/d/1v0thrQ1E591S4WN8R6tNn1-gHty5m_YD/view?usp=sharing",
        "https://drive.google.com/file/d/1He89LzxdKeAIYTOL-gz1GN6aOq06It6g/view?usp=sharing",
        "https://drive.google.com/file/d/1-ezo6Nc-OQk6xtyAviPtCCm1IWN5cmhP/view?usp=sharing",
        "https://drive.google.com/file/d/1XQYSFjhqvNjOCWIyF2vlkmCXoe0l35q0/view?usp=sharing"
    ],
    "Legislación y Pedagogía": [
        "https://drive.google.com/file/d/1XiFzhOT2PqgTJkQFpDw7xxORGImxx9eZ/view?usp=sharing",
        "https://drive.google.com/file/d/1t7EdXUBpoDhSuxbKli0JHBX0aq6tqrbq/view?usp=sharing",
        "https://drive.google.com/file/d/1JKBVhWP1MxNleGBs_wrnkhk2phUDe_UF/view?usp=sharing",
        "https://drive.google.com/file/d/1zxGPqEZzxHihSJe2uPNwRAlEGPHkfiPj/view?usp=sharing",
        "https://drive.google.com/file/d/1VfX_aBH-8aA_tvB9TbZEP66wVcd7fAW4/view?usp=sharing"
    ],
    "Tecnología e Informática": [
        "https://docs.google.com/document/d/1KXsLDV_48tQnphfTedD2GesfhoztrDBW/edit?usp=sharing",
        "https://docs.google.com/document/d/1l5gyiJJXAT0x2xwAgQox1gQo24fLXjEp/edit?usp=sharing",
        "https://drive.google.com/file/d/15MtwY1NPnKhbLo_7uY_uCE8R83HWiNJq/view?usp=sharing"
    ],
    "Psicotécnica": [
        "https://drive.google.com/file/d/1o1iyEAq9MgkvsiyqpkaWSpnd5Xx731-d/view?usp=sharing",
        "https://drive.google.com/file/d/13jBZlJFzm4Zr54tXaZwJMNalyJt0fQMT/view?usp=sharing",
        "https://drive.google.com/file/d/1q9N39H0hPiGrHVsi6U2jU7kyE6mSIMSE/view?usp=sharing"
    ]
}

def obtener_enlaces_por_area(area):
    area_lower = area.lower()
    if "numérica" in area_lower or "cuantitativo" in area_lower or "matematicas" in area_lower:
        return BIBLIOTECA_ESPECIFICA["Aptitud Numérica"], "Aptitud Numérica"
    elif "verbal" in area_lower or "lectura" in area_lower:
        return BIBLIOTECA_ESPECIFICA["Aptitud Verbal"], "Aptitud Verbal"
    elif "pedag" in area_lower or "legislación" in area_lower or "ley" in area_lower or "decreto" in area_lower or "casos" in area_lower:
        return BIBLIOTECA_ESPECIFICA["Legislación y Pedagogía"], "Legislación y Pedagogía"
    elif "tecnolog" in area_lower or "informática" in area_lower:
        return BIBLIOTECA_ESPECIFICA["Tecnología e Informática"], "Tecnología e Informática"
    elif "psicot" in area_lower:
        return BIBLIOTECA_ESPECIFICA["Psicotécnica"], "Prueba Psicotécnica"
    else:
        return [BIBLIOTECA_ESPECIFICA["Legislación y Pedagogía"][0]], "Documento General"

def renderizar_caja_documentos(enlaces, nombre_cat):
    html_links = "".join([f"<li><a href='{link}' target='_blank'>📄 Documento Oficial de Estudio {i+1}</a></li>" for i, link in enumerate(enlaces[:5])])
    return f"""
    <div class="norma-box">
        <b>🔍 Respaldo Oficial ({nombre_cat}):</b> Estudia este tema directamente desde tus archivos exactos:
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

# Inicializar variables de estado
for key in ["examen_activo", "tema_activo", "contenido_tema", "links_activos", "preguntas_mini", "resultado_mini"]:
    if key not in st.session_state:
        st.session_state[key] = None

if "respuestas_mini" not in st.session_state: st.session_state.respuestas_mini = {}

# --- MENÚ LATERAL ---
with st.sidebar:
    st.markdown(f"### 👨‍🏫 Docente: {usuario}")
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.usuario_actual = None
        st.rerun()
    st.divider()
    modo = st.radio("Navegación:", [
        "🗺️ Temario Oficial y Ruta", 
        "📖 Generador de Lecciones (Con Ejemplos)", 
        "📝 Simulacro Oficial (20 Preg. + Tiempo)", 
        "📅 Historial y Progreso"
    ])
    st.divider()
    area_evaluacion = st.selectbox(
        "Área de Enfoque Actual:",
        [
            "1. Aptitud Numérica (Razonamiento Cuantitativo)",
            "2. Aptitud Verbal (Lectura Crítica)",
            "3. Competencias Pedagógicas y Legislación (Leyes y Casos)",
            "4. Conocimientos Específicos: Tecnología e Informática",
            "5. Prueba Psicotécnica"
        ]
    )

# --- PROMPTS MAESTROS ---
PROMPT_TEORIA = """
Actúa como el mejor preparador matemático y pedagógico para el Concurso Docente de Colombia.
Redacta una clase magistral sobre el tema: '{tema}'.

ESTRUCTURA ESTRICTA Y OBLIGATORIA QUE DEBES SEGUIR:
1. EXPLICACIÓN PROFUNDA: Nada de conceptos superficiales. Explica cómo funciona y para qué sirve en la prueba.
2. EJEMPLOS APLICADOS (PASO A PASO): 
   - Si el tema es matemático (Regla de 3, porcentajes, ecuaciones), MUESTRA LA OPERACIÓN MATEMÁTICA paso a paso. Desglosa los números.
   - Si el tema es pedagógico/legal, plantea una situación de aula real y explica cómo resolverla basándose en la norma.
"""

INSTRUCCION_MINI_JSON = """
Eres un evaluador experto de la CNSC. Genera EXACTAMENTE 10 preguntas de opción múltiple exclusivas del tema solicitado.
Devuelve ÚNICAMENTE un arreglo JSON.
Las justificaciones DEBEN ser detalladas, con una explicación lógica y matemática paso a paso (si aplica) o basada estrictamente en la normatividad educativa real colombiana.
Formato:
[
  {
    "id": 1,
    "contexto": "Situación o problema...",
    "enunciado": "Pregunta...",
    "opciones": {"A": "...", "B": "...", "C": "..."},
    "correcta": "A",
    "justificacion": "Explicación lógica paso a paso o citando la norma que sustenta la respuesta correcta...",
    "cita_legal": "Documento, Ley, o Principio Matemático"
  }
]
"""

def generar_modulo_completo(tema_completo):
    """Función unificada para generar la teoría y el JSON interactivo"""
    st.session_state.resultado_mini = None
    st.session_state.respuestas_mini = {}
    
    with st.spinner("1/2: Redactando teoría y ejemplos matemáticos/pedagógicos paso a paso..."):
        resp_texto = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=PROMPT_TEORIA.format(tema=tema_completo)
        )
    
    with st.spinner("2/2: Diseñando minisimulacro interactivo de 10 preguntas exclusivas del tema..."):
        try:
            resp_json = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=f"Genera 10 preguntas interactivas sobre: {tema_completo}",
                config=types.GenerateContentConfig(
                    system_instruction=INSTRUCCION_MINI_JSON,
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )
            st.session_state.preguntas_mini = json.loads(resp_json.text)
        except Exception as e:
            st.error("Hubo un error generando las preguntas interactivas. Se mostrará solo la teoría.")
            st.session_state.preguntas_mini = None

    enlaces, nom_cat = obtener_enlaces_por_area(tema_completo)
    st.session_state.tema_activo = tema_completo
    st.session_state.contenido_tema = resp_texto.text
    st.session_state.links_activos = renderizar_caja_documentos(enlaces, nom_cat)
    
    fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    datos_globales[usuario]["diario_estudio"][f"{fecha_hoy} - {tema_completo}"] = resp_texto.text
    guardar_datos(datos_globales)

def renderizar_mini_simulacro():
    """Muestra el quiz de 10 preguntas y lo califica"""
    st.divider()
    st.markdown('<div class="header-title">📝 MINISIMULACRO INTERACTIVO (10 Preguntas)</div>', unsafe_allow_html=True)
    st.write("Aplica lo que acabas de estudiar. Al finalizar, la IA te dará el puntaje y las explicaciones lógicas paso a paso.")
    
    if st.session_state.preguntas_mini and not st.session_state.resultado_mini:
        with st.form("mini_form"):
            for p in st.session_state.preguntas_mini:
                st.markdown(f"**{p['id']}. {p['enunciado']}**")
                if p['contexto'] and p['contexto'] != "...":
                    st.caption(f"Contexto: {p['contexto']}")
                st.session_state.respuestas_mini[p['id']] = st.radio(
                    "Selecciona:", options=list(p["opciones"].keys()),
                    format_func=lambda x: f"{x}) {p['opciones'][x]}", key=f"mq_{p['id']}", index=None
                )
                st.write("---")
            
            if st.form_submit_button("📥 Calificar Minisimulacro", type="primary"):
                puntaje = 0
                revision = []
                for p in st.session_state.preguntas_mini:
                    resp = st.session_state.respuestas_mini[p['id']]
                    if resp == p['correcta']: puntaje += 1
                    revision.append({
                        "Pregunta": p['enunciado'], "Tu Respuesta": resp or "No respondida", 
                        "Correcta": p['correcta'], "Justificación": p['justificacion'], "Base": p.get('cita_legal', 'N/A')
                    })
                
                st.session_state.resultado_mini = {"puntaje": puntaje, "total": 10, "revision": revision}
                st.rerun()

    if st.session_state.resultado_mini:
        res = st.session_state.resultado_mini
        st.markdown(f"""
        <div class="resultado-box">
            <h2>📊 Puntaje Obtenido: {res['puntaje']} / {res['total']}</h2>
            <p>Revisa la justificación lógica, matemática o normativa de cada pregunta a continuación:</p>
        </div>
        """, unsafe_allow_html=True)
        
        for i, r in enumerate(res['revision']):
            with st.expander(f"Pregunta {i+1} | Tu opción: {r['Tu Respuesta']} | Correcta: {r['Correcta']}"):
                st.write(f"**Explicación Lógica/Paso a Paso:** {r['Justificación']}")
                st.info(f"**Fundamento/Documento:** {r['Base']}")
        
        if st.button("🔄 Volver a estudiar este tema o cerrar resultados"):
            st.session_state.resultado_mini = None
            st.session_state.respuestas_mini = {}
            st.rerun()

# --- MÓDULO 1: TEMARIO OFICIAL Y RUTA ---
if modo == "🗺️ Temario Oficial y Ruta":
    st.markdown('<div class="header-title">🗺️ Temario Oficial del Concurso Docente 2026</div>', unsafe_allow_html=True)
    
    temario_oficial = [
        {"categoria": "Aptitud Numérica", "sub": "Porcentajes, Regla de 3, Sucesiones, Ecuaciones, Gráficas."},
        {"categoria": "Aptitud Verbal", "sub": "Sinónimos, Antónimos, Comprensión lectora, Oraciones lógicas."},
        {"categoria": "Legislación y Pedagogía", "sub": "Ley 115, Ley 1098, Ley 1620, Decreto 1290, Decreto 1421, Guías 31 y 34."},
        {"categoria": "Casos de Aula", "sub": "Juicio Situacional y Práctica Pedagógica."}
    ]
    
    for item in temario_oficial:
        st.markdown(f"<div class='temario-card'><h4>{item['categoria']}</h4><p>{item['sub']}</p></div>", unsafe_allow_html=True)
        if st.button(f"🚀 Estudiar a fondo: {item['categoria']}", key=f"gen_{item['categoria']}"):
            generar_modulo_completo(f"{item['categoria']} - {item['sub']}")
            st.rerun()

    if st.session_state.contenido_tema:
        st.markdown(st.session_state.links_activos, unsafe_allow_html=True)
        st.markdown(st.session_state.contenido_tema)
        renderizar_mini_simulacro()

# --- MÓDULO 2: GENERADOR DE LECCIONES (CON EJEMPLOS) ---
elif modo == "📖 Generador de Lecciones (Con Ejemplos)":
    st.markdown(f'<div class="header-title">📖 Clase Magistral: {area_evaluacion}</div>', unsafe_allow_html=True)
    tema_especifico = st.text_input("Ingresa el tema exacto que quieres estudiar hoy (Ej: Regla de 3 compuesta, Ley 1620 casos...):")
    
    if st.button(f"📚 Generar Clase, Ejemplos y Simulacro", type="primary"):
        tema_busqueda = f"{area_evaluacion} - {tema_especifico}" if tema_especifico else area_evaluacion
        generar_modulo_completo(tema_busqueda)
        st.rerun()

    if st.session_state.contenido_tema:
        st.markdown(st.session_state.links_activos, unsafe_allow_html=True)
        st.markdown(st.session_state.contenido_tema)
        renderizar_mini_simulacro()

# --- MÓDULO 3: SIMULACRO OFICIAL ---
elif modo == "📝 Simulacro Oficial (20 Preg. + Tiempo)":
    st.markdown(f'<div class="header-title">📝 Simulacro de Prueba Escrita - {area_evaluacion}</div>', unsafe_allow_html=True)
    
    if st.button("🚀 Iniciar Simulacro Oficial (20 Preguntas)", type="primary"):
        st.session_state.examen_activo = None
        if "resultado_ultimo_examen" in st.session_state: del st.session_state.resultado_ultimo_examen
        
        with st.spinner(f"Construyendo 20 preguntas avanzadas para: {area_evaluacion}..."):
            sys_inst = f"""Eres un evaluador de la CNSC. Genera 20 preguntas complejas de opción múltiple exclusivas de '{area_evaluacion}'. Devuelve SOLO JSON: [ {{"id": 1, "contexto": "...", "enunciado": "...", "opciones": {{"A": ".", "B": ".", "C": "."}}, "correcta": "A", "justificacion": "...", "cita_legal": "..."}} ]"""
            try:
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents="Genera 20 preguntas",
                    config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json", temperature=0.8)
                )
                st.session_state.examen_activo = json.loads(response.text)
                st.session_state.respuestas_usuario = {}
            except Exception:
                st.error("Error al compilar. Vuelve a intentar.")

    if st.session_state.examen_activo:
        preguntas = st.session_state.examen_activo
        with st.form("form_ex"):
            for p in preguntas:
                st.markdown(f"<div class='pregunta-card'><b>Pregunta {p.get('id', '*')}</b><br><br><i>{p['contexto']}</i><br><br><b>{p['enunciado']}</b></div>", unsafe_allow_html=True)
                st.session_state.respuestas_usuario[p['id']] = st.radio("Selecciona:", options=list(p["opciones"].keys()), format_func=lambda x: f"{x}) {p['opciones'][x]}", key=f"q_{p['id']}", index=None)
                st.write("---")
            
            if st.form_submit_button("📥 Entregar Prueba", type="primary"):
                puntaje = 0
                revision = []
                for p in preguntas:
                    resp = st.session_state.respuestas_usuario[p['id']]
                    if resp == p['correcta']: puntaje += 1
                    revision.append({"Pregunta": p['enunciado'], "Tu Respuesta": resp or "N/A", "Correcta": p['correcta'], "Justificación": p['justificacion'], "Base": p.get('cita_legal', 'N/A')})
                
                reg = {"Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "Área": area_evaluacion, "Puntaje": puntaje, "Total": len(preguntas), "Efectividad": round((puntaje/len(preguntas))*100, 1)}
                datos_globales[usuario]["historial_examenes"].append(reg)
                guardar_datos(datos_globales)
                st.session_state.resultado_ultimo_examen = {"puntaje": puntaje, "total": len(preguntas), "revision": revision}
                st.rerun()

    if "resultado_ultimo_examen" in st.session_state:
        res = st.session_state.resultado_ultimo_examen
        st.success(f"📊 Calificación: {res['puntaje']} / {res['total']}")
        enlaces, nom_cat = obtener_enlaces_por_area(area_evaluacion)
        for i, r in enumerate(res['revision']):
            with st.expander(f"Pregunta {i+1} | Tu opción: {r['Tu Respuesta']} | Correcta: {r['Correcta']}"):
                st.write(f"**Justificación:** {r['Justificación']}")
                st.info(f"**Sustento:** {r['Base']} | [📂 Verificar en {nom_cat}]({enlaces[0]})")

# --- MÓDULO 4: HISTORIAL ---
elif modo == "📅 Historial y Progreso":
    st.markdown('<div class="header-title">📅 Historial Diario y Estadísticas</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📚 Diario de Estudio (Contenido Exacto)", "📈 Gráficas"])
    
    with tab1:
        diario = datos_globales[usuario].get("diario_estudio", {})
        if diario:
            sesion = st.selectbox("Selecciona la fecha estudiada:", list(diario.keys())[::-1])
            if sesion:
                enlaces, nom_cat = obtener_enlaces_por_area(sesion)
                st.markdown(renderizar_caja_documentos(enlaces, nom_cat), unsafe_allow_html=True)
                st.markdown(diario[sesion])
        else:
            st.info("No hay sesiones guardadas.")
            
    with tab2:
        examenes = datos_globales[usuario].get("historial_examenes", [])
        if examenes:
            df = pd.DataFrame(examenes)
            col1, col2 = st.columns(2)
            with col1: st.metric("Simulacros", len(df))
            with col2: st.metric("Efectividad Promedio", f"{df['Efectividad'].mean():.1f}%")
            st.line_chart(df, y="Efectividad", x="Fecha", use_container_width=True)
            st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("No hay simulacros.")
