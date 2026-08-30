import json
import os
import datetime
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types
from streamlit_gsheets import GSheetsConnection 

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS VISUALES ---
st.set_page_config(page_title="Plataforma Experta CNSC 2026", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    .header-title { 
        font-size: 2.4rem; 
        font-weight: 800; 
        color: #38BDF8; 
        border-bottom: 4px solid #3B82F6; 
        padding-bottom: 12px; 
        margin-bottom: 25px;
    }
    .norma-box { 
        border-left: 6px solid #2563EB; 
        padding: 18px; 
        margin: 20px 0; 
        background: rgba(37, 99, 235, 0.1); 
        border-radius: 8px; 
    }
    .pregunta-card { 
        border: 1px solid #334155; 
        padding: 22px; 
        border-radius: 10px; 
        margin-bottom: 20px; 
        background-color: #1E293B;
    }
    .resultado-box { 
        background: rgba(34, 197, 94, 0.1); 
        border-left: 6px solid #22C55E; 
        padding: 22px; 
        border-radius: 10px; 
        margin: 20px 0; 
    }
    .feedback-box {
        background: rgba(245, 158, 11, 0.1);
        border-left: 6px solid #F59E0B;
        padding: 18px;
        border-radius: 8px;
        margin: 20px 0;
    }
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        font-weight: 600;
        background-color: #334155;
        color: #F8FAFC;
        border: 1px solid #475569;
    }
    .stButton>button:hover {
        background-color: #475569;
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CREDENCIALES SEGURIZADAS Y MAPA DE DOCUMENTOS ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    API_KEY = None

USUARIOS_PERMITIDOS = ["MARCELA2026", "LELY2026", "KARO2026", "CHECHO2026", "ISABELLA2026", "CARLA2026"]
CLAVE_SECRETA = "docente2026"
ARCHIVO_DATOS = "datos_estudio_maestro_v20.json"

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
    "Legislación Educativa y Debido Proceso": [
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
    "Excel y Ofimática Docente": [
        "https://docs.google.com/document/d/1KXsLDV_48tQnphfTedD2GesfhoztrDBW/edit?usp=sharing",
        "https://docs.google.com/document/d/1l5gyiJJXAT0x2xwAgQox1gQo24fLXjEp/edit?usp=sharing",
        "https://drive.google.com/file/d/15MtwY1NPnKhbLo_7uY_uCE8R83HWiNJq/view?usp=sharing"
    ]
}

VIDEOS_EXACTOS = {
    "Porcentajes": "https://www.youtube.com/watch?v=ZZw7_m2x0Vw",
    "Regla de 3 Simple (Directa e Inversa)": "https://www.youtube.com/watch?v=kY3y7q_oG8s",
    "Regla de 3 Compuesta": "https://www.youtube.com/watch?v=hN7mQ02lJ40",
    "Relaciones y Proporciones": "https://www.youtube.com/watch?v=W5v5x5Y7x7Y",
    "Sucesiones": "https://www.youtube.com/watch?v=5z3W81v2l7A",
    "Ecuaciones de primer grado": "https://www.youtube.com/watch?v=7q3J4vL1x7Q",
    "Análisis de gráficas": "https://www.youtube.com/watch?v=9x3V1l8k57A",
    "Pensamiento abstracto": "https://www.youtube.com/watch?v=1x2v3u4v5w6",
    "Debido Proceso y Casos Disciplinarios": "https://www.youtube.com/watch?v=1x2v3u4v5w6",
    "Excel y Herramientas Ofimáticas CNSC": "https://www.youtube.com/watch?v=hN7mQ02lJ40"
}

def obtener_enlaces_por_area(area):
    area_lower = area.lower()
    if any(palabra in area_lower for palabra in ["porcentaje", "regla", "sucesion", "ecuacion", "abstracto", "grafica", "numérica"]):
        return BIBLIOTECA_ESPECIFICA["Aptitud Numérica"], "Aptitud Numérica"
    elif any(palabra in area_lower for palabra in ["sinonimo", "antonimo", "analogia", "lectora", "oraciones", "verbal"]):
        return BIBLIOTECA_ESPECIFICA["Aptitud Verbal"], "Aptitud Verbal"
    elif any(palabra in area_lower for palabra in ["ley", "decreto", "guia", "legislacion", "proceso"]):
        return BIBLIOTECA_ESPECIFICA["Legislación Educativa y Debido Proceso"], "Legislación Educativa y Debido Proceso"
    elif any(palabra in area_lower for palabra in ["excel", "office", "ofimatica", "word", "powerpoint"]):
        return BIBLIOTECA_ESPECIFICA["Excel y Ofimática Docente"], "Excel y Ofimática Docente"
    else:
        return BIBLIOTECA_ESPECIFICA["Pedagogía"], "Pedagogía"

def renderizar_caja_documentos(enlaces, nombre_cat, tema):
    html_links = "".join([f"<li><a href='{link}' target='_blank' style='color: #38BDF8;'>📄 Documento oficial de {nombre_cat} {i+1}</a></li>" for i, link in enumerate(enlaces)])
    url_video_exacto = VIDEOS_EXACTOS.get(tema, "https://www.youtube.com/watch?v=ZZw7_m2x0Vw")
    
    return f"""
    <div class="norma-box">
        <b>🔍 Respaldo Oficial ({nombre_cat}):</b> Estudia este tema directamente desde tus archivos exactos de Drive:
        <ul class="link-list">
            {html_links}
        </ul>
        <hr style="margin: 12px 0; border: 0; border-top: 1px solid #3B82F6;">
        <b>📺 Enlace Directo al Video de Estudio:</b>
        <ul class="link-list">
            <li><a href='{url_video_exacto}' target='_blank' style='color: #4ADE80; font-weight: bold;'>▶️ Ver videotutorial clave para dominar: {tema}</a></li>
        </ul>
    </div>
    """

# --- 3. BASE DE DATOS HÍBRIDA (LOCAL + DRIVE) ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    conn = None

def cargar_datos():
    # Intenta leer localmente primero para asegurar velocidad y estabilidad
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
            
    # Si no hay local, intenta leer de Drive
    if conn is not None:
        try:
            df = conn.read(worksheet="Historial", ttl=0)
            if not df.empty:
                datos = {usr: {"historial_examenes": [], "historial_minisimulacros": [], "diario_estudio": {}} for usr in USUARIOS_PERMITIDOS}
                for _, row in df.iterrows():
                    usr = str(row["Usuario"]).strip().upper()
                    tipo = str(row["Tipo"]).strip()
                    try:
                        contenido = json.loads(str(row["Contenido"]))
                    except:
                        continue
                    if usr not in datos: datos[usr] = {"historial_examenes": [], "historial_minisimulacros": [], "diario_estudio": {}}
                    if tipo == "Examen": datos[usr]["historial_examenes"].append(contenido)
                    elif tipo == "Minisimulacro": datos[usr]["historial_minisimulacros"].append(contenido)
                    elif tipo == "Diario": datos[usr]["diario_estudio"][str(row["Clave"])] = contenido
                return datos
        except Exception:
            pass
            
    return {usr: {"historial_examenes": [], "historial_minisimulacros": [], "diario_estudio": {}} for usr in USUARIOS_PERMITIDOS}

def guardar_datos(datos):
    # 1. Guardado local ultra seguro (Nunca pierdes tus datos)
    try:
        with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error guardado local: {e}")

    # 2. Guardado en Drive silencioso
    if conn is not None:
        try:
            filas = []
            for usr, data in datos.items():
                for ex in data.get("historial_examenes", []):
                    filas.append({"Usuario": usr, "Tipo": "Examen", "Clave": "", "Contenido": json.dumps(ex, ensure_ascii=False)})
                for mini in data.get("historial_minisimulacros", []):
                    filas.append({"Usuario": usr, "Tipo": "Minisimulacro", "Clave": "", "Contenido": json.dumps(mini, ensure_ascii=False)})
                for clave, cont in data.get("diario_estudio", {}).items():
                    filas.append({"Usuario": usr, "Tipo": "Diario", "Clave": clave, "Contenido": json.dumps(cont, ensure_ascii=False)})
            
            df_nuevo = pd.DataFrame(filas)
            if df_nuevo.empty: df_nuevo = pd.DataFrame(columns=["Usuario", "Tipo", "Clave", "Contenido"])
            conn.update(worksheet="Historial", data=df_nuevo)
        except Exception:
            pass # Falla silenciosa en Drive, la app sigue funcionando gracias al archivo local

datos_globales = cargar_datos()

for usr in USUARIOS_PERMITIDOS:
    if usr not in datos_globales:
        datos_globales[usr] = {"historial_examenes": [], "historial_minisimulacros": [], "diario_estudio": {}}
    if "historial_minisimulacros" not in datos_globales[usr]:
        datos_globales[usr]["historial_minisimulacros"] = []

# --- 4. VALIDACIÓN DE API KEY Y LOGIN ---
if not API_KEY:
    st.error("⚠️ No se ha configurado la API Key de Gemini en st.secrets.")
    st.stop()

if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None

if st.session_state.usuario_actual is None:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="header-title" style="text-align: center;">🏛️ Plataforma CNSC 2026</div>', unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94A3B8;'>Sistema Experto de Preparación Docente con Inteligencia Artificial</p>", unsafe_allow_html=True)
        
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
        "🎯 Exámenes por Área Específica",
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
    if "proceso" in tema_exacto.lower() or "disciplinario" in tema_exacto.lower() or "ley 1620" in tema_exacto.lower():
        return f"""
        Eres un evaluador riguroso de la CNSC. Genera EXACTAMENTE 10 preguntas complejas y EXTENSAS basadas en casos prácticos sobre: {tema_exacto}. 
        Devuelve ÚNICAMENTE un arreglo JSON válido, sin bloques de código Markdown alrededor.
        Formato estricto:
        [
          {{
            "id": 1,
            "contexto": "Caso detallado...",
            "enunciado": "Pregunta analítica...",
            "opciones": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
            "correcta": "A",
            "justificacion": "Explicación jurídica...",
            "cita_legal": "Norma o artículo"
          }}
        ]
        """
    else:
        return f"""
        Eres un evaluador riguroso de la CNSC. Genera EXACTAMENTE 10 preguntas complejas de opción múltiple exclusivas del tema: {tema_exacto}.
        Devuelve ÚNICAMENTE un arreglo JSON válido.
        Formato estricto:
        [
          {{
            "id": 1,
            "contexto": "Situación...",
            "enunciado": "Pregunta...",
            "opciones": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
            "correcta": "A",
            "justificacion": "Explicación lógica...",
            "cita_legal": "Regla aplicable"
          }}
        ]
        """

def generar_teoria_y_ejemplos(tema_exacto):
    st.session_state.preguntas_mini = None
    st.session_state.resultado_mini = None
    st.session_state.respuestas_mini = {}
    st.session_state.lista_ejemplos_extra = []
    
    with st.spinner(f"Redactando clase magistral y materiales para: {tema_exacto}..."):
        try:
            resp_texto = client.models.generate_content(
                model="gemini-3.5-flash", 
                contents=PROMPT_TEORIA_ESPECIFICA.format(tema=tema_exacto)
            )
            contenido = resp_texto.text
        except Exception as e:
            # ESCUDO: Mostrará el error real sin recargar la página
            st.error(f"❌ Error de Gemini (Posible límite de cuota superado): {e}")
            return False
    
    enlaces, nom_cat = obtener_enlaces_por_area(tema_exacto)
    caja_html = renderizar_caja_documentos(enlaces, nom_cat, tema_exacto)
    
    st.session_state.tema_activo = tema_exacto
    st.session_state.contenido_tema = contenido
    st.session_state.links_activos = caja_html
    
    fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clave_diario = f"{fecha_hoy} - {usuario} - {tema_exacto}"
    datos_globales[usuario]["diario_estudio"][clave_diario] = contenido
    guardar_datos(datos_globales)
    
    return True

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
            st.error(f"❌ Error al generar el simulacro: {e}")
            return False

def mostrar_diagnostico_y_retroalimentacion(revision_preguntas):
    correctas = [r for r in revision_preguntas if r['Acierto']]
    incorrectas = [r for r in revision_preguntas if not r['Acierto']]
    
    total = len(revision_preguntas)
    porcentaje = (len(correctas) / total) * 100 if total > 0 else 0
    
    st.markdown("### 📊 Diagnóstico de Desempeño por Competencias")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Puntaje Obtenido", f"{len(correctas)} / {total}")
    col2.metric("Efectividad", f"{porcentaje:.1f}%")
    col3.metric("Estado", "Aprobado 🟢" if porcentaje >= 70 else "A Reforzar 🔴")
    
    st.progress(porcentaje / 100)
    
    feedback_html = f"""
    <div class='feedback-box'>
        <h3>💡 Análisis Inteligente de Resultados</h3>
    """
    
    if porcentaje >= 80:
        feedback_html += "<p>🌟 <b>Nivel Alcanzado:</b> Sobresaliente. Tienes un dominio avanzado de las temáticas evaluadas.</p>"
    elif porcentaje >= 50:
        feedback_html += "<p>⚠️ <b>Nivel Alcanzado:</b> Aceptable con áreas de mejora. Posees bases sólidas pero cometes errores en interpretaciones complejas.</p>"
    else:
        feedback_html += "<p>🚨 <b>Nivel Alcanzado:</b> Requiere refuerzo urgente. Es necesario repasar los conceptos fundamentales y los marcos legales.</p>"
        
    feedback_html += "<h4>💪 Tus Fortalezas</h4><ul>"
    if correctas:
        feedback_html += f"<li>Demostraste alta precisión en conceptos clave, resolviendo correctamente {len(correctas)} de {total} ítems evaluados.</li>"
    else:
        feedback_html += "<li>En esta sesión no se registraron aciertos consolidados, lo que indica una excelente oportunidad para estudiar la teoría desde cero.</li>"
    feedback_html += "</ul>"
    
    feedback_html += "<h4>⚠️ Desventajas y Puntos en los que estás Fallando</h4><ul>"
    if incorrectas:
        feedback_html += f"<li>Se identificaron {len(incorrectas)} errores que revelan debilidades en la lectura crítica y en la aplicación directa de normativas.</li>"
        for inc in incorrectas[:3]:
            feedback_html += f"<li><b>Falla detectada en:</b> \"{inc['Pregunta'][:70]}...\" (Respondiste <i>{inc['Tu Respuesta']}</i>, la correcta era <i>{inc['Correcta']}</i>).</li>"
    else:
        feedback_html += "<li>¡Ninguna desventaja detectada en este test! Dominio total de las preguntas formuladas.</li>"
    feedback_html += "</ul></div>"
    
    st.markdown(feedback_html, unsafe_allow_html=True)

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
        "⚖️ 3. Marco Legal y Debido Proceso": [
            "Ley 115 (Ley General de Educación)", "Ley 1098 (Infancia y Adolescencia)", 
            "Ley 1620 (Convivencia Escolar y RAI)", "Debido Proceso y Casos Disciplinarios", 
            "Guía 31 (Evaluación de desempeño)", "Decreto 1421 (Educación inclusiva)"
        ],
        "💻 4. Excel y Ofimática Docente": [
            "Excel y Herramientas Ofimáticas CNSC", "Funciones y Tablas Dinámicas en Informes Escolares", "Gestión de Correo y Documentación Oficial"
        ]
    }
    
    col_menu, col_contenido = st.columns([1, 2.8])
    
    with col_menu:
        st.markdown("### 📚 Selecciona Tema")
        for categoria, subtemas in TEMARIO_DESGLOSADO.items():
            with st.expander(categoria, expanded=False):
                for subtema in subtemas:
                    if st.button(f"📘 {subtema}", key=f"btn_{subtema}"):
                        exito = generar_teoria_y_ejemplos(subtema)
                        if exito:
                            st.rerun() # <- Sólo recarga si no hubo error

    with col_contenido:
        if st.session_state.contenido_tema:
            st.markdown(f"## Módulo Académico: {st.session_state.tema_activo}")
            st.markdown(st.session_state.links_activos, unsafe_allow_html=True)
            st.divider()
            st.markdown(st.session_state.contenido_tema)
            st.divider()
            
            # --- BANCO DE EJEMPLOS ADICIONALES ---
            st.markdown("### ➕ Banco de Ejemplos Adicionales")
            if st.button("➕ Cargar más ejemplos de práctica", type="secondary"):
                with st.spinner("Generando nuevos ejercicios resueltos..."):
                    try:
                        prompt_ej = f"Genera 3 NUEVOS problemas avanzados sobre '{st.session_state.tema_activo}' con su procedimiento detallado."
                        resp_ej = client.models.generate_content(model="gemini-3.5-flash", contents=prompt_ej)
                        st.session_state.lista_ejemplos_extra.append(resp_ej.text)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            for idx, ej_bloque in enumerate(st.session_state.lista_ejemplos_extra):
                with st.container():
                    st.markdown(f"**Ejercicios Adicionales - Bloque {idx + 1}**")
                    st.markdown(ej_bloque)
                    st.write("---")
            
            # --- MINISIMULACRO ---
            st.divider()
            st.markdown(f"### 📝 MINISIMULACRO INTERACTIVO: {st.session_state.tema_activo}")
            
            if not st.session_state.preguntas_mini:
                st.info("¿Comprendiste la teoría? Pon a prueba tus conocimientos con este minisimulacro evaluativo.")
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
                        puntaje, revision = 0, []
                        for p in st.session_state.preguntas_mini:
                            resp = st.session_state.respuestas_mini.get(p['id'])
                            es_correcta = (resp == p['correcta'])
                            if es_correcta: puntaje += 1
                            revision.append({
                                "Pregunta": p['enunciado'], "Tu Respuesta": resp or "Sin responder", 
                                "Correcta": p['correcta'], "Justificación": p['justificacion'], 
                                "Base": p.get('cita_legal', 'N/A'), "Acierto": es_correcta
                            })
                        
                        resultado_eval = {"puntaje": puntaje, "total": len(st.session_state.preguntas_mini), "revision": revision}
                        st.session_state.resultado_mini = resultado_eval
                        
                        registro_mini = {
                            "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Tema": st.session_state.tema_activo,
                            "Puntaje": puntaje, "Total": len(st.session_state.preguntas_mini),
                            "Efectividad": round((puntaje/len(st.session_state.preguntas_mini))*100, 1),
                            "Detalle": revision
                        }
                        datos_globales[usuario]["historial_minisimulacros"].append(registro_mini)
                        guardar_datos(datos_globales)
                        st.rerun()

            elif st.session_state.resultado_mini:
                res = st.session_state.resultado_mini
                st.markdown(f"<div class='resultado-box'><h2>📊 Calificación del Minisimulacro: {res['puntaje']} / {res['total']}</h2></div>", unsafe_allow_html=True)
                
                mostrar_diagnostico_y_retroalimentacion(res['revision'])
                
                st.markdown("### 📋 Detalle de Preguntas y Justificaciones")
                for i, r in enumerate(res['revision']):
                    icono = "✅" if r['Acierto'] else "❌"
                    color_txt = "#4ADE80" if r['Acierto'] else "#F87171"
                    with st.expander(f"{icono} Pregunta {i+1} | Tu opción: {r['Tu Respuesta']} | Correcta: {r['Correcta']}"):
                        st.markdown(f"<span style='color:{color_txt}; font-weight:bold;'>{'Respuesta Correcta' if r['Acierto'] else 'Respuesta Incorrecta'}</span>", unsafe_allow_html=True)
                        st.write(f"**Justificación:** {r['Justificación']}")
                        st.info(f"**Fundamento:** {r['Base']}")
                
                if st.button("🔄 Repetir Minisimulacro (Nuevas Preguntas)"):
                    st.session_state.preguntas_mini = None
                    st.session_state.resultado_mini = None
                    st.session_state.respuestas_mini = {}
                    st.rerun()

