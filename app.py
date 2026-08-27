import json
import os
import datetime
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CONFIGURACIÓN DE PÁGINA Y UI PROFESIONAL ---
st.set_page_config(page_title="Simulador Avanzado CNSC 2026", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    .header-title { font-size: 2.2rem; color: #0F172A; font-weight: 800; border-bottom: 3px solid #3B82F6; padding-bottom: 10px; margin-bottom: 20px;}
    .norma-link { background-color: #EFF6FF; border-left: 4px solid #3B82F6; padding: 15px; border-radius: 5px; margin: 15px 0;}
    .pregunta-box { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 20px; border-radius: 8px; margin-bottom: 15px; }
    .stTextInput>div>div>input { border-radius: 8px; }
    .btn-historial { margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 2. CREDENCIALES, USUARIOS Y ENLACES OFICIALES ---
API_KEY = "AQ.Ab8RN6IT6-t3t77qXYzFiVNyakzVr-4cTvUU9Skrh9E_o9r6Tw"
USUARIOS_PERMITIDOS = ["MARCELA2026", "LELY2026", "KARO2026", "CHECHO2026"]
CLAVE_SECRETA = "docente2026"
ARCHIVO_DATOS = "datos_estudio_avanzado.json"

ENLACES_MINISTERIO = {
    "ley 1620": "https://www.mineducacion.gov.co/1759/w3-article-322486.html",
    "decreto 1290": "https://www.mineducacion.gov.co/1621/articles-187765_archivo_pdf_decreto_1290.pdf",
    "ley 115": "https://www.mineducacion.gov.co/1621/articles-85906_archivo_pdf.pdf",
    "decreto 1075": "https://www.mineducacion.gov.co/1759/w3-article-351080.html"
}

# --- 3. GESTIÓN DE BASE DE DATOS LOCAL ---
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {usr: {"historial_examenes": [], "temas_guardados": {}} for usr in USUARIOS_PERMITIDOS}

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

datos_globales = cargar_datos()

# --- 4. LOGIN SEGURO (CAJA DE TEXTO VACÍA) ---
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None

if st.session_state.usuario_actual is None:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="header-title">🏛️ Acceso CNSC 2026</div>', unsafe_allow_html=True)
        st.info("Ingresa tus credenciales para acceder al simulador avanzado.")
        
        usuario_input = st.text_input("Usuario (ID):").strip().upper()
        clave_input = st.text_input("Contraseña:", type="password")
        
        if st.button("Iniciar Sesión", type="primary", use_container_width=True):
            if usuario_input in USUARIOS_PERMITIDOS and clave_input == CLAVE_SECRETA:
                st.session_state.usuario_actual = usuario_input
                st.rerun()
            else:
                st.error("Acceso denegado. Verifica tu usuario y contraseña.")
    st.stop()

# --- 5. INICIALIZACIÓN DE LA APLICACIÓN ---
client = genai.Client(api_key=API_KEY)
usuario = st.session_state.usuario_actual

if usuario not in datos_globales:
    datos_globales[usuario] = {"historial_examenes": [], "temas_guardados": {}}

# Variables de estado para navegación fluida
if "examen_activo" not in st.session_state: st.session_state.examen_activo = None
if "tema_activo" not in st.session_state: st.session_state.tema_activo = None
if "contenido_tema" not in st.session_state: st.session_state.contenido_tema = None

with st.sidebar:
    st.markdown(f"### 👨‍🏫 Panel de {usuario}")
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.usuario_actual = None
        st.rerun()
    st.divider()
    modo = st.radio("Navegación:", ["📖 Centro de Estudio", "📝 Simulacro Oficial (20 Preg.)", "📊 Mi Rendimiento"])
    st.divider()
    area_evaluacion = st.selectbox(
        "Área de Enfoque:",
        ["Competencias Pedagógicas (Legislación)", "Lectura Crítica", "Razonamiento Cuantitativo", "Tecnología e Informática"]
    )

# --- MÓDULO 1: CENTRO DE ESTUDIO AVANZADO ---
if modo == "📖 Centro de Estudio":
    st.markdown('<div class="header-title">📖 Centro de Estudio y Legislación</div>', unsafe_allow_html=True)
    
    col_historial, col_estudio = st.columns([1, 3])
    
    with col_historial:
        st.subheader("📚 Tus Apuntes")
        temas_previos = datos_globales[usuario].get("temas_guardados", {})
        if temas_previos:
            for t in list(temas_previos.keys())[::-1]: # Mostrar los más recientes primero
                if st.button(f"📄 {t}", key=f"btn_{t}", use_container_width=True):
                    st.session_state.tema_activo = t
                    st.session_state.contenido_tema = temas_previos[t]
        else:
            st.caption("No tienes temas guardados aún.")

    with col_estudio:
        tema_nuevo = st.text_input("Buscar un nuevo tema, ley o teoría pedagógica:")
        if st.button("Generar Material Experto", type="primary"):
            with st.spinner("Analizando y estructurando contenido normativo..."):
                prompt = f"""Escribe un documento de estudio avanzado sobre '{tema_nuevo}' para el Concurso Docente de Colombia.
                Debe ser un nivel universitario/profesional. Incluye:
                1. Conceptos fundamentales.
                2. Artículos clave (si es una norma) o autores (si es pedagogía).
                3. Tips específicos de cómo la CNSC suele evaluar este tema."""
                
                respuesta = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
                
                st.session_state.tema_activo = tema_nuevo
                st.session_state.contenido_tema = respuesta.text
                
                # Guardar en el caché histórico
                datos_globales[usuario]["temas_guardados"][tema_nuevo] = respuesta.text
                guardar_datos(datos_globales)

        if st.session_state.tema_activo:
            # Mostrar Enlaces Oficiales si existen
            tema_minuscula = st.session_state.tema_activo.lower()
            for clave, link in ENLACES_MINISTERIO.items():
                if clave in tema_minuscula:
                    st.markdown(f"""
                    <div class="norma-link">
                        <b>🔗 Recurso Oficial Detectado:</b> Puedes consultar el documento original y actualizado del MEN aquí: 
                        <a href="{link}" target="_blank">{clave.upper()}</a>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown(st.session_state.contenido_tema)
            
            st.divider()
            if st.button(f"🔍 Profundizar y generar ejemplos de aula para '{st.session_state.tema_activo}'"):
                with st.spinner("Diseñando casos prácticos..."):
                    prompt_ejemplos = f"Dame 3 ejemplos prácticos y reales aplicados al aula escolar sobre el tema: {st.session_state.tema_activo}. Explica cómo se resuelve cada caso."
                    ejemplos = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt_ejemplos)
                    st.success("Ejemplos Generados:")
                    st.markdown(ejemplos.text)

# --- MÓDULO 2: SIMULACRO OFICIAL 20 PREGUNTAS ---
elif modo == "📝 Simulacro Oficial (20 Preg.)":
    st.markdown('<div class="header-title">📝 Simulacro de Prueba Escrita CNSC</div>', unsafe_allow_html=True)
    st.warning("⏱️ Esta prueba consta de 20 preguntas de juicio situacional inéditas. La generación puede tardar hasta 40 segundos debido a la complejidad requerida. Por favor, ten paciencia.")
    
    if st.button("Generar Nuevo Simulacro (20 Preguntas)", type="primary"):
        st.session_state.examen_activo = None # Limpiar examen anterior
        with st.spinner("Construyendo 20 casos situacionales con justificaciones normativas... Esto tomará un momento."):
            system_instruction = """
            Eres un experto en redactar pruebas para la Comisión Nacional del Servicio Civil (CNSC) de Colombia.
            Genera EXACTAMENTE 20 preguntas de nivel avanzado basadas en el área solicitada.
            Todas deben ser casos hipotéticos de aula o colegio (Juicio Situacional).
            Devuelve ÚNICAMENTE un arreglo JSON estricto.
            Formato:
            [
              {
                "id": 1,
                "contexto": "Texto del caso...",
                "enunciado": "Pregunta...",
                "opciones": {"A": "...", "B": "...", "C": "..."},
                "correcta": "A",
                "justificacion": "Por qué es correcta...",
                "cita_legal": "Referencia exacta (Ej: Artículo 39, Ley 1620 / Estándares Básicos MEN / Decreto 1290)."
              }
            ]
            """
            try:
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=f"Genera 20 preguntas inéditas para el área: {area_evaluacion}",
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.7 # Mayor temperatura para asegurar variedad entre intentos
                    ),
                )
                st.session_state.examen_activo = json.loads(response.text)
                st.session_state.respuestas_usuario = {}
            except Exception as e:
                st.error("Hubo un error al compilar las 20 preguntas (límite de memoria de la IA). Por favor, haz clic de nuevo para reintentar.")
                
    if st.session_state.examen_activo:
        preguntas = st.session_state.examen_activo
        
        with st.form("formulario_examen"):
            for p in preguntas:
                st.markdown(f"""
                <div class="pregunta-box">
                    <b>Pregunta {p.get('id', '*')}</b><br><br>
                    <i>Contexto:</i> {p['contexto']}<br><br>
                    <b>{p['enunciado']}</b>
                </div>
                """, unsafe_allow_html=True)
                
                st.session_state.respuestas_usuario[p['id']] = st.radio(
                    "Selecciona:", 
                    options=list(p["opciones"].keys()), 
                    format_func=lambda x: f"{x}) {p['opciones'][x]}",
                    key=f"q_{p['id']}",
                    index=None
                )
                st.write("---")
            
            entregado = st.form_submit_button("Finalizar y Calificar Simulacro", type="primary")
            
            if entregado:
                puntaje = 0
                revision_detallada = []
                
                for p in preguntas:
                    resp_usr = st.session_state.respuestas_usuario[p['id']]
                    es_correcta = (resp_usr == p['correcta'])
                    if es_correcta: puntaje += 1
                    
                    revision_detallada.append({
                        "Pregunta": p['enunciado'],
                        "Tu Respuesta": resp_usr if resp_usr else "Sin responder",
                        "Correcta": p['correcta'],
                        "Justificación": p['justificacion'],
                        "Base Legal/Teórica": p.get('cita_legal', 'Soporte pedagógico general')
                    })
                
                # Guardar registro
                registro_examen = {
                    "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Área": area_evaluacion,
                    "Puntaje": f"{puntaje} / {len(preguntas)}",
                    "Efectividad": f"{(puntaje/len(preguntas))*100:.1f}%"
                }
                datos_globales[usuario]["historial_examenes"].append(registro_examen)
                guardar_datos(datos_globales)
                
                st.session_state.resultado_ultimo_examen = {
                    "puntaje": puntaje,
                    "total": len(preguntas),
                    "revision": revision_detallada
                }
                st.rerun()

    # Mostrar resultados si acaba de entregar
    if "resultado_ultimo_examen" in st.session_state:
        res = st.session_state.resultado_ultimo_examen
        st.success(f"📊 Calificación Final: {res['puntaje']} de {res['total']} respuestas correctas.")
        
        st.subheader("Hoja de Respuestas y Fundamentación Normativa")
        for i, rev in enumerate(res['revision']):
            with st.expander(f"Pregunta {i+1} | Tu respuesta: {rev['Tu Respuesta']} | Correcta: {rev['Correcta']}"):
                if rev['Tu Respuesta'] == rev['Correcta']:
                    st.success("✅ Respondiste correctamente.")
                else:
                    st.error("❌ Respuesta incorrecta.")
                st.write(f"**Justificación Técnica:** {rev['Justificación']}")
                st.info(f"**Sustento Legal/Documental:** {rev['Base Legal/Teórica']}")

# --- MÓDULO 3: MI RENDIMIENTO ---
elif modo == "📊 Mi Rendimiento":
    st.markdown('<div class="header-title">📊 Auditoría de Rendimiento</div>', unsafe_allow_html=True)
    st.write(f"Aquí puedes auditar tus simulacros completos, **{usuario}**. Cada registro representa una prueba de 20 preguntas finalizada.")
    
    examenes = datos_globales[usuario].get("historial_examenes", [])
    if examenes:
        df_examenes = pd.DataFrame(examenes)
        st.dataframe(df_examenes.iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("No tienes exámenes completados registrados. Ve a la pestaña 'Simulacro Oficial' para presentar tu primera prueba.")
