import json
import os
import datetime
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS AVANZADOS ---
st.set_page_config(page_title="Plataforma Experta CNSC 2026", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    .main { background-color: #F8FAFC; }
    .header-title { 
        font-size: 2.4rem; 
        font-weight: 800; 
        color: #1E3A8A; 
        border-bottom: 4px solid #3B82F6; 
        padding-bottom: 12px; 
        margin-bottom: 25px;
    }
    .norma-box { 
        border-left: 6px solid #2563EB; 
        padding: 18px; 
        margin: 20px 0; 
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); 
        border-radius: 8px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .pregunta-card { 
        border: 1px solid #E2E8F0; 
        padding: 22px; 
        border-radius: 10px; 
        margin-bottom: 20px; 
        background-color: #FFFFFF;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .resultado-box { 
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); 
        border-left: 6px solid #22C55E; 
        padding: 22px; 
        border-radius: 10px; 
        margin: 20px 0; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-1px;);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
    }
    div.stExpander {
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        background-color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CREDENCIALES Y MAPA DE DOCUMENTOS ---
API_KEY = "AQ.Ab8RN6IT6-t3t77qXYzFiVNyakzVr-4cTvUU9Skrh9E_o9r6Tw"
USUARIOS_PERMITIDOS = ["MARCELA2026", "LELY2026", "KARO2026", "CHECHO2026", "ISABELLA2026", "CARLA2026"]
CLAVE_SECRETA = "docente2026"
ARCHIVO_DATOS = "datos_estudio_maestro_v14.json"

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

def renderizar_caja_documentos(enlaces, nombre_cat, tema):
    html_links = "".join([f"<li><a href='{link}' target='_blank'>📄 Documento oficial de {nombre_cat} {i+1}</a></li>" for i, link in enumerate(enlaces)])
    query_yt = tema.replace(" ", "+")
    url_yt = f"https://www.youtube.com/results?search_query=concurso+docente+colombia+{query_yt}"
    url_yt_general = f"https://www.youtube.com/results?search_query=preparacion+cnsc+{nombre_cat.lower()}"
    
    return f"""
    <div class="norma-box">
        <b>🔍 Respaldo Oficial ({nombre_cat}):</b> Estudia este tema directamente desde tus archivos exactos de Drive:
        <ul class="link-list">
            {html_links}
        </ul>
        <hr style="margin: 10px 0; border: 0; border-top: 1px solid #93C5FD;">
        <b>📺 Videotutoriales y Clases de Apoyo en YouTube:</b>
        <ul class="link-list">
            <li><a href='{url_yt}' target='_blank'>▶️ Buscar videoclases explicativas sobre: <b>{tema}</b></a></li>
            <li><a href='{url_yt_general}' target='_blank'>▶️ Ver lista de reproducción recomendada para <b>{nombre_cat}</b></a></li>
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
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="header-title" style="text-align: center;">🏛️ Plataforma CNSC 2026</div>', unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748B;'>Sistema Experto de Preparación Docente con Inteligencia Artificial</p>", unsafe_allow_html=True)
        
        usuario_input = st.text_input("👤 Usuario (ID Autorizado):").strip().upper()
        clave_input = st.text_input("🔑 Contraseña:", type="password")
        
        if st.button("🚀 Ingresar al Sistema", type="primary", use_container_width=True):
            if usuario_input in USUARIOS_PERMITIDOS and clave_input == CLAVE_SECRETA:
                st.session_state.usuario_actual = usuario_input
                st.rerun()
            else:
                st.error("⚠️ Usuario o contraseña incorrectos.")
    st.stop()

client = genai.Client(api_key=API_KEY)
usuario = st.session_state.usuario_actual

for key in ["examen_activo", "tema_activo", "contenido_tema", "lista_ejemplos_extra", "links_activos", "preguntas_mini", "resultado_mini"]:
    if key not in st.session_state:
        st.session_state[key] = None

if "lista_ejemplos_extra" not in st.session_state: st.session_state.lista_ejemplos_extra = []
if "respuestas_mini" not in st.session_state: st.session_state.respuestas_mini = {}

# --- MENÚ LATERAL ---
with st.sidebar:
    st.markdown(f"### 👨‍🏫 Docente: **{usuario}**")
    if st.button("🚪 Cerrar Sesión", type="secondary"):
        st.session_state.usuario_actual = None
        st.rerun()
    st.divider()
    modo = st.radio("Navegación Principal:", [
        "🗺️ Temario Detallado (Tema a Tema)", 
        "📝 Simulacro Oficial (20 Preguntas)", 
        "📅 Historial y Progreso"
    ])

# --- PROMPTS MAESTROS ---
PROMPT_TEORIA_ESPECIFICA = """
Actúa como un preparador experto de alto nivel para el Concurso Docente de Colombia.
Desarrolla una clase magistral EXCLUSIVAMENTE sobre este tema específico: '{tema}'.

REGLAS ESTRICTAS:
1. TEORÍA CLARA Y DIRECTA: Explica la lógica detallada del concepto.
2. VARIEDAD DE EJEMPLOS (MÍNIMO 3): Presenta al menos 3 problemas diferentes con dificultad progresiva.
3. PASO A PASO DETALLADO: Muestra el procedimiento línea por línea.
4. FORMATO: Texto plano impecable, sin usar código LaTeX que rompa la interfaz.
"""

def obtener_instruccion_json(tema_exacto):
    return f"""
    Eres un evaluador riguroso de la CNSC. Genera EXACTAMENTE 10 preguntas complejas de opción múltiple exclusivas del tema: {tema_exacto}.
    Devuelve ÚNICAMENTE un arreglo JSON válido, sin bloques de código Markdown alrededor.
    Formato estricto:
    [
      {{
        "id": 1,
        "contexto": "Situación...",
        "enunciado": "Pregunta...",
        "opciones": {{"A": "...", "B": "...", "C": "..."}},
        "correcta": "A",
        "justificacion": "Explicación lógica paso a paso...",
        "cita_legal": "Regla matemática o marco legal"
      }}
    ]
    """

def generar_teoria_y_ejemplos(tema_exacto):
    st.session_state.preguntas_mini = None
    st.session_state.resultado_mini = None
    st.session_state.respuestas_mini = {}
    st.session_state.lista_ejemplos_extra = []
    
    with st.spinner(f"Redactando clase magistral y materiales para: {tema_exacto}..."):
        resp_texto = client.models.generate_content(
            model="gemini-3.5-flash", 
            contents=PROMPT_TEORIA_ESPECIFICA.format(tema=tema_exacto)
        )
    
    enlaces, nom_cat = obtener_enlaces_por_area(tema_exacto)
    st.session_state.tema_activo = tema_exacto
    st.session_state.contenido_tema = resp_texto.text
    st.session_state.links_activos = renderizar_caja_documentos(enlaces, nom_cat, tema_exacto)
    
    fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    datos_globales[usuario]["diario_estudio"][f"{fecha_hoy} - {tema_exacto}"] = resp_texto.text
    guardar_datos(datos_globales)

def generar_mini_simulacro_json(tema_exacto):
    with st.spinner(f"Construyendo banco de 10 preguntas interactivas tipo CNSC para: {tema_exacto}..."):
        try:
            resp_json = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=f"Genera 10 preguntas JSON puras sobre: {tema_exacto}",
                config=types.GenerateContentConfig(
                    system_instruction=obtener_instruccion_json(tema_exacto),
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )
            texto_bruto = resp_json.text
            inicio_json = texto_bruto.find('[')
            fin_json = texto_bruto.rfind(']') + 1
            if inicio_json != -1 and fin_json != 0:
                texto_limpio = texto_bruto[inicio_json:fin_json]
            else:
                texto_limpio = texto_bruto.replace("```json", "").replace("```", "").strip()
                
            st.session_state.preguntas_mini = json.loads(texto_limpio)
            return True
        except Exception as e:
            st.error(f"Error al procesar el minisimulacro. Intenta nuevamente.")
            return False

# --- MÓDULO 1: TEMARIO DETALLADO ---
if modo == "🗺️ Temario Detallado (Tema a Tema)":
    st.markdown('<div class="header-title">🗺️ Módulo de Estudio Detallado</div>', unsafe_allow_html=True)
    
    TEMARIO_DESGLOSADO = {
        "📐 1. Aptitud Numérica": [
            "Porcentajes", "Regla de 3 Simple (Directa e Inversa)", "Regla de 3 Compuesta", 
            "Relaciones y Proporciones", "Sucesiones", "Ecuaciones de primer grado", "Análisis de gráficas", "Pensamiento abstracto"
        ],
        "🗣️ 2. Aptitud Verbal": [
            "Sinónimos y Antónimos", "Analogías", "Comprensión lectora", 
            "Ordenamiento de palabras", "Orden lógico de oraciones"
        ],
        "⚖️ 3. Marco Legal y Competencias Básicas": [
            "Ley 115 (Ley General de Educación)", "Ley 1098 (Infancia y Adolescencia)", 
            "Ley 1620 (Convivencia Escolar y RAI)", "Guía 31 (Evaluación de desempeño)", 
            "Guía 34 (Mejoramiento institucional)", "Decreto 1421 (Educación inclusiva)"
        ],
        "🧠 4. Casos Aplicados y Documentos Adicionales": [
            "Casos aplicados de Convivencia Escolar", "Manual de funciones docente", 
            "Preguntas tipo ICFES (Análisis y aplicación)"
        ]
    }
    
    col_menu, col_contenido = st.columns([1, 2.8])
    
    with col_menu:
        st.markdown("### 📚 Selecciona Tema")
        for categoria, subtemas in TEMARIO_DESGLOSADO.items():
            with st.expander(categoria, expanded=False):
                for subtema in subtemas:
                    if st.button(f"📘 {subtema}", key=f"btn_{subtema}"):
                        generar_teoria_y_ejemplos(subtema)
                        st.rerun()

    with col_contenido:
        if st.session_state.contenido_tema:
            st.markdown(f"## Módulo Académico: {st.session_state.tema_activo}")
            st.markdown(st.session_state.links_activos, unsafe_allow_html=True)
            st.markdown(st.session_state.contenido_tema)
            
            st.divider()
            
            # --- SECCIÓN DE EJEMPLOS ADICIONALES ILIMITADOS ---
            st.markdown("### ➕ Banco de Ejemplos Adicionales")
            if st.button("➕ Cargar más ejemplos de práctica", type="secondary"):
                with st.spinner("Generando nuevos ejercicios resueltos..."):
                    prompt_ej = f"Genera 3 NUEVOS problemas avanzados sobre '{st.session_state.tema_activo}' con su procedimiento paso a paso detallado."
                    resp_ej = client.models.generate_content(model="gemini-3.5-flash", contents=prompt_ej)
                    st.session_state.lista_ejemplos_extra.append(resp_ej.text)
                st.rerun()
            
            # Mostrar todos los bloques de ejemplos solicitados acumulativamente
            for idx, ej_bloque in enumerate(st.session_state.lista_ejemplos_extra):
                with st.container():
                    st.markdown(f"**Ejercicios Adicionales - Bloque {idx + 1}**")
                    st.markdown(ej_bloque)
                    st.write("---")
            
            # --- SECCIÓN DEL MINISIMULACRO ---
            st.divider()
            st.markdown(f"### 📝 MINISIMULACRO INTERACTIVO: {st.session_state.tema_activo}")
            
            if not st.session_state.preguntas_mini:
                st.info("¿Comprendiste la teoría? Pon a prueba tus conocimientos con este minisimulacro de 10 preguntas evaluativas.")
                if st.button(f"🎯 Iniciar Minisimulacro de {st.session_state.tema_activo}", type="primary"):
                    if generar_mini_simulacro_json(st.session_state.tema_activo):
                        st.rerun()
            
            elif st.session_state.preguntas_mini and not st.session_state.resultado_mini:
                with st.form("mini_form"):
                    for p in st.session_state.preguntas_mini:
                        st.markdown(f"**Pregunta {p['id']}. {p['enunciado']}**")
                        if p.get('contexto') and p['contexto'] != "...":
                            st.caption(f"Contexto: {p['contexto']}")
                        st.session_state.respuestas_mini[p['id']] = st.radio(
                            "Selecciona una opción:", options=list(p["opciones"].keys()),
                            format_func=lambda x: f"{x}) {p['opciones'][x]}", key=f"mq_{p['id']}", index=None
                        )
                        st.write("---")
                    
                    if st.form_submit_button("📥 Calificar Mis Respuestas", type="primary"):
                        puntaje = 0
                        revision = []
                        for p in st.session_state.preguntas_mini:
                            resp = st.session_state.respuestas_mini.get(p['id'])
                            es_correcta = (resp == p['correcta'])
                            if es_correcta: puntaje += 1
                            revision.append({
                                "Pregunta": p['enunciado'], "Tu Respuesta": resp or "Sin responder", 
                                "Correcta": p['correcta'], "Justificación": p['justificacion'], 
                                "Base": p.get('cita_legal', 'N/A'), "Acierto": es_correcta
                            })
                        st.session_state.resultado_mini = {"puntaje": puntaje, "total": len(st.session_state.preguntas_mini), "revision": revision}
                        st.rerun()

            elif st.session_state.resultado_mini:
                res = st.session_state.resultado_mini
                st.markdown(f"<div class='resultado-box'><h2>📊 Calificación del Minisimulacro: {res['puntaje']} / {res['total']}</h2></div>", unsafe_allow_html=True)
                for i, r in enumerate(res['revision']):
                    icono = "✅" if r['Acierto'] else "❌"
                    color_txt = "green" if r['Acierto'] else "red"
                    with st.expander(f"{icono} Pregunta {i+1} | Tu opción: {r['Tu Respuesta']} | Correcta: {r['Correcta']}"):
                        st.markdown(f"<span style='color:{color_txt}; font-weight:bold;'>{'Respuesta Correcta' if r['Acierto'] else 'Respuesta Incorrecta'}</span>", unsafe_allow_html=True)
                        st.write(f"**Justificación:** {r['Justificación']}")
                        st.info(f"**Fundamento:** {r['Base']}")
                
                if st.button("🔄 Repetir Minisimulacro"):
                    st.session_state.preguntas_mini = None
                    st.session_state.resultado_mini = None
                    st.session_state.respuestas_mini = {}
                    st.rerun()
        else:
            st.info("👈 Selecciona un tema en el menú de la izquierda para desplegar el contenido académico, enlaces de Drive y videos de YouTube.")

# --- MÓDULO 2: SIMULACRO OFICIAL ---
elif modo == "📝 Simulacro Oficial (20 Preguntas)":
    st.markdown('<div class="header-title">📝 Simulacro Oficial Tipo Concurso Docente</div>', unsafe_allow_html=True)
    area_sim = st.selectbox("Selecciona el área a evaluar:", ["Aptitud Numérica", "Aptitud Verbal", "Competencias Pedagógicas y Legislación"])
    
    if st.button("🚀 Generar Evaluación de 20 Preguntas", type="primary"):
        st.session_state.examen_activo = None
        if "resultado_ultimo_examen" in st.session_state: del st.session_state.resultado_ultimo_examen
        
        with st.spinner(f"Construyendo simulacro oficial de {area_sim}..."):
            sys_inst = f"Eres evaluador experto de la CNSC. Genera 20 preguntas exclusivas y exigentes de '{area_sim}'. Devuelve SOLO JSON puro: [ {{\"id\": 1, \"contexto\": \"...\", \"enunciado\": \"...\", \"opciones\": {{\"A\": \".\", \"B\": \".\", \"C\": \".\"}}, \"correcta\": \"A\", \"justificacion\": \"...\", \"cita_legal\": \"...\"}} ]"
            try:
                response = client.models.generate_content(
                    model="gemini-3.5-flash", contents="Genera 20 preguntas JSON puras",
                    config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json", temperature=0.8)
                )
                texto_bruto = response.text
                inicio_json = texto_bruto.find('[')
                fin_json = texto_bruto.rfind(']') + 1
                if inicio_json != -1 and fin_json != 0:
                    texto_limpio = texto_bruto[inicio_json:fin_json]
                else:
                    texto_limpio = texto_bruto.replace("```json", "").replace("```", "").strip()
                
                st.session_state.examen_activo = json.loads(texto_limpio)
                st.session_state.respuestas_usuario = {}
            except Exception as e:
                st.error(f"Error al procesar el examen oficial. Intenta de nuevo.")

    if st.session_state.examen_activo:
        preguntas = st.session_state.examen_activo
        with st.form("form_ex"):
            for p in preguntas:
                st.markdown(f"<div class='pregunta-card'><b>Pregunta {p.get('id', '*')}</b><br><br><i>{p['contexto']}</i><br><br><b>{p['enunciado']}</b></div>", unsafe_allow_html=True)
                st.session_state.respuestas_usuario[p['id']] = st.radio("Selecciona opción:", options=list(p["opciones"].keys()), format_func=lambda x: f"{x}) {p['opciones'][x]}", key=f"q_{p['id']}", index=None)
            
            if st.form_submit_button("📥 Enviar y Calificar Simulacro Oficial", type="primary"):
                puntaje, revision = 0, []
                for p in preguntas:
                    resp = st.session_state.respuestas_usuario.get(p['id'])
                    es_correcta = (resp == p['correcta'])
                    if es_correcta: puntaje += 1
                    revision.append({
                        "Pregunta": p['enunciado'], "Tu Respuesta": resp or "N/A", 
                        "Correcta": p['correcta'], "Justificación": p['justificacion'], 
                        "Base": p.get('cita_legal', 'N/A'), "Acierto": es_correcta
                    })
                
                efectividad = round((puntaje/len(preguntas))*100, 1)
                datos_globales[usuario]["historial_examenes"].append({
                    "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 
                    "Área": area_sim, "Puntaje": puntaje, "Total": len(preguntas), "Efectividad": efectividad
                })
                guardar_datos(datos_globales)
                st.session_state.resultado_ultimo_examen = {"puntaje": puntaje, "total": len(preguntas), "revision": revision}
                st.rerun()

    if "resultado_ultimo_examen" in st.session_state:
        res = st.session_state.resultado_ultimo_examen
        st.success(f"📊 Calificación Final: {res['puntaje']} / {res['total']} ({(res['puntaje']/res['total'])*100:.1f}%)")
        for i, r in enumerate(res['revision']):
            icono = "✅" if r['Acierto'] else "❌"
            color_txt = "green" if r['Acierto'] else "red"
            with st.expander(f"{icono} Pregunta {i+1} | Tu opción: {r['Tu Respuesta']} | Correcta: {r['Correcta']}"):
                st.markdown(f"<span style='color:{color_txt}; font-weight:bold;'>{'Respuesta Correcta' if r['Acierto'] else 'Respuesta Incorrecta'}</span>", unsafe_allow_html=True)
                st.write(f"**Justificación:** {r['Justificación']}")
                st.info(f"**Norma o Fundamento:** {r['Base']}")

# --- MÓDULO 4: HISTORIAL ---
elif modo == "📅 Historial y Progreso":
    st.markdown('<div class="header-title">📅 Historial de Progreso y Diario de Estudio</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📈 Rendimiento en Simulacros", "📚 Diario de Estudio Registrado"])
    
    with tab1:
        examenes = datos_globales[usuario].get("historial_examenes", [])
        if examenes:
            df = pd.DataFrame(examenes)
            col1, col2 = st.columns(2)
            with col1: st.metric("Simulacros Presentados", len(df))
            with col2: st.metric("Efectividad Promedio", f"{df['Efectividad'].mean():.1f}%")
            st.line_chart(df, y="Efectividad", x="Fecha", use_container_width=True)
            st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("No registra simulacros oficiales completados todavía.")
            
    with tab2:
        diario = datos_globales[usuario].get("diario_estudio", {})
        if diario:
            sesion = st.selectbox("Selecciona la sesión guardada:", list(diario.keys())[::-1])
            if sesion:
                enlaces, nom_cat = obtener_enlaces_por_area(sesion)
                st.markdown(renderizar_caja_documentos(enlaces, nom_cat, sesion.split(" - ")[-1]), unsafe_allow_html=True)
                st.markdown(diario[sesion])
        else:
            st.info("No hay sesiones registradas en el diario de estudio.")