# --- MÓDULO 2: SIMULACRO OFICIAL ---
elif modo == "📝 Simulacro Oficial (20 Preguntas)":
    st.markdown('<div class="header-title">📝 Simulacro Oficial Tipo Concurso Docente</div>', unsafe_allow_html=True)
    area_sim = st.selectbox("Selecciona el área a evaluar:", ["Aptitud Numérica", "Aptitud Verbal", "Competencias Pedagógicas y Legislación"])
    
    if st.button("🚀 Generar Evaluación de 20 Preguntas", type="primary"):
        st.session_state.examen_activo = None
        if "resultado_ultimo_examen" in st.session_state: del st.session_state.resultado_ultimo_examen
        
        with st.spinner(f"Construyendo simulacro oficial de {area_sim}..."):
            sys_inst = f"Eres evaluador experto de la CNSC. Genera 20 preguntas exclusivas y exigentes de '{area_sim}'. Devuelve SOLO JSON puro."
            try:
                response = client.models.generate_content(
                    model="gemini-3.5-flash", contents="Genera 20 preguntas JSON puras",
                    config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json", temperature=0.8)
                )
                texto_limpio = response.text[response.text.find('['):response.text.rfind(']')+1] if '[' in response.text else response.text.replace("```json", "").replace("```", "").strip()
                st.session_state.examen_activo = json.loads(texto_limpio)
                st.session_state.respuestas_usuario = {}
            except Exception as e:
                st.error(f"❌ Error al procesar el examen oficial: {e}")

    if st.session_state.examen_activo:
        preguntas = st.session_state.examen_activo
        with st.form("form_ex"):
            for p in preguntas:
                st.markdown(f"<div class='pregunta-card'><b>Pregunta {p.get('id', '*')}</b><br><br><i>{p.get('contexto', '')}</i><br><br><b>{p['enunciado']}</b></div>", unsafe_allow_html=True)
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
                    "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    "Área": area_sim, "Puntaje": puntaje, "Total": len(preguntas), "Efectividad": efectividad
                })
                guardar_datos(datos_globales)
                st.session_state.resultado_ultimo_examen = {"puntaje": puntaje, "total": len(preguntas), "revision": revision}
                st.rerun()

    if "resultado_ultimo_examen" in st.session_state:
        res = st.session_state.resultado_ultimo_examen
        st.success(f"📊 Calificación Final: {res['puntaje']} / {res['total']} ({(res['puntaje']/res['total'])*100:.1f}%)")
        mostrar_diagnostico_y_retroalimentacion(res['revision'])
        for i, r in enumerate(res['revision']):
            icono = "✅" if r['Acierto'] else "❌"
            with st.expander(f"{icono} Pregunta {i+1} | Tu opción: {r['Tu Respuesta']} | Correcta: {r['Correcta']}"):
                st.write(f"**Justificación:** {r['Justificación']}")

