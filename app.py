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
    .norma-box { border-left: 5px solid #2563EB; padding: 12px; margin: 15px 0; background-color: rgba(37, 99, 235, 0.08); border-radius: 4px; }
    .pregunta-card { border: 1px solid #E2E8F0; padding: 20px; border-radius: 8px; margin-bottom: 15px; }
    .temario-card { background-color: rgba(255, 255, 255, 0.03); border: 1px solid #334155; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .stTextInput>div>div>input { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- 2. CREDENCIALES Y MAPA OFICIAL DE NORMATIVIDAD Y TEMARIO CNSC ---
API_KEY = "AQ.Ab8RN6IT6-t3t77qXYzFiVNyakzVr-4cTvUU9Skrh9E_o9r6Tw"
USUARIOS_PERMITIDOS = ["MARCELA2026", "LELY2026", "KARO2026", "CHECHO2026"]
CLAVE_SECRETA = "docente2026"
ARCHIVO_DATOS = "datos_estudio_maestro_v3.json"

# Mapeo de enlaces oficiales del MEN basados estrictamente en tu temario
ENLACES_NORMATIVOS = {
    "ley 1620": "https://www.mineducacion.gov.co/1759/w3-article-322486.html",
    "decreto 1290": "https://www.mineducacion.gov.co/1621/articles-187765_archivo_pdf_decreto_1290.pdf",
    "ley 115": "https://www.mineducacion.gov.co/1621/articles-85906_archivo_pdf.pdf",
    "ley 1098": "https://www.mineducacion.gov.co/1621/articles-235787_archivo_pdf_ley_1098.pdf",
    "decreto 1421": "https://www.mineducacion.gov.co/1759/w3-article-366894.html",
    "guia 31": "https://www.mineducacion.gov.co/1621/articles-175563_archivo_pdf.pdf",
    "guia 34": "https://www.mineducacion.gov.co/1759/w3-article-177783.html",
    "general": "https://drive.google.com/drive/folders/12dgYySHb9BnINgYTSuOqvM4ru-1VhxRW?usp=sharing"
}

def obtener_enlace_norma(texto):
    texto_lower = texto.lower()
    for clave, link in ENLACES_NORMATIVOS.items():
        if clave in texto_lower:
            return link, clave.upper()
    return ENLACES_NORMATIVOS["general"], "Biblioteca de Respaldo Drive"

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
        st.info("Ingresa tus credenciales para acceder al simulador y temario oficial.")
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
    datos_globales[usuario] = {"historial_examenes": [], "diario_estudio": {}}

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
        "🗺️ Temario Oficial y Ruta", 
        "📖 Generador por Área de Enfoque", 
        "📝 Simulacro Oficial (20 Preg. + Tiempo)", 
        "📅 Historial y Progreso"
    ])
    st.divider()
    
    # Selector dinámico del área de estudio
    area_evaluacion = st.selectbox(
        "Área de Enfoque Actual:",
        [
            "1. Aptitud Numérica (Razonamiento Cuantitativo)",
            "2. Aptitud Verbal (Lectura Crítica)",
            "3. Competencias Pedagógicas y Legislación (Ley 115, 1098, 1620, Decreto 1290, 1421, Guías 31 y 34)",
            "4. Conocimientos Específicos: Tecnología e Informática"
        ]
    )
    st.markdown(f"[📂 Abrir Carpeta Drive General]({ENLACES_NORMATIVOS['general']})")

# --- MÓDULO 1: TEMARIO OFICIAL Y RUTA ---
if modo == "🗺️ Temario Oficial y Ruta":
    st.markdown('<div class="header-title">🗺️ Temario Oficial del Concurso Docente 2026</div>', unsafe_allow_html=True)
    st.info("Esta es la estructura exacta que debes dominar. Haz clic en cualquier módulo para que la IA te genere la lección experta correspondiente basada en los documentos oficiales del MEN.")
    
    temario_oficial = [
        {"categoria": "1. Aptitud Numérica", "sub": "Porcentajes, Regla de 3 (simple/compuesta), Proporciones, Sucesiones, Ecuaciones de 1er grado, Análisis de gráficas y Pensamiento abstracto."},
        {"categoria": "2. Aptitud Verbal", "sub": "Sinónimos, Antónimos, Analogías, Comprensión lectora, Ordenamiento de palabras y Oraciones lógicas."},
        {"categoria": "3. Marco Normativo Fundamental", "sub": "Ley 115 (General de Educación), Ley 1098 (Infancia y Adolescencia), Ley 1620 (Convivencia Escolar), Decreto 1421 (Educación Inclusiva)."},
        {"categoria": "4. Gestión y Evaluación Institucional", "sub": "Decreto 1290 (Evaluación de Aprendizajes), Guía 31 (Evaluación de Desempeño), Guía 34 (Mejoramiento Institucional) y Manual de Funciones Docente."},
        {"categoria": "5. Juicios de Casos Pedagógicos", "sub": "Situaciones de aula complejas resueltas bajo la normativa vigente y enfoque de derechos."}
    ]
    
    for item in temario_oficial:
        st.markdown(f"""
        <div class="temario-card">
            <h4>{item['categoria']}</h4>
            <p><i>Contenidos evaluados:</i> {item['sub']}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"🚀 Generar Material de Estudio: {item['categoria']}", key=f"gen_{item['categoria']}"):
            with st.spinner(f"Generando módulo experto para {item['categoria']}..."):
                prompt = f"""Actúa como experto evaluador de la CNSC. Redacta una clase magistral y completa de estudio enfocada en: '{item['categoria']} - {item['sub']}'. 
                Proporciona explicaciones teóricas claras, fórmulas o artículos normativos según aplique, y ejemplos tipo prueba escrita."""
                
                resp = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
                st.session_state.tema_activo = item['categoria']
                st.session_state.contenido_tema = resp.text
                
                fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                datos_globales[usuario]["diario_estudio"][f"{fecha_hoy} - {item['categoria']}"] = resp.text
                guardar_datos(datos_globales)
                st.rerun()

    if st.session_state.contenido_tema:
        link_drive, nombre_norma = obtener_enlace_norma(st.session_state.tema_activo)
        st.markdown(f"""
        <div class="norma-box">
            <b>🔍 Constatación Documental:</b> Este tema está respaldado por los documentos del MEN. 
            Consúltalo directamente aquí: <a href="{link_drive}" target="_blank">Abrir {nombre_norma}</a>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(st.session_state.contenido_tema)

# --- MÓDULO 2: GENERADOR POR ÁREA DE ENFOQUE ---
elif modo == "📖 Generador por Área de Enfoque":
    st.markdown(f'<div class="header-title">📖 Módulo Activo: {area_evaluacion}</div>', unsafe_allow_html=True)
    st.info(f"Has seleccionado trabajar sobre el área: **{area_evaluacion}**. Haz clic en el botón inferior para que la IA genere un material de estudio específico ajustado a este componente.")
    
    tema_especifico = st.text_input("Especifica un subtema o deja que la IA elija el punto clave a estudiar:", placeholder="Ej: Protocolo de atención Ley 1620, o Porcentajes avanzados...")
    
    if st.button(f"📚 Generar Lección para '{area_evaluacion}'", type="primary"):
        with st.spinner("Redactando contenido pedagógico especializado..."):
            prompt = f"""Crea un documento de estudio avanzado y riguroso para el Concurso Docente de Colombia enfocado en el área: '{area_evaluacion}'.
            Subtema o enfoque: '{tema_especifico if tema_especifico else "Temas fundamentales de la categoría"}'.
            Incluye conceptos clave, ejemplos resueltos, normatividad asociada y tips para el examen de la CNSC."""
            
            resp = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
            st.session_state.tema_activo = f"{area_evaluacion} - {tema_especifico or 'General'}"
            st.session_state.contenido_tema = resp.text
            
            fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            datos_globales[usuario]["diario_estudio"][f"{fecha_hoy} - {st.session_state.tema_activo}"] = resp.text
            guardar_datos(datos_globales)

    if st.session_state.contenido_tema:
        link_drive, nombre_norma = obtener_enlace_norma(st.session_state.tema_activo)
        st.markdown(f"""
        <div class="norma-box">
            <b>📂 Enlace de Verificación en Drive / MEN:</b> <a href="{link_drive}" target="_blank">Consultar {nombre_norma}</a>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(st.session_state.contenido_tema)

# --- MÓDULO 3: SIMULACRO OFICIAL ---
elif modo == "📝 Simulacro Oficial (20 Preg. + Tiempo)":
    st.markdown(f'<div class="header-title">📝 Simulacro Oficial - {area_evaluacion}</div>', unsafe_allow_html=True)
    st.warning("⏱️ Examen cronometrado de 20 preguntas adaptado estrictamente al área de enfoque seleccionada en la barra lateral.")
    
    if st.button("🚀 Generar Simulacro de 20 Preguntas", type="primary"):
        st.session_state.examen_activo = None
        if "resultado_ultimo_examen" in st.session_state: del st.session_state.resultado_ultimo_examen
        
        with st.spinner(f"Construyendo 20 preguntas tipo ICFES / CNSC para el área: {area_evaluacion}..."):
            system_instruction = f"""
            Eres un evaluador senior de la CNSC de Colombia. Genera EXACTAMENTE 20 preguntas complejas de opción múltiple (juicio situacional o resolución de problemas) adaptadas a la categoría: '{area_evaluacion}'.
            Devuelve ÚNICAMENTE un arreglo JSON estricto:
            [
              {
                "id": 1,
                "contexto": "Caso o enunciado...",
                "enunciado": "Pregunta...",
                "opciones": {"A": "...", "B": "...", "C": "..."},
                "correcta": "A",
                "justificacion": "...",
                "cita_legal": "Norma, Artículo o Teoría de referencia"
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
                        temperature=0.8
                    ),
                )
                st.session_state.examen_activo = json.loads(response.text)
                st.session_state.respuestas_usuario = {}
            except Exception:
                st.error("Error al compilar el simulacro. Vuelve a intentar.")

    if st.session_state.examen_activo:
        preguntas = st.session_state.examen_activo
        with st.form("form_ex"):
            for p in preguntas:
                st.markdown(f"""
                <div class="pregunta-card">
                    <b>Pregunta {p.get('id', '*')}</b><br><br>
                    <i>Contexto/Caso:</i> {p['contexto']}<br><br>
                    <b>{p['enunciado']}</b>
                </div>
                """, unsafe_allow_html=True)
                st.session_state.respuestas_usuario[p['id']] = st.radio(
                    "Selecciona:", options=list(p["opciones"].keys()),
                    format_func=lambda x: f"{x}) {p['opciones'][x]}", key=f"q_{p['id']}", index=None
                )
                st.write("---")
            
            if st.form_submit_button("📥 Enviar y Calificar Simulacro", type="primary"):
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
        st.success(f"📊 Calificación Final: {res['puntaje']} / {res['total']}")
        for i, r in enumerate(res['revision']):
            link_drive, nombre_norma = obtener_enlace_norma(r['Base'])
            with st.expander(f"Pregunta {i+1} | Tu opción: {r['Tu Respuesta']} | Correcta: {r['Correcta']}"):
                st.write(f"**Justificación:** {r['Justificación']}")
                st.info(f"**Sustento:** {r['Base']} | [📂 Verificar en {nombre_norma}]({link_drive})")

# --- MÓDULO 4: HISTORIAL Y PROGRESO ---
elif modo == "📅 Historial y Progreso":
    st.markdown('<div class="header-title">📅 Historial Diario y Estadísticas de Avance</div>', unsafe_allow_html=True)
    st.write(f"Auditoría de estudio para **{usuario}**. Revisa tus sesiones pasadas y evolución en los simulacros.")
    
    tab1, tab2 = st.tabs(["📚 Diario de Estudio (Contenido Exacto)", "📈 Gráficas de Rendimiento"])
    
    with tab1:
        diario = datos_globales[usuario].get("diario_estudio", {})
        if diario:
            sesion = st.selectbox("Selecciona la fecha y sesión estudiada:", list(diario.keys())[::-1])
            if sesion:
                st.markdown(f"### 📄 {sesion}")
                link_drive, nombre_norma = obtener_enlace_norma(sesion)
                st.markdown(f"""
                <div class="norma-box">
                    <b>📂 Documento Oficial Relacionado:</b> <a href="{link_drive}" target="_blank">Abrir {nombre_norma}</a>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(diario[sesion])
        else:
            st.info("Aún no hay sesiones guardadas en tu diario.")
            
    with tab2:
        examenes = datos_globales[usuario].get("historial_examenes", [])
        if examenes:
            df = pd.DataFrame(examenes)
            col1, col2 = st.columns(2)
            with col1: st.metric("Simulacros Realizados", len(df))
            with col2: st.metric("Efectividad Promedio", f"{df['Efectividad'].mean():.1f}%")
            
            st.divider()
            st.line_chart(df, y="Efectividad", x="Fecha", use_container_width=True)
            st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Aún no tienes simulacros registrados.")
