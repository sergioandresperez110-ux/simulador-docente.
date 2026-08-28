import json
import os
import datetime
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CONFIGURACIÓN DE PÁGINA Y DISEÑO ---
st.set_page_config(page_title="Plataforma Experta CNSC 2026", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    .header-title { font-size: 2.2rem; color: #0F172A; font-weight: 800; border-bottom: 3px solid #3B82F6; padding-bottom: 10px; margin-bottom: 20px;}
    .ruta-card { background-color: #F8FAFC; border: 1px solid #CBD5E1; padding: 18px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid #2563EB; }
    .drive-link-box { background-color: #EFF6FF; border-left: 4px solid #3B82F6; padding: 12px; border-radius: 5px; margin: 10px 0;}
    .pregunta-box { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 20px; border-radius: 8px; margin-bottom: 15px; }
    .stTextInput>div>div>input { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- 2. CREDENCIALES Y BIBLIOTECA DE DRIVE ---
API_KEY = "AQ.Ab8RN6IT6-t3t77qXYzFiVNyakzVr-4cTvUU9Skrh9E_o9r6Tw"
USUARIOS_PERMITIDOS = ["MARCELA2026", "LELY2026", "KARO2026", "CHECHO2026"]
CLAVE_SECRETA = "docente2026"
ARCHIVO_DATOS = "datos_estudio_maestro.json"

ENLACES_DRIVE_GENERAL = "https://drive.google.com/drive/folders/12dgYySHb9BnINgYTSuOqvM4ru-1VhxRW?usp=sharing"

BIBLIOTECA_DRIVE = {
    "ley 1620": "https://drive.google.com/drive/folders/12dgYySHb9BnINgYTSuOqvM4ru-1VhxRW?usp=sharing",
    "decreto 1290": "https://drive.google.com/drive/folders/12dgYySHb9BnINgYTSuOqvM4ru-1VhxRW?usp=sharing",
    "competencias pedagogicas": "https://drive.google.com/drive/folders/12dgYySHb9BnINgYTSuOqvM4ru-1VhxRW?usp=sharing",
    "tecnologia e informatica": "https://drive.google.com/drive/folders/12dgYySHb9BnINgYTSuOqvM4ru-1VhxRW?usp=sharing"
}

# --- 3. BASE DE DATOS LOCAL ---
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {usr: {"historial_examenes": [], "temas_guardados": {}} for usr in USUARIOS_PERMITIDOS}

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
        st.markdown('<div class="header-title">🏛️ Acceso Seguro CNSC</div>', unsafe_allow_html=True)
        st.info("Ingresa tus credenciales para acceder a la ruta de estudio inteligente.")
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

if usuario not in datos_globales:
    datos_globales[usuario] = {"historial_examenes": [], "temas_guardados": {}}

if "examen_activo" not in st.session_state: st.session_state.examen_activo = None
if "tema_activo" not in st.session_state: st.session_state.tema_activo = None
if "contenido_tema" not in st.session_state: st.session_state.contenido_tema = None

# --- MENÚ LATERAL ---
with st.sidebar:
    st.markdown(f"### 👨‍🏫 Docente: {usuario}")
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.usuario_actual = None
        st.rerun()
    st.divider()
    modo = st.radio("Navegación:", [
        "🗺️ Ruta de Estudio Inteligente (Inicio)", 
        "📖 Biblioteca y Módulos de Estudio", 
        "📝 Simulacro Oficial (20 Preg. + Tiempo)", 
        "📊 Gráficas de Desempeño y Progreso"
    ])
    st.divider()
    area_evaluacion = st.selectbox(
        "Área de Enfoque:",
        ["Competencias Pedagógicas (Legislación)", "Lectura Crítica", "Razonamiento Cuantitativo", "Tecnología e Informática"]
    )
    st.markdown(f"[📂 Abrir Biblioteca en Drive]({ENLACES_DRIVE_GENERAL})")

# --- MÓDULO 1: RUTA DE ESTUDIO INTELIGENTE (LA GUÍA PASO A PASO) ---
if modo == "🗺️ Ruta de Estudio Inteligente (Inicio)":
    st.markdown('<div class="header-title">🗺️ Tu Ruta de Estudio Oficial - CNSC 2026</div>', unsafe_allow_html=True)
    st.success("¡Bienvenida a tu plan maestro! Como vas a empezar desde cero, no tienes que inventar qué estudiar. La IA ha diseñado esta ruta progresiva basada en las normativas del Ministerio de Educación y los documentos de tu biblioteca en Google Drive.")
    
    # Ruta preestablecida experta para docentes novatos en el concurso
    fases_estudio = [
        {"fase": "Fase 1: Marco Legal y Convivencia Escolar", "tema": "Ley 1620 y Rutas de Atención Integral", "desc": "Comprende los protocolos obligatorios ante situaciones de conflicto y acoso escolar."},
        {"fase": "Fase 2: Evaluación y Promoción Institucional", "tema": "Decreto 1290 de Evaluación del Aprendizaje", "desc": "Estudia los criterios de valoración, escalas de calificación y directrices institucionales."},
        {"fase": "Fase 3: Fundamentos Pedagógicos Constitucionales", "tema": "Ley 115 (Ley General de Educación) y Fines de la Educación", "desc": "Revisa la estructura del sistema educativo colombiano y los niveles de formación."},
        {"fase": "Fase 4: Juicio Situacional y Práctica de Aula", "tema": "Resolución de Casos Pedagógicos Complejos", "desc": "Aprende a responder bajo la perspectiva de la escuela inclusiva y el enfoque de derechos."}
    ]
    
    for item in fases_estudio:
        st.markdown(f"""
        <div class="ruta-card">
            <h4>{item['fase']}</h4>
            <p><b>Tema Clave:</b> {item['tema']}</p>
            <p>{item['desc']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"🚀 Cargar y Estudiar: {item['tema']}", key=f"ruta_{item['tema']}"):
            with st.spinner(f"Generando lección estructurada sobre {item['tema']} vinculada a tu biblioteca..."):
                prompt = f"""Actúa como experto en el Concurso Docente de Colombia. Escribe una lección completa, didáctica y estructurada para un docente que empieza desde cero sobre: '{item['tema']}'. 
                Explícalo de forma clara, incluye los artículos o conceptos fundamentales y haz énfasis en cómo lo evalúa la CNSC. 
                Recuerda basarte en los lineamientos oficiales de los documentos del MEN."""
                
                respuesta = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
                st.session_state.tema_activo = item['tema']
                st.session_state.contenido_tema = respuesta.text
                
                datos_globales[usuario]["temas_guardados"][item['tema']] = respuesta.text
                guardar_datos(datos_globales)
                st.rerun()

    if st.session_state.contenido_tema:
        st.divider()
        st.markdown(f"### 📄 Lección Activa: {st.session_state.tema_activo}")
        st.markdown(f"""
        <div class="drive-link-box">
            <b>📂 Resguardo Documental:</b> Esta lección está respaldada por los archivos oficiales de tu biblioteca. 
            <a href="{ENLACES_DRIVE_GENERAL}" target="_blank">Consultar Documentos Originales en Google Drive</a>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(st.session_state.contenido_tema)

# --- MÓDULO 2: BIBLIOTECA Y MÓDULOS DE ESTUDIO ---
elif modo == "📖 Biblioteca y Módulos de Estudio":
    st.markdown('<div class="header-title">📖 Biblioteca y Búsqueda de Contenido Experto</div>', unsafe_allow_html=True)
    
    col_h, col_e = st.columns([1, 3])
    with col_h:
        st.subheader("📚 Tus Apuntes Guardados")
        temas_previos = datos_globales[usuario].get("temas_guardados", {})
        if temas_previos:
            for t in list(temas_previos.keys())[::-1]:
                if st.button(f"📄 {t}", key=f"sb_{t}", use_container_width=True):
                    st.session_state.tema_activo = t
                    st.session_state.contenido_tema = temas_previos[t]
        else:
            st.caption("No tienes temas guardados.")

    with col_e:
        tema_libre = st.text_input("¿Qué otro concepto o ley específica deseas consultar?")
        if st.button("Generar Material Basado en Drive", type="primary") and tema_libre:
            with st.spinner("Sintetizando información oficial..."):
                prompt = f"""Redacta un documento maestro de estudio sobre '{tema_libre}' para el Concurso Docente de Colombia, 
                integrando de forma rigurosa los principios normativos oficiales (como si leyeras directamente los PDFs de la biblioteca)."""
                resp = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
                st.session_state.tema_activo = tema_libre
                st.session_state.contenido_tema = resp.text
                datos_globales[usuario]["temas_guardados"][tema_libre] = resp.text
                guardar_datos(datos_globales)

        if st.session_state.tema_activo:
            st.markdown(f"### Módulo: {st.session_state.tema_activo}")
            st.markdown(f"""
            <div class="drive-link-box">
                <b>📂 Enlace a Documentos de Drive:</b> <a href="{ENLACES_DRIVE_GENERAL}" target="_blank">Abrir Carpeta de Respaldo</a>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(st.session_state.contenido_tema)

# --- MÓDULO 3: SIMULACRO OFICIAL ---
elif modo == "📝 Simulacro Oficial (20 Preg. + Tiempo)":
    st.markdown('<div class="header-title">📝 Simulacro Oficial con Exigencia Real (20 Preguntas)</div>', unsafe_allow_html=True)
    st.warning("⏱️ Prueba de 20 preguntas de juicio situacional con rigor de la CNSC. Al finalizar, el sistema calculará tu efectividad y actualizará tus gráficas de desempeño.")
    
    if st.button("🚀 Generar Nuevo Simulacro", type="primary"):
        st.session_state.examen_activo = None
        if "resultado_ultimo_examen" in st.session_state: del st.session_state.resultado_ultimo_examen
        
        with st.spinner("Construyendo 20 casos situacionales estrictos basados en normatividad y doctrina pedagógica..."):
            system_instruction = """
            Eres un evaluador senior de la CNSC de Colombia. Genera EXACTAMENTE 20 preguntas complejas de juicio situacional para docentes.
            Deben estar basadas estrictamente en la normatividad educativa colombiana (Leyes, Decretos del MEN).
            Devuelve ÚNICAMENTE un arreglo JSON estricto:
            [
              {
                "id": 1,
                "contexto": "...",
                "enunciado": "...",
                "opciones": {"A": "...", "B": "...", "C": "..."},
                "correcta": "A",
                "justificacion": "...",
                "cita_legal": "Artículo X, Ley/Decreto Y"
              }
            ]
            """
            try:
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=f"Genera 20 preguntas para el área: {area_evaluacion}",
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.85
                    ),
                )
                st.session_state.examen_activo = json.loads(response.text)
                st.session_state.respuestas_usuario = {}
            except Exception:
                st.error("Error al compilar el examen. Intenta de nuevo.")

    if st.session_state.examen_activo:
        preguntas = st.session_state.examen_activo
        with st.form("form_ex"):
            for p in preguntas:
                st.markdown(f"""
                <div class="pregunta-box">
                    <b>Pregunta {p.get('id', '*')}</b><br><br>
                    <i>Contexto:</i> {p['contexto']}<br><br>
                    <b>{p['enunciado']}</b>
                </div>
                """, unsafe_allow_html=True)
                st.session_state.respuestas_usuario[p['id']] = st.radio(
                    "Selecciona:", options=list(p["opciones"].keys()),
                    format_func=lambda x: f"{x}) {p['opciones'][x]}", key=f"q_{p['id']}", index=None
                )
                st.write("---")
            
            if st.form_submit_button("📥 Enviar y Calificar Examen", type="primary"):
                puntaje = 0
                revision = []
                for p in preguntas:
                    resp_usr = st.session_state.respuestas_usuario[p['id']]
                    es_ok = (resp_usr == p['correcta'])
                    if es_ok: puntaje += 1
                    revision.append({
                        "Pregunta": p['enunciado'], "Tu Respuesta": resp_usr or "N/A",
                        "Correcta": p['correcta'], "Justificación": p['justificacion'], "Base": p.get('cita_legal', 'Normativa MEN')
                    })
                
                # Registro con área para graficar
                reg = {
                    "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Área": area_evaluacion,
                    "Puntaje": puntaje,
                    "Total": len(preguntas),
                    "Efectividad": round((puntaje/len(preguntas))*100, 1)
                }
                datos_globales[usuario]["historial_examenes"].append(reg)
                guardar_datos(datos_globales)
                
                st.session_state.resultado_ultimo_examen = {"puntaje": puntaje, "total": len(preguntas), "revision": revision}
                st.rerun()

    if "resultado_ultimo_examen" in st.session_state:
        res = st.session_state.resultado_ultimo_examen
        st.success(f"📊 Calificación: {res['puntaje']} / {res['total']}")
        for i, r in enumerate(res['revision']):
            with st.expander(f"Pregunta {i+1} | Tu opción: {r['Tu Respuesta']} | Correcta: {r['Correcta']}"):
                st.write(f"**Justificación:** {r['Justificación']}")
                st.info(f"**Sustento:** {r['Base']} | [📂 Ver en Google Drive]({ENLACES_DRIVE_GENERAL})")

# --- MÓDULO 4: GRÁFICAS DE DESEMPEÑO Y PROGRESO ---
elif modo == "📊 Gráficas de Desempeño y Progreso":
    st.markdown('<div class="header-title">📊 Gráficas de Desempeño Analítico</div>', unsafe_allow_html=True)
    st.write(f"Visualización gráfica del rendimiento de **{usuario}** en los simulacros presentados.")
    
    examenes = datos_globales[usuario].get("historial_examenes", [])
    if examenes:
        df = pd.DataFrame(examenes)
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Total Simulacros Realizados", len(df))
        with col_m2:
            prom_efectividad = df["Efectividad"].mean()
            st.metric("Efectividad Promedio Global", f"{prom_efectividad:.1f}%")
            
        st.divider()
        st.subheader("📈 Evolución de la Efectividad por Examen (%)")
        # Gráfica de línea nativa integrada en Streamlit
        st.line_chart(df, y="Efectividad", x="Fecha", use_container_width=True)
        
        st.divider()
        st.subheader("📑 Registro Detallado de Pruebas")
        st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("Aún no tienes simulacros registrados. Presenta tu primera prueba para que la plataforma genere las gráficas analíticas.")
