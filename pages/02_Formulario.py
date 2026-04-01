import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import os

# ══════════════════════════════════════════════════════════════
#  CONFIGURACIÓN Y RUTAS (CORREGIDO PARA /PAGES)
# ══════════════════════════════════════════════════════════════
SECTORES = ["Corte", "Corte Laminado", "Canteado", "Perforación", "DVH", "Laminado", "Templado"]

# Subimos un nivel para encontrar la DB en la raíz del proyecto
BASE_DIR = Path(__file__).parent.parent 
DB_PATH = BASE_DIR / "produccion.db"

st.set_page_config(page_title="Carga de Producción - Centurion", layout="centered")

# Estilos visuales para los carteles
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .dup-box {
        padding: 15px;
        background-color: #441111;
        border: 1px solid #ff4b4b;
        border-radius: 10px;
        color: #ff8a8a;
        text-align: center;
        margin-bottom: 15px;
    }
    .success-box {
        padding: 15px;
        background-color: #114411;
        border: 1px solid #28a745;
        border-radius: 10px;
        color: #98ff98;
        text-align: center;
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  LOGICA DE BASE DE DATOS
# ══════════════════════════════════════════════════════════════

def es_duplicado(orden, sector):
    """Chequea si la orden ya existe en ese sector específico"""
    if not orden.strip(): return False
    try:
        conn = sqlite3.connect(DB_PATH)
        # Limpiamos espacios para que la comparación sea exacta
        query = "SELECT 1 FROM registros WHERE TRIM(orden) = ? AND sector = ? LIMIT 1"
        res = pd.read_sql_query(query, conn, params=(str(orden).strip(), sector))
        conn.close()
        return not res.empty
    except:
        return False

def guardar_registro(orden, carro, lado, usuario, sector):
    """Guarda el nuevo registro en SQLite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO registros (fecha_hora, orden, carro, lado, usuario, sector)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (fecha_hora, str(orden).strip(), carro, lado, usuario.strip(), sector))
        
        conn.commit()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

# ══════════════════════════════════════════════════════════════
#  INTERFAZ DE USUARIO
# ══════════════════════════════════════════════════════════════

# Inicializar estados de sesión
if 'ultimo' not in st.session_state:
    st.session_state.ultimo = None

with st.sidebar:
    if st.button("🏠 Volver al Inicio"):
        st.switch_page("main.py")
    st.divider()
    st.info("Escaneá el código de barras Centurion o cargá manualmente.")

st.title("📋 Carga de Producción")

# --- FORMULARIO ---
with st.container():
    sector_sel = st.selectbox("📍 Sector", SECTORES)
    
    col_ord, col_car, col_lad = st.columns([2, 1, 1])
    with col_ord:
        orden = st.text_input("🔢 Orden (Escáner)", key="input_orden")
    with col_car:
        carro = st.number_input("🛒 Carro", min_value=1, value=1, step=1)
    with col_lad:
        lado = st.selectbox("↔️ Lado", ["A", "B", "C", "D"])

    operario = st.text_input("👷 Operario / Usuario", placeholder="Tu nombre")

    st.divider()

    # --- LÓGICA DE AVISOS Y CARGA ---
    ya_existe = es_duplicado(orden, sector_sel)
    
    # Solo mostrar cartel de duplicado si la orden no es la que acabamos de cargar ahora
    if orden.strip() and ya_existe:
        if st.session_state.ultimo is None or st.session_state.ultimo['orden'] != orden.strip():
            st.markdown(f'<div class="dup-box">⚠️ La orden {orden} ya existe en {sector_sel}</div>', unsafe_allow_html=True)

    if st.button("✅ CARGAR REGISTRO", type="primary"):
        if not operario.strip() or not orden.strip():
            st.error("❌ Falta completar Orden u Operario.")
        else:
            success, error = guardar_registro(orden, carro, lado, operario, sector_sel)
            if success:
                # Guardamos en sesión para que el cartel rojo no moleste
                st.session_state.ultimo = {"orden": orden.strip(), "sector": sector_sel}
                st.balloons()
            else:
                st.error(f"Error al guardar: {error}")

# --- MOSTRAR ÚLTIMO REGISTRO EXITOSO ---
if st.session_state.ultimo:
    st.markdown(f'''
        <div class="success-box">
            ✅ REGISTRADO: {st.session_state.ultimo['orden']} ({st.session_state.ultimo['sector']})
        </div>
    ''', unsafe_allow_html=True)
