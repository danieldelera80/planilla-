import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime
from pathlib import Path

# ══════════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════
SECTORES = ["Corte", "Corte Laminado", "Canteado", "Perforación", "DVH", "Laminado", "Templado"]
DB_PATH = Path(__file__).parent / "produccion.db"

st.set_page_config(page_title="Monitor de Producción PRO", layout="wide")

@st.cache_data(ttl=5) # Actualización rápida cada 5 segundos
def cargar_datos(sector_nombre):
    try:
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
    dups = df['orden'].duplicated(keep=False)
    def estilo_fila(row):
        return ['background-color: #5c1010; color: white;' if dups.iloc[row.name] else '' for _ in row]
    return df.style.apply(estilo_fila, axis=1)

st.title("🚀 Monitor de Producción Industrial")

tabs = st.tabs(SECTORES)
for tab, s_nombre in zip(tabs, SECTORES):
    with tab:
        df, err = cargar_datos(s_nombre)
        if err:
            st.error(f"Error en base de datos: {err}")
            continue
        
        if df.empty:
            st.info(f"No hay registros cargados para {s_nombre}.")
            continue

        # Métricas del día
        hoy = datetime.now().date()
        df_hoy = df[df['fecha_hora'].dt.date == hoy]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Hoy", len(df_hoy))
        m2.metric("Total Histórico", len(df))
        m3.metric("Operarios Hoy", df_hoy['usuario'].nunique())

        st.divider()
        col_izq, col_der = st.columns([1, 2])

        with col_izq:
            st.subheader("📊 Actividad por Operario")
            if not df_hoy.empty:
                fig = px.bar(df_hoy['usuario'].value_counts().reset_index(), 
                             x='usuario', y='count', color='count', text_auto=True,
                             template="plotly_dark", labels={'count': 'Carros'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption("Sin datos para graficar hoy.")

        with col_der:
            st.subheader("📝 Últimos Registros")
            st.dataframe(marcar_duplicados(df.head(50).reset_index(drop=True)), use_container_width=True)

st.sidebar.caption(f"Conectado a: {DB_PATH.name}")
if st.sidebar.button("🔄 Forzar Refresco"):
    st.cache_data.clear()
    st.rerun()
