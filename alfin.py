import streamlit as st
import sqlite3
import pandas as pd
import time
from datetime import date
import re

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS (DISEÑO LIMPIO NEGRO & AMARILLO)
# ---------------------------------------------------------
st.set_page_config(
    page_title="YSIVAMOS - Fitness Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS de alto contraste y legibilidad
st.markdown("""
<style>
    /* Fondo principal negro mate */
    .stApp {
        background-color: #0D0D0D !important;
        color: #F0F0F0 !important;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #141414 !important;
        border-right: 2px solid #222222 !important;
    }

    /* Tipografías y Encabezados */
    h1 {
        color: #FFD700 !important;
        font-weight: 900 !important;
        font-size: 2.2rem !important;
        margin-bottom: 0.5rem !important;
    }
    h2, h3 {
        color: #FFD700 !important;
        font-weight: 800 !important;
    }
    p, label, span {
        color: #E0E0E0 !important;
        font-size: 1.05rem !important;
    }

    /* Tarjetas Modulares (Cards) */
    .card-box {
        background-color: #161616;
        border: 1px solid #2D2D2D;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }

    /* Botones Principales (Amarillo Neón / Texto Negro Impreso) */
    div.stButton > button:first-child {
        background: #FFD700 !important;
        color: #000000 !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.75rem 1.5rem !important;
        width: 100% !important;
        cursor: pointer !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button:first-child:hover {
        background: #FFE033 !important;
        transform: scale(1.02) !important;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.4) !important;
    }

    /* Inputs y Selectboxes */
    .stTextInput input, .stNumberInput input, div[data-baseweb="select"] > div {
        background-color: #222222 !important;
        color: #FFFFFF !important;
        border: 1px solid #444444 !important;
        border-radius: 8px !important;
        font-size: 1.1rem !important;
    }

    /* Métricas */
    [data-testid="stMetricValue"] {
        color: #FFD700 !important;
        font-size: 2.5rem !important;
        font-weight: 900 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #AAAAAA !important;
        font-size: 1.1rem !important;
    }

    /* Tablas de datos */
    [data-testid="stDataFrame"] {
        background-color: #1A1A1A !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. BASE DE DATOS Y AUTENTICACIÓN
# ---------------------------------------------------------
conn = sqlite3.connect("fitness_app.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT, provider TEXT, status TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS registro_entrenamiento 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, fecha TEXT, bloque TEXT, ejercicio TEXT, peso REAL, reps INT, rpe INT)''')

c.execute('''CREATE TABLE IF NOT EXISTS registro_nutricion 
             (user_email TEXT, fecha TEXT, proteinas REAL, carbos REAL, grasas REAL, agua REAL, PRIMARY KEY (user_email, fecha))''')
conn.commit()

if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'auth_stage' not in st.session_state:
    st.session_state['auth_stage'] = 'login'
if 'temp_email' not in st.session_state:
    st.session_state['temp_email'] = ""

# BASE DE DATOS DE RUTINAS
RUTINAS = {
    "⚡ Día 1: Upper (Torso - Fuerza)": [
        "Press Inclinado con Mancuernas",
        "Jalón al Pecho Agarre Abierto",
        "Press Militar con Mancuernas Sentado",
        "Remo Bajo en Polea Agarre Neutro/Triángulo",
        "Superset: Rosca en Polea + Tríceps Cuerda"
    ],
    "⚡ Día 2: Lower (Pierna - Fuerza)": [
        "Sentadilla Libre con Barra",
        "Leg Press 45°",
        "Sillón Extensor",
        "Camilla Flexora",
        "Elevación de Talones / Pantorrilla Sentado",
        "Plancha Abdominal (Core)"
    ],
    "⚡ Día 4: Push (Empuje - Hipertrofia)": [
        "Supino Inclinado o Plano (Barra/Mancuernas)",
        "Crossover en Polea Alta",
        "Elevaciones Laterales con Mancuernas",
        "Desarrollo de Hombros en Máquina o Mancuernas",
        "Tríceps Francés con Mancuerna/Anilla",
        "Tríceps en Polea con Cuerda"
    ],
    "⚡ Día 5: Pull (Tirón - Hipertrofia)": [
        "Jalón Neutro (Triángulo)",
        "Remo Unilateral con Mancuerna",
        "Crucifijo Inverso en Máquina (Hombro Posterior)",
        "Encogimiento de Hombros con Mancuernas (Trapézio)",
        "Rosca Directa en Polea con Barra Recta",
        "Rosca Alternada con Mancuernas"
    ],
    "⚡ Día 6: Legs (Pierna 2 - Cadena Posterior)": [
        "Leg Press 45°",
        "Camilla Flexora",
        "Sillón Extensor",
        "Máquina de Aducción de Cadera",
        "Máquina de Abducción de Cadera",
        "Pantorrilla en Leg Press o Sentado"
    ]
}

# ---------------------------------------------------------
# 3. PANTALLA DE LOGIN
# ---------------------------------------------------------
def login_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><h1 style='text-align: center;'>⚡ YSIVAMOS FITNESS</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #AAAAAA; font-size: 1.2rem;'>Inicia sesión para acceder a tus rutinas y nutrición</p><br>", unsafe_allow_html=True)

        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        if st.session_state['auth_stage'] == 'login':
            st.subheader("Acceso a la Cuenta")
            
            email_input = st.text_input("Correo Electrónico", placeholder="ejemplo@correo.com")
            
            if st.button("🌐 Acceso Rápido con Google / Correo"):
                if re.match(r"[^@]+@[^@]+\.[^@]+", email_input):
                    st.session_state['temp_email'] = email_input
                    st.session_state['auth_stage'] = 'verify'
                    st.success("¡Código enviado! Usa el código de verificación: 123456")
                    st.rerun()
                else:
                    st.error("Ingresa un correo electrónico válido.")

            st.write("---")
            st.markdown("### O ingresa con tu Contraseña")
            pass_input = st.text_input("Contraseña", type="password")
            if st.button("Ingresar"):
                c.execute("SELECT email FROM usuarios WHERE email=? AND password=?", (email_input, pass_input))
                user = c.fetchone()
                if user:
                    st.session_state['user'] = user[0]
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

        elif st.session_state['auth_stage'] == 'verify':
            st.subheader(f"Verificar: {st.session_state['temp_email']}")
            code_input = st.text_input("Código de 6 dígitos", placeholder="123456")
            
            if st.button("Confirmar Código"):
                if code_input == "123456":
                    c.execute("INSERT OR IGNORE INTO usuarios (email, provider, status) VALUES (?, ?, ?)", (st.session_state['temp_email'], "email", "activo"))
                    conn.commit()
                    st.session_state['auth_stage'] = 'set_password'
                    st.rerun()
                else:
                    st.error("Código incorrecto. Usa 123456")

        elif st.session_state['auth_stage'] == 'set_password':
            st.subheader("Crea tu Contraseña (Opcional)")
            new_pass = st.text_input("Nueva Contraseña", type="password")
            
            if st.button("Guardar e Iniciar Sesión"):
                if new_pass:
                    c.execute("UPDATE usuarios SET password=? WHERE email=?", (new_pass, st.session_state['temp_email']))
                    conn.commit()
                st.session_state['user'] = st.session_state['temp_email']
                st.session_state['auth_stage'] = 'login'
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. APLICACIÓN PRINCIPAL (POST-LOGIN)
# ---------------------------------------------------------
if not st.session_state['user']:
    login_screen()
else:
    # Sidebar
    st.sidebar.markdown(f"### 👤 Usuario\n`{st.session_state['user']}`")
    
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state['user'] = None
        st.session_state['auth_stage'] = 'login'
        st.rerun()

    st.sidebar.write("---")
    opcion = st.sidebar.radio("MENÚ PRINCIPAL", ["🏋️ Registrar Rutina", "⏱️ Temporizador", "🥗 Nutrición", "📈 Sobrecarga Progresiva"])

    # 1. ENTRENAMIENTO
    if opcion == "🏋️ Registrar Rutina":
        st.markdown("# 🏋️ Registro de Entrenamiento")
        st.write("Registra tus cargas diarias para evaluar tu sobrecarga progresiva.")
        
        col1, col2 = st.columns([1.3, 1])
        
        with col1:
            st.markdown("<div class='card-box'>", unsafe_allow_html=True)
            st.subheader("1. Selección de Ejercicio")
            bloque_sel = st.selectbox("Selecciona la Rutina del Día:", list(RUTINAS.keys()))
            ejercicio_sel = st.selectbox("Selecciona el Ejercicio:", RUTINAS[bloque_sel])
            
            st.subheader("2. Carga y Esfuerzo")
            col_p, col_r = st.columns(2)
            with col_p:
                peso = st.number_input("Carga Utilizada (kg)", min_value=0.0, value=20.0, step=0.5)
            with col_r:
                reps = st.number_input("Repeticiones", min_value=1, value=10, step=1)
                
            rpe = st.select_slider("Esfuerzo Percibido (RPE 1 al 10)", options=list(range(1, 11)), value=8)
            
            st.write("<br>", unsafe_allow_html=True)
            if st.button("💾 REGISTRAR SERIE"):
                fecha_actual = str(date.today())
                c.execute("INSERT INTO registro_entrenamiento (user_email, fecha, bloque, ejercicio, peso, reps, rpe) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (st.session_state['user'], fecha_actual, bloque_sel, ejercicio_sel, peso, reps, rpe))
                conn.commit()
                st.success(f"✅ ¡Guardado! {ejercicio_sel} — {peso} kg x {reps} reps (RPE {rpe})")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='card-box'>", unsafe_allow_html=True)
            st.subheader("💡 Claves de Técnica")
            st.markdown(f"**Ejercicio:** {ejercicio_sel}")
            st.info("""
            📌 **Indicaciones clave:**
            • Mantén retracción escapular y postura firme.
            • Controla la fase excéntrica (bajada) en 2 a 3 segundos.
            • Aplica el rango de movimiento completo sin impulso.
            """)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 📋 Series Registradas Hoy")
        df_hoy = pd.read_sql_query(f"SELECT bloque AS 'Rutina', ejercicio AS 'Ejercicio', peso AS 'Peso (kg)', reps AS 'Reps', rpe AS 'RPE' FROM registro_entrenamiento WHERE user_email='{st.session_state['user']}' AND fecha='{date.today()}'", conn)
        if not df_hoy.empty:
            st.dataframe(df_hoy, use_container_width=True)
        else:
            st.info("Aún no has registrado series el día de hoy.")

    # 2. TEMPORIZADOR
    elif opcion == "⏱️ Temporizador":
        st.markdown("# ⏱️ Cronómetro de Descanso")
        st.write("Mantén un descanso exacto entre series para maximizar el rendimiento.")
        
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        col_t1, col_t2, col_t3 = st.columns(3)
        tiempo_seg = 0
        if col_t1.button("⏱️ 60 Segundos"):
            tiempo_seg = 60
        if col_t2.button("⏱️ 90 Segundos"):
            tiempo_seg = 90
        if col_t3.button("⏱️ 120 Segundos"):
            tiempo_seg = 120

        if tiempo_seg > 0:
            placeholder = st.empty()
            for i in range(tiempo_seg, -1, -1):
                mins, secs = divmod(i, 60)
                placeholder.markdown(f"<h1 style='text-align: center; font-size: 6rem; color: #FFD700;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
                time.sleep(1)
            st.balloons()
            st.success("🔔 ¡TIEMPO CUMPLIDO! Comienza tu siguiente serie.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 3. NUTRICIÓN
    elif opcion == "🥗 Nutrición":
        st.markdown("# 🥗 Control de Nutrición Diaria")
        
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            prot = st.number_input("Proteínas (g)", min_value=0, value=175)
        with col2:
            carbs = st.number_input("Carbohidratos (g)", min_value=0, value=180)
        with col3:
            grasas = st.number_input("Grasas (g)", min_value=0, value=80)

        calorias = (prot * 4) + (carbs * 4) + (grasas * 9)
        st.metric("Total Calorías Diarias", f"{calorias} kcal")

        agua = st.slider("Consumo de Agua (Litros)", 0.0, 5.0, 2.5, step=0.25)

        if st.button("💾 GUARDAR MACROS DE HOY"):
            fecha_actual = str(date.today())
            c.execute("INSERT OR REPLACE INTO registro_nutricion VALUES (?, ?, ?, ?, ?, ?)",
                      (st.session_state['user'], fecha_actual, prot, carbs, grasas, agua))
            conn.commit()
            st.success("✅ ¡Objetivo nutricional guardado con éxito!")
        st.markdown("</div>", unsafe_allow_html=True)

    # 4. SOBRECARGA PROGRESIVA
    elif opcion == "📈 Sobrecarga Progresiva":
        st.markdown("# 📈 Evolución de Fuerza")
        df_progresos = pd.read_sql_query(f"SELECT fecha, ejercicio, peso, reps FROM registro_entrenamiento WHERE user_email='{st.session_state['user']}'", conn)

        if not df_progresos.empty:
            st.markdown("<div class='card-box'>", unsafe_allow_html=True)
            ejercicio_sel = st.selectbox("Selecciona un Ejercicio para ver tu avance:", df_progresos["ejercicio"].unique())
            df_filtrado = df_progresos[df_progresos["ejercicio"] == ejercicio_sel]

            st.line_chart(df_filtrado.set_index("fecha")["peso"])
            st.dataframe(df_filtrado, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Aún no registras datos para generar tus gráficas de sobrecarga progresiva.")
