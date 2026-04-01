import streamlit as st

st.set_page_config(page_title="Sistema Central Centurion", layout="centered")

st.title("🏭 Control de Producción")
st.write("Elegí qué querés hacer:")

col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 Ver Monitor (Dashboard)", use_container_width=True):
        st.switch_page("app.py")

with col2:
    if st.button("📋 Cargar Producción (Formulario)", use_container_width=True):
        st.switch_page("formulario.py")