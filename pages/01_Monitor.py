import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime
from pathlib import Path
import os

# ══════════════════════════════════════════════════════════════
#  CONFIGURACIÓN Y RUTAS (CORREGIDO PARA /PAGES)
# ══════════════════════════════════════════════════════════════
SECTORES = ["Corte", "Corte Laminado", "Canteado", "Perforación", "DVH", "Laminado", "Templado"]

# Subimos un nivel (.parent.parent) porque este archivo está en /pages
BASE_DIR = Path(__file__).parent.parent 
DB_PATH = BASE_DIR / "produccion.db"

st.set_page_config(page_title="Monitor de Producción PRO", layout="wide")

# ─── CONTROL DE LICENCIA (EXTENDIDO) ───
FECHA_LIMITE = datetime(2030, 12, 31) 
if datetime.now() > FECHA_LIMITE:
    st.error("### ⚠️ SISTEMA BLOQUEADO — Licencia vencida")
    st.info("Contacto Soporte: Daniel De Lera")
    st.stop()

# ══════════════════════════════════════════════════════════════
#  FUNCIONES DE BASE DE DATOS
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=10)
def cargar_datos(sector_nombre):
    try:
        if not DB_PATH.exists():
            return None, f"No se encuentra la base de datos en: {DB_PATH}"
            
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT * FROM registros WHERE sector = ? ORDER BY fecha_hora DESC"
        df = pd.read_sql_query(query, conn, params=(sector_nombre,))
        conn.close()
        
        if not df.empty:
            df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
        return df, None
    except Exception as e:
        return None, str(e)

def marcar_duplicados(df):
    if df.empty: return df
    # El nombre de la columna en la DB es 'orden' (minúscula)
    dups = df['orden'].duplicated(keep=False)
    def estilo_fila(row):
        return ['background-color: #5c1010; color: white;' if dups.iloc[row.name] else '' for _ in row]
    return df.style.apply(estilo_fila, axis=1)

# ══════════════════════════════════════════════════════════════
#  SIDEBAR Y NAVEGACIÓN
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("⚙️ Administración")
    if st.button("🏠 Volver al Inicio", use_container_width=True):
        st.switch_page("main.py")
    st.divider()
    if st.button("🔄 Refrescar Datos", type="primary"):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Base de datos: {DB_PATH.name}")

# ══════════════════════════════════════════════════════════════
#  RENDER DEL DASHBOARD
# ══════════════════════════════════════════════════════════════
st.title("🚀 Monitor de Producción Industrial")

tabs = st.tabs(SECTORES)

for tab, s_nombre in zip(tabs, SECTORES):
    with tab:
        df, err = cargar_datos(s_nombre)
        
        if err:
            st.error(f"❌ Error: {err}")
            continue
        
        if df is None or df.empty:
            st.info(f"📭 Sin registros para el sector: {s_nombre}")
            continue

        # --- MÉTRICAS ---
        hoy = datetime.now().date()
        df_hoy = df[df['fecha_hora'].dt.date == hoy]
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Total Hoy", len(df_hoy))
        with col_m2:
            st.metric("Histórico", len(df))
        with col_m3:
            st.metric("Operarios Hoy", df_hoy['usuario'].nunique() if not df_hoy.empty else 0)

        st.divider()

        # --- GRÁFICO Y TABLA ---
        col_izq, col_der = st.columns([1, 2])

        with col_izq:
            st.subheader("📊 Ranking Operarios")
            if not df_hoy.empty:
                conteo = df_hoy['usuario'].value_counts().reset_index()
                conteo.columns = ['Operario', 'Carros']
                fig = px.bar(conteo, x='Operario', y='Carros', color='Carros', 
                             text_auto=True, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True, key=f"grafico_{s_nombre}")
            else:
                st.info("No hay actividad hoy para graficar.")

        with col_der:
            st.subheader("📝 Últimos Registros")
            # Mostramos los últimos 50 registros resaltando duplicados
            st.dataframe(marcar_duplicados(df.head(50).reset_index(drop=True)), 
                         use_container_width=True, hide_index=True)

st.divider()
st.caption("Sistema de Monitoreo — Planta Centurion")
