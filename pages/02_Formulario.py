
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import sqlite3
from datetime import datetime
from pathlib import Path

# ══════════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════
SECTORES = ["Corte", "Corte Laminado", "Canteado", "Perforación", "DVH", "Laminado", "Templado"]
BASE_DIR = Path(__file__).parent.parent  # Agregamos .parent para subir un nivel
DB_PATH = BASE_DIR / "produccion.db"

st.set_page_config(page_title="Carga de Producción", layout="centered")
# Estilos visuales
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    div.stButton > button { width: 100%; height: 64px; font-size: 20px; font-weight: bold; border-radius: 12px; }
    .ok-box { background-color: #1a4a1a; border: 2px solid #2ecc71; padding: 15px; border-radius: 10px; text-align: center; color: #2ecc71; font-weight: bold; }
    .dup-box { background-color: #4a1a1a; border: 2px solid #e74c3c; padding: 15px; border-radius: 10px; text-align: center; color: #e74c3c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def es_duplicado(orden, sector):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT 1 FROM registros WHERE orden = ? AND sector = ? LIMIT 1"
    res = pd.read_sql_query(query, conn, params=(str(orden).strip(), sector))
    conn.close()
    return not res.empty

def guardar_registro(orden, carro, lado, usuario, sector):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO registros (orden, carro, lado, fecha_hora, usuario, sector)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (str(orden).strip(), int(carro), lado, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(usuario).strip(), sector))
        conn.commit()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

# Manejo de scanner vía URL
params = st.query_params
orden_desde_qr = params.get("orden", "")
if 'orden_valor' not in st.session_state: st.session_state.orden_valor = ""
if 'ultimo' not in st.session_state: st.session_state.ultimo = None

if orden_desde_qr:
    st.session_state.orden_valor = orden_desde_qr
    st.query_params.clear()

st.title("📋 Carga de Producción")
operario = st.text_input("👤 Tu nombre", placeholder="Ej: Daniel")
sector_sel = st.selectbox("🏭 Sector", SECTORES)

st.divider()
# Aquí puedes reinsertar tu bloque SCANNER_HTML si lo deseas

orden = st.text_input("🔢 N° de Orden", value=st.session_state.orden_valor)
col1, col2 = st.columns(2)
with col1: carro = st.number_input("🚗 Carro", 1, 300, 1)
with col2: lado = st.selectbox("↔️ Lado", ["A", "B"])

if orden.strip() and es_duplicado(orden, sector_sel):
    st.markdown(f'<div class="dup-box">⚠️ La orden {orden} ya existe en {sector_sel}</div>', unsafe_allow_html=True)

if st.button("✅ CARGAR REGISTRO", type="primary"):
    if not operario.strip() or not orden.strip():
        st.error("Faltan datos obligatorios.")
    else:
        dup = es_duplicado(orden, sector_sel)
        ok, err = guardar_registro(orden, carro, lado, operario, sector_sel)
        if ok:
            st.session_state.ultimo = {"orden": orden, "sector": sector_sel, "dup": dup}
            st.session_state.orden_valor = ""
            st.rerun()
        else: st.error(err)

if st.session_state.ultimo:
    u = st.session_state.ultimo
    clase = "dup-box" if u["dup"] else "ok-box"
    st.markdown(f'<div class="{clase}">REGISTRADO: {u["orden"]} ({u["sector"]})</div>', unsafe_allow_html=True)
