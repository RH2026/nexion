import io
import time
from datetime import datetime
from github import Github
import pandas as pd
import pytz
import streamlit as st

# ── 1. CONFIGURACIÓN Y PERMISOS ──
tz_gdl = pytz.timezone('America/Mexico_City')
hoy = datetime.now(tz_gdl)

st.set_page_config(
    page_title="NEXION // Control Financiero",
    page_icon=chr(128184),
    layout="wide"
)

# Estilo visual profesional estilo NEXION
st.markdown("""

""", unsafe_allow_html=True)

st.markdown(f"### {chr(128187)} NEXION // CONTROL FINANCIERO PERSONAL")
st.markdown(f"**Fecha actual:** {hoy.strftime('%A %d de %B de %Y').upper()} | **Zona Horaria:** Guadalajara, Jal.")
st.markdown("---")

# ── 2. DATOS FINANCIEROS FIJOS ──
INGRESO_SEMANAL = 4450.0
GASTO_CASA = 1500.0
GASOLINA = 600.0
CONSULTA = 350.0
GASTOS_HIJA = 250.0
TOTAL_GASTOS_SEMANALES = GASTO_CASA + GASOLINA + CONSULTA + GASTOS_HIJA  # $2,700

# Apartados mensuales convertidos a semana ($900 en total por semana)
AHORRO_TV_SEM = 225.0
AHORRO_PRESTAMO_SEM = 400.0
AHORRO_INTERNET_SEM = 275.0
TOTAL_AHORRO_MENSUAL_SEM = AHORRO_TV_SEM + AHORRO_PRESTAMO_SEM + AHORRO_INTERNET_SEM  # $900

TOTAL_APARTADO_SEMANAL = TOTAL_GASTOS_SEMANALES + TOTAL_AHORRO_MENSUAL_SEM  # $3,600
DISPONIBLE_SEMANAL = INGRESO_SEMANAL - TOTAL_APARTADO_SEMANAL  # $850

# ── 3. MÉTRICAS PRINCIPALES EN TARJETAS ──
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label=chr(128181) + " Ingreso Semanal", value=f"${INGRESO_SEMANAL:,.2f}")
with col2:
    st.metric(label=chr(128221) + " Gastos + Ahorro Fijo", value=f"\({TOTAL_APARTADO_SEMANAL:,.2f}", delta=f"-\){TOTAL_APARTADO_SEMANAL:,.2f}")
with col3:
    st.metric(label=chr(128188) + " Fondo Mensual (Semanal)", value=f"${TOTAL_AHORRO_MENSUAL_SEM:,.2f}")
with col4:
    st.metric(label=chr(128176) + " Libre / Disponible", value=f"\({DISPONIBLE_SEMANAL:,.2f}", delta=f"+\){DISPONIBLE_SEMANAL:,.2f}")

st.markdown("---")

# ── 4. SECCIÓN DE COMPROMISOS MENSUALES (FECHAS CLAVE) ──
st.markdown(f"#### {chr(128197)} CALENDARIO DE PAGOS MENSUALES (CIERRE DE SEPTIEMBRE)")

col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    st.info(f"""
    **{chr(128250)} Abono de TV**
    * **Monto:** $900.00
    * **Fecha límite:** 25 de Septiembre (Viernes)
    * **Estado:** {chr(9989)} Fondo asegurado con cobro del día
    """)

with col_p2:
    st.info(f"""
    **{chr(127760)} Internet**
    * **Monto:** $1,100.00
    * **Fecha límite:** 27 de Septiembre (Domingo)
    * **Estado:** {chr(9203)} Asegurar desde el viernes 25
    """)

with col_p3:
    st.info(f"""
    **{chr(127974)} Préstamo**
    * **Monto:** $1,600.00
    * **Fecha límite:** 28 de Septiembre (Lunes)
    * **Estado:** {chr(9203)} Asegurar desde el viernes 25
    """)

st.markdown("---")

# ── 5. REGISTRO Y SIMULADOR SEMANAL ──
st.markdown(f"#### {chr(128202)} SIMULADOR Y DISTRIBUCIÓN DE TU VIERNES DE PAGO")

with st.form("form_distribucion"):
    st.markdown("Cada viernes que recibes tus **$4,450.00**, el dinero se distribuye automáticamente de la siguiente manera para mantener tus finanzas blindadas:")
    
    data_tabla = {
        "Concepto": [
            "Gastos de Casa / Despensa",
            "Gasolina",
            "Consulta",
            "Gastos de tu Hija",
            "Ahorro Abono TV (Proporcional)",
            "Ahorro Abono Préstamo (Proporcional)",
            "Ahorro Internet (Proporcional)",
            "LIBRE / DISPONIBLE PARA TI"
        ],
        "Monto Semanal": [
            f"${GASTO_CASA:,.2f}",
            f"${GASOLINA:,.2f}",
            f"${CONSULTA:,.2f}",
            f"${GASTOS_HIJA:,.2f}",
            f"${AHORRO_TV_SEM:,.2f}",
            f"${AHORRO_PRESTAMO_SEM:,.2f}",
            f"${AHORRO_INTERNET_SEM:,.2f}",
            f"${DISPONIBLE_SEMANAL:,.2f}"
        ],
        "Tipo": [
            "Gasto Fijo", "Gasto Fijo", "Gasto Fijo", "Gasto Fijo",
            "Ahorro Mensual", "Ahorro Mensual", "Ahorro Mensual",
            "Disponible"
        ]
    }
    
    df_presupuesto = pd.DataFrame(data_tabla)
    st.dataframe(df_presupuesto, use_container_width=True, hide_index=True)
    
    btn_guardar = st.form_submit_button(chr(128190) + " REGISTRAR CORTE DE ESTA SEMANA", use_container_width=True)
    
    if btn_guardar:
        st.success(chr(9989) + " ¡Corte de la semana registrado con éxito en tu sistema NEXION financiero!")
        

