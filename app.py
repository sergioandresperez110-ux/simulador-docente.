import json
import os
import datetime
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS LIMPIOS ---
st.set_page_config(page_title="Plataforma Experta CNSC 2026", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    .header-title { font-size: 2.2rem; font-weight: 800; border-bottom: 3px solid #3B82F6; padding-bottom: 10px; margin-bottom: 20px;}
    .norma-box { border-left: 5px solid #2563EB; padding: 12px; margin: 15px 0; background-color: rgba(37, 99, 235, 0.05); border-radius: 4px; }
    .pregunta-card { border: 1px solid #E2E8F0; padding: 20px; border-radius: 8px; margin-bottom: 15px; }
    .stTextInput>div>div>input { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- 2. CREDENCIALES Y MAPA DE ENLACES ESPECÍFICOS DE GOOGLE DRIVE ---
API_KEY = "AQ.Ab8RN6IT6-t3t77qXYzFiVNyakzVr-4cTvUU9Skrh9E_o9r6Tw"
USUARIOS_PERMITIDOS = ["MARCELA2026", "LELY2026", "KARO2026", "CHECHO2026"]
CLAVE_SECRETA = "docente2026"
ARCHIVO_DATOS = "datos_estudio_maestro_v2.json"

# Enlaces directos y específicos para que constates la información real
ENLACES_NORMATIVOS = {
    "ley 1620": "https://drive.google.com/drive/folders/12dgYySHb9BnINgYTSuOqvM4ru-1VhxRW?usp=sharing", # Reemplaza con el link específico de Ley 1620 si lo deseas
    "decreto 1290": "https://drive.google.com/drive/folders/12dgYySHb9BnINgYTSuOqvM4ru-1VhxRW?usp=sharing",
    "ley 115": "https://drive.google.com/drive/folders/12dgYySHb9BnINgYTSuOqvM4ru-1VhxRW?usp=sharing",
    "general": "https://drive.google.com/drive/folders/12dgYySHb9BnINgYTSuOqvM4ru-1VhxRW?usp=sharing"
}

def obtener_enlace_norma(texto):
    texto_lower = texto.lower()
    for clave, link in ENLACES_NORMATIVOS.items():
        if clave in texto_lower:
            return link, clave.upper()
    return ENLACES_NORMATIVOS["general"], "Documentación Oficial MEN"

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
        st.markdown('<div class="header-title">🏛️ Acceso Seguro CNSC</div>', unsafe_allow_html=True)
        st.info("Ingresa tus credenciales para acceder a tu historial y ruta.")
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
        "🗺️ Ruta de Estudio Inteligente", 
        "📖 Biblioteca y Módulos de Estudio", 
        "📝 Simulacro Oficial (20 Preg. + Tiempo)", 
        "📅 Historial Día a Día y Progreso"
    ])
    st.divider()
    area_evaluacion = st.selectbox(
        "Área de Enfoque:",
        ["Competencias Pedagógicas (Legislación)", "Lectura Crítica", "Razonamiento Cuantitativo", "Tecnología e Informática"]
    )
    st.markdown(f"[📂 Abrir Biblioteca General]({ENLACES_NORMATIVOS['general']})")

# --- MÓDULO 1: RUTA DE ESTUDIO INTELIGENTE ---
if modo == "🗺️ Ruta de Estudio Inteligente":
    st.markdown('<div class="header-title">🗺️ Ruta de Estudio Oficial - CNSC 2026</div>', unsafe_allow_html=True)
    st.info("Selecciona cualquier fase del plan maestro. La IA redactará el contenido y te entregará el enlace exacto del documento de respaldo para verificar la norma.")
    
    fases_estudio = [
        {"fase": "Fase 1: Marco Legal y Convivencia Escolar", "tema": "Ley 1620 y Rutas de Atención Integral", "desc": "Protocolos obligatorios ante situaciones de conflicto y acoso escolar."},
        {"fase": "Fase 2: Evaluación y Promoción Institucional", "tema": "Decreto 1290 de Evaluación del Aprendizaje", "desc": "Criterios de valoración y escalas de calificación institucional."},
        {"fase": "Fase 3: Fundamentos Pedagógicos", "tema": "Ley 115 (Ley General de Educación)", "desc": "Estructura del sistema educativo colombiano y fines de la educación."},
        {"fase": "Fase 4: Juicio Situacional", "tema": "Resolución de Casos Pedagógicos Complejos", "desc": "Análisis de situaciones de aula bajo el enfoque de derechos."}
    ]
    
    for item in fases_estudio:
        st.markdown(f"### {item['fase']}")
        st.write(f"**Tema:** {item['tema']} — {item['desc']}")
        if st.button(f"🚀 Cargar y Estudiar: {item['tema']}", key=f"ruta_{item['tema']}"):
            with st.spinner(f"Generando lección experta sobre {item['tema']}..."):
                prompt = f"""Actúa como experto en el Concurso Docente de Colombia. Escribe una lección completa, rigurosa y estructurada sobre: '{item['tema']}'. 
                Incluye los artículos exactos de la norma, los conceptos fundamentales y cómo lo evalúa la CNSC."""
                
                respuesta = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
                st.session_state.tema_activo = item['tema']
                st.session_state.contenido_tema = respuesta.text
                
                # Guardar en el historial diario exacto
                fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                key_historial = f"{fecha_hoy} - {item['tema']}"
                datos_globales[usuario]["diario_estudio"][key_historial] = respuesta.text
                guardar_datos(datos_globales)
                st.rerun()
        st.divider()

    if st.session_state.contenido_tema:
        link_drive, nombre_norma = obtener_enlace_norma(st.session_state.tema_activo)
        st.markdown(f"""
        <div class="norma-box">
            <b>🔍 Constatación Documental:</b> Este tema está respaldado por la normatividad oficial. 
            Puedes abrir y constatar el documento exacto aquí: <a href="{link_drive}" target="_blank">{nombre_norma} en Google Drive</a>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(st.session_state.contenido_tema)

# --- MÓDULO 2: BIBLIOTECA Y MÓDULOS DE ESTUDIO ---
elif modo == "📖 Biblioteca y Módulos de Estudio":
    st.markdown('<div class="header-title">📖 Consulta y Generación de Contenido Experto</div>', unsafe_allow_html=True)
    
    tema_libre = st.text_input("¿Qué norma, ley o concepto específico deseas investigar hoy?")
    if st.button("Generar Material de Estudio", type="primary") and tema_libre:
        with st.spinner("Investigando y redactando apuntes..."):
            prompt = f"""Redacta un documento maestro de estudio sobre '{tema_libre}' para el Concurso Docente de Colombia, 
            citando artículos y principios normativos oficiales."""
            resp = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
            st.session_state.tema_activo = tema_libre
            st.session_state.contenido_tema = resp.text
            
            fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            key_historial = f"{fecha_hoy} - {tema_libre}"
            datos_globales[usuario]["diario_estudio"][key_historial] = resp.text
            guardar_datos(datos_globales)

    if st.session_state.contenido_tema:
        link_drive, nombre_norma = obtener_enlace_norma(st.session_state.tema_activo)
        st.markdown(f"### Módulo: {st.session_state.tema_activo}")
        st.markdown(f"""
        <div class="norma-box">
            <b>🔍 Verificar en Documento Original:</b> Constata la validez de esta información en el archivo correspondiente: 
            <a href="{link_drive}" target="_blank">Abrir {nombre_norma} en Google Drive</a>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(st.session_state.contenido_tema)

# --- MÓDULO 3: SIMULACRO OFICIAL ---
elif modo == "📝 Simulacro Oficial (20 Preg. + Tiempo)":
    st.markdown('<div class="header-title">📝 Simulacro Oficial con Exigencia Real (20 Preguntas)</div>', unsafe_allow_html=True)
    st.warning("⏱️ Prueba de 20 preguntas de juicio situacional con rigor de la CNSC. Incluye justificaciones basadas en normatividad.")
    
    if st.button("🚀 Generar Nuevo Simulacro", type="primary"):
        st.session_state.examen_activo = None
        if "resultado_ultimo_examen" in st.session_state: del st.session_state.resultado_ultimo_examen
        
        with st.spinner("Construyendo 20 casos situacionales estrictos..."):
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
                <div class="pregunta-card">
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
                        "Correcta": p['correcta'], "Justificación": p['justificación'], "Base": p.get('cita_legal', 'Normativa MEN')
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
        st.success(f"📊 Calificación: {res['puntaje']} / {res['total']}")
        for i, r in enumerate(res['revision']):
            link_drive, nombre_norma = obtener_enlace_norma(r['Base'])
            with st.expander(f"Pregunta {i+1} | Tu opción: {r['Tu Respuesta']} | Correcta: {r['Correcta']}"):
                st.write(f"**Justificación:** {r['Justificación']}")
                st.info(f"**Sustento Legal:** {r['Base']} | [📂 Verificar en {nombre_norma}]({link_drive})")

# --- MÓDULO 4: HISTORIAL DÍA A DÍA Y PROGRESO ---
elif modo == "📅 Historial Día a Día y Progreso":
    st.markdown('<div class="header-title">📅 Historial Día a Día y Evolución Académica</div>', unsafe_allow_html=True)
    st.write(f"Aquí puedes auditar cada paso de tu estudio diario, **{usuario}**. Selecciona una fecha anterior para desplegar exactamente el contenido que estudiaste ese día.")
    
    tab1, tab2 = st.tabs(["📚 Diario de Estudio (Contenido Exacto)", "📈 Gráficas de Simulacros"])
    
    with tab1:
        diario = datos_globales[usuario].get("diario_estudio", {})
        if diario:
            sesion_seleccionada = st.selectbox("Selecciona la sesión de estudio guardada:", list(diario.keys())[::-1])
            if sesion_seleccionada:
                st.markdown(f"### Apuntes de la sesión: {sesion_seleccionada}")
                link_drive, nombre_norma = obtener_enlace_norma(sesion_seleccionada)
                st.markdown(f"""
                <div class="norma-box">
                    <b>📂 Documento Original de Respaldo:</b> <a href="{link_drive}" target="_blank">Abrir {nombre_norma} en Google Drive</a>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(diario[sesion_seleccionada])
        else:
            st.info("Aún no tienes sesiones de estudio guardadas. Genera contenido en la Ruta Inteligente o Biblioteca.")
            
    with tab2:
        examenes = datos_globales[usuario].get("historial_examenes", [])
        if examenes:
            df = pd.DataFrame(examenes)
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric("Total Simulacros Presentados", len(df))
            with col_m2:
                prom_efectividad = df["Efectividad"].mean()
                st.metric("Efectividad Promedio Global", f"{prom_efectividad:.1f}%")
                
            st.divider()
            st.subheader("📈 Evolución de la Efectividad por Examen (%)")
            st.line_chart(df, y="Efectividad", x="Fecha", use_container_width=True)
            
            st.divider()
            st.subheader("📑 Registro de Pruebas")
            st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Aún no tienes simulacros registrados.")
