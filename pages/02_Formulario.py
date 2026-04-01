import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import os

# ══════════════════════════════════════════════════════════════
#  CONFIGURACIÓN Y RUTAS
# ══════════════════════════════════════════════════════════════
SECTORES = ["Corte", "Corte Laminado", "Canteado", "Perforación", "DVH", "Laminado", "Templado"]

# Buscamos la DB en la raíz (un nivel arriba de /pages)
BASE_DIR = Path(__file__).parent.parent 
DB_PATH = BASE_DIR / "produccion.db"

st.set_page_config(page_title="Carga de Producción - Centurion", layout="centered")

# Estilos para el Check Verde y la interfaz
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; font-size: 18px; }
    .dup-box {
        padding: 15px;
        background-color: #441111;
        border: 1px solid #ff4b4b;
        border-radius: 10px;
        color: #ff8a8a;
        text-align: center;
        margin-bottom: 15px;
    }
    .success-panel {
        padding: 25px;
        background-color: #002b1b;
        border: 2px solid #28a745;
        border-radius: 15px;
        color: #d4edda;
        text-align: center;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  LOGICA DE BASE DE DATOS
# ══════════════════════════════════════════════════════════════

def es_duplicado(orden, sector):
    if not orden.strip(): return False
    try:
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT 1 FROM registros WHERE TRIM(orden) = ? AND sector = ? LIMIT 1"
        res = pd.read_sql_query(query, conn, params=(str(orden).strip(), sector))
        conn.close()
        return not res.empty
    except:
        return False

def guardar_registro(orden, carro, lado, usuario, sector):
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

if 'ultimo' not in st.session_state:
    st.session_state.ultimo = None

with st.sidebar:
    if st.button("🏠 Volver al Inicio"):
        st.switch_page("main.py")
    st.divider()
    st.write("Configuración de carga local activa.")

st.title("📋 Carga de Producción")

# --- FORMULARIO REORDENADO ---
with st.container():
    # 1. OPERARIO AL PRINCIPIO
    operario = st.text_input("👷 Operario / Usuario", placeholder="Escribí tu nombre o escaneá tu ID")
    
    st.divider()
    
    # 2. SECTOR Y DATOS DE ORDEN
    sector_sel = st.selectbox("📍 Sector de Trabajo", SECTORES)
    
    col_ord, col_car, col_lad = st.columns([2, 1, 1])
    with col_ord:
        orden = st.text_input("🔢 Orden (Escáner)", key="input_orden")
    with col_car:
        carro = st.number_input("🛒 Carro", min_value=1, value=1)
    with col_lad:
        lado = st.selectbox("↔️ Lado", ["A", "B", "C", "D"])

    st.write("") # Espacio visual

    # --- LÓGICA DE AVISOS Y BOTÓN ---
    ya_existe = es_duplicado(orden, sector_sel)
    
    # Solo mostramos advertencia si no es la orden que acabamos de registrar
    if orden.strip() and ya_existe:
        if st.session_state.ultimo is None or st.session_state.ultimo['orden'] != orden.strip():
            st.markdown(f'<div class="dup-box">⚠️ La orden {orden} ya existe en {sector_sel}</div>', unsafe_allow_html=True)

    if st.button("💾 REGISTRAR AHORA", type="primary"):
        if not operario.strip() or not orden.strip():
            st.error("❌ ERROR: Tenés que poner tu nombre y el número de orden.")
        else:
            success, error = guardar_registro(orden, carro, lado, operario, sector_sel)
            if success:
                st.session_state.ultimo = {"orden": orden.strip(), "sector": sector_sel, "op": operario}
                st.rerun() # Refrescamos para mostrar el cartel de éxito
            else:
                st.error(f"Falla en base de datos: {error}")

# --- CARTEL DE ÉXITO (EL CHECK VERDE) ---
if st.session_state.ultimo:
    st.markdown(f'''
        <div class="success-panel">
            <div style="font-size: 50px;">✅</div>
            <div style="font-size: 22px; font-weight: bold;">¡REGISTRO EXITOSO!</div>
            <div style="font-size: 16px; margin-top: 10px; opacity: 0.9;">
                Orden: <b>{st.session_state.ultimo['orden']}</b><br>
                Sector: {st.session_state.ultimo['sector']}<br>
                Cargado por: {st.session_state.ultimo['op']}
            </div>
        </div>
    ''', unsafe_allow_html=True)