# --- MÓDULO 3: EXÁMENES POR ÁREA ESPECÍFICA ---
elif modo == "🎯 Exámenes por Área Específica":
    st.markdown('<div class="header-title">🎯 Módulo de Exámenes por Área Específica</div>', unsafe_allow_html=True)
    area_especifica = st.selectbox("Selecciona el área de profundización:", [
        "Excel y Ofimática Docente (Basado en exámenes anteriores CNSC)",
        "Debido Proceso y Casos Disciplinarios Institucionales",
        "Competencias Pedagógicas y Didácticas Específicas"
    ])
    
    if st.button("🚀 Generar Examen Especializado (15 Preguntas)", type="primary"):
        st.session_state.examen_especifico = None
        if "resultado_especifico" in st.session_state: del st.session_state.resultado_especifico
        
        with st.spinner(f"Construyendo banco especializado para: {area_especifica}..."):
            sys_inst = f"Eres evaluador experto de la CNSC. Genera 15 preguntas JSON sobre '{area_especifica}'."
            try:
                response = client.models.generate_content(
                    model="gemini-3.5-flash", contents="Genera 15 preguntas JSON puras",
                    config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json", temperature=0.8)
                )
                texto_limpio = response.text[response.text.find('['):response.text.rfind(']')+1] if '[' in response.text else response.text.replace("```json", "").replace("```", "").strip()
                st.session_state.examen_especifico = json.loads(texto_limpio)
                st.session_state.respuestas_especifico = {}
            except Exception as e:
                st.error(f"❌ Error al procesar el examen: {e}")

    if "examen_especifico" in st.session_state and st.session_state.examen_especifico:
        preguntas_esp = st.session_state.examen_especifico
        with st.form("form_esp"):
            for p in preguntas_esp:
                st.markdown(f"<div class='pregunta-card'><b>Pregunta {p.get('id', '*')}</b><br><br><b>{p['enunciado']}</b></div>", unsafe_allow_html=True)
                st.session_state.respuestas_especifico[p['id']] = st.radio("Selecciona opción:", options=list(p["opciones"].keys()), format_func=lambda x: f"{x}) {p['opciones'][x]}", key=f"esp_{p['id']}", index=None)
            
            if st.form_submit_button("📥 Enviar y Calificar Examen Especializado", type="primary"):
                puntaje, revision = 0, []
                for p in preguntas_esp:
                    resp = st.session_state.respuestas_especifico.get(p['id'])
                    es_correcta = (resp == p['correcta'])
                    if es_correcta: puntaje += 1
                    revision.append({
                        "Pregunta": p['enunciado'], "Tu Respuesta": resp or "N/A", 
                        "Correcta": p['correcta'], "Justificación": p['justificación'], 
                        "Acierto": es_correcta
                    })
                
                datos_globales[usuario]["historial_examenes"].append({
                    "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    "Área": f"Específica: {area_especifica}", "Puntaje": puntaje, "Total": len(preguntas_esp), "Efectividad": round((puntaje/len(preguntas_esp))*100, 1)
                })
                guardar_datos(datos_globales)
                st.session_state.resultado_especifico = {"puntaje": puntaje, "total": len(preguntas_esp), "revision": revision}
                st.rerun()

    if "resultado_especifico" in st.session_state:
        res_esp = st.session_state.resultado_especifico
        st.success(f"📊 Calificación Examen Específico: {res_esp['puntaje']} / {res_esp['total']}")
        mostrar_diagnostico_y_retroalimentacion(res_esp['revision'])

# --- MÓDULO 4: HISTORIAL Y PROGRESO ---
elif modo == "📅 Historial y Progreso":
    st.markdown('<div class="header-title">📅 Historial de Progreso y Diario de Estudio</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📈 Simulacros Oficiales", "🎯 Minisimulacros", "📚 Diario de Estudio"])
    
    with tab1:
        examenes = datos_globales[usuario].get("historial_examenes", [])
        if examenes:
            df = pd.DataFrame(examenes)
            st.line_chart(df, y="Efectividad", x="Fecha", use_container_width=True)
            st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("No registra simulacros.")
            
    with tab2:
        minis = datos_globales[usuario].get("historial_minisimulacros", [])
        if minis:
            for idx, m in enumerate(minis[::-1]):
                with st.expander(f"📌 [{m['Fecha']}] Tema: {m['Tema']} — Puntaje: {m['Puntaje']}/{m['Total']} ({m['Efectividad']}%)"):
                    for q_idx, det in enumerate(m['Detalle']):
                        ic = "✅" if det['Acierto'] else "❌"
                        st.markdown(f"**{ic} Pregunta {q_idx+1}:** {det['Pregunta']}")
                        st.write(f"*Tu respuesta:* {det['Tu Respuesta']} | *Correcta:* {det['Correcta']}")
        else:
            st.info("Aún no has completado minisimulacros.")

    with tab3:
        diario = datos_globales[usuario].get("diario_estudio", {})
        if diario:
            sesion = st.selectbox("Selecciona la sesión guardada:", list(diario.keys())[::-1])
            if sesion:
                st.markdown(diario[sesion])
        else:
            st.info("No hay sesiones registradas.")
