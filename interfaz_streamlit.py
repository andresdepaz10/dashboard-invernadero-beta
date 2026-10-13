import streamlit as st
import pandas as pd
import time
import urllib.request
import io
import plotly.graph_objects as go
import datetime

st.set_page_config(page_title="Monitoreo Invernadero", layout="wide")
st.title("Invernadero inteligente - Panel de monitoreo")
SHEET_URL = "https://docs.google.com/spreadsheets/d/1E-Md23GAPTStTRUPnVyDADuJuMf7v3AcwKfDUCnLats/export?format=csv"

#-------------------------------------------------------------
@st.cache_data(ttl=10) 
def cargar_datos():
    try:
        req = urllib.request.Request(SHEET_URL, headers={'User-Agent': 'Mozilla/5.0'})
        import ssl
        contexto = ssl._create_unverified_context() 
        with urllib.request.urlopen(req, context=contexto) as response:
            datos_csv = response.read().decode('utf-8') 
        df = pd.read_csv(io.StringIO(datos_csv))
        return df
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return pd.DataFrame()      
df = cargar_datos()
#-------------------------------------------------------------

if not df.empty:
    ultima_medicion = df.iloc[-1]
    
    df['fecha_hora'] = df['fecha'] + ' ' + df['hora']
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'], format='%d/%m/%Y %H:%M:%S', dayfirst=True)
    df = df.set_index('fecha_hora')

    # --- crear velocimetros
    def crear_velocimetro(valor, titulo, sufijo, rango_min, rango_max, opt_min, opt_max):
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = valor,
            title = {'text': titulo, 'font': {'size': 18}},
            number = {'suffix': sufijo, 'font': {'size': 24}},
            gauge = {
                'axis': {'range': [rango_min, rango_max], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "rgba(0,0,0,0)"}, # Ocultamos la barra sólida para usar solo el puntero
                'steps': [
                    {'range': [rango_min, opt_min], 'color': "rgba(255, 99, 71, 0.6)"},  # Peligro (Bajo) - Rojo
                    {'range': [opt_min, opt_max], 'color': "rgba(144, 238, 144, 0.6)"}, # Óptimo - Verde
                    {'range': [opt_max, rango_max], 'color': "rgba(255, 99, 71, 0.6)"}   # Peligro (Alto) - Rojo
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 6},
                    'thickness': 0.8,
                    'value': valor
                }
            }
        ))
        fig.update_layout(margin=dict(l=15, r=15, t=40, b=15), height=200, paper_bgcolor="rgba(0,0,0,0)")
        return fig
    
    # =========================================================
    # 1. SISTEMA DE ALERTAS VISUALES COMPLETO
    # =========================================================
    temp_actual = ultima_medicion['temperatura_ambiente']
    hum_actual = ultima_medicion['humedad_ambiente']
    vpd_actual = ultima_medicion['vpd']
    suelo_actual = ultima_medicion['humedad_suelo1']

    alertas = 0 # Contador para saber si todo está bien

    if temp_actual < 18 or temp_actual > 28:
        st.warning(f"🌡️ ALERTA TEMPERATURA: {temp_actual}°C fuera del rango óptimo (18-28°C).")
        alertas += 1
        
    if hum_actual < 50 or hum_actual > 70:
        st.warning(f"💧 ALERTA HUMEDAD: {hum_actual}% fuera del rango óptimo (50-70%).")
        alertas += 1

    if suelo_actual <= 10:
        st.error(f"🚨 ALERTA SUELO: {suelo_actual}%. Riesgo de deshidratación extrema.")
        alertas += 1
    elif suelo_actual > 80:
        st.warning(f"💦 ALERTA SUELO: {suelo_actual}%. Suelo demasiado húmedo, riesgo de asfixia radicular.")
        alertas += 1
    
    if vpd_actual < 0.6 or vpd_actual > 1.2:
        st.warning(f"⚠️ ALERTA VPD: {vpd_actual} kPa fuera de la zona de confort transpiratorio.")
        alertas += 1

    if alertas == 0:
        st.toast('✅ Todos los parámetros críticos están en rangos óptimos', icon='🌱')


    # =========================================================
    # 2. BARRA LATERAL (SIDEBAR) - FILTRO OPTIMIZADO (Últimos 3 días)
    # =========================================================
    st.sidebar.header("Filtros de historial")
    st.sidebar.write("Ajusta el rango de fechas. (Por defecto: últimos 3 días).")

    min_date = df.index.min().date()
    max_date = df.index.max().date()
    
    # Calculamos la fecha de hace 3 días para que sea el valor por defecto
    default_start = max_date - datetime.timedelta(days=3)
    if default_start < min_date:
        default_start = min_date # Evita errores si hay menos de 3 días de datos

    fechas_seleccionadas = st.sidebar.date_input(
        "Selecciona el rango de fechas:",
        value=(default_start, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if len(fechas_seleccionadas) == 2:
        start_date, end_date = fechas_seleccionadas
        mask = (df.index.date >= start_date) & (df.index.date <= end_date)
        df_filtrado = df.loc[mask]
    else:
        df_filtrado = df

    # =========================================================
    # 3. ESTADO ACTUAL (Velocímetros y Tarjetas)
    # =========================================================
    with st.container(border=True):
        st.subheader("🌱 Variables Biológicas Críticas")
        
        col1, col2 = st.columns(2)
        with col1:
            fig_temp = crear_velocimetro(ultima_medicion['temperatura_ambiente'], "Temperatura", " °C", 0, 45, 18, 28)
            st.plotly_chart(fig_temp, use_container_width=True)
        with col2:
            fig_hum = crear_velocimetro(ultima_medicion['humedad_ambiente'], "Humedad", " %", 0, 100, 50, 70)
            st.plotly_chart(fig_hum, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            fig_vpd = crear_velocimetro(ultima_medicion['vpd'], "VPD", " kPa", 0, 3, 0.6, 1.2)
            st.plotly_chart(fig_vpd, use_container_width=True)
        with col4:
            fig_suelo = crear_velocimetro(ultima_medicion['humedad_suelo1'], "Humedad Suelo", " %", 0, 100, 40, 80)
            st.plotly_chart(fig_suelo, use_container_width=True)

    with st.container(border=True):
        st.subheader("📊 Parámetros Físicos y de Referencia")
        col_ref1, col_ref2, col_ref3 = st.columns(3)
        try:
            with col_ref1:
                st.metric("Intensidad Lumínica", f"{ultima_medicion['luxes1']:.1f} lx")
            with col_ref2:
                st.metric("Presión Barométrica", f"{ultima_medicion['presion_ambiente']:.1f} hPa")
            with col_ref3:
                st.metric("Altitud Relativa", f"{ultima_medicion['altitud']:.1f} msnm")
        except KeyError as e:
            st.warning(f"Asegúrate de que la columna {e} exista en tu Google Sheet.")
    
    # =========================================================
    # 4. TENDENCIAS HISTÓRICAS (USANDO DF_FILTRADO)
    # =========================================================
    with st.container(border=True):
        #--------------- parametros de monitoreo
        st.subheader("📈 Historial de Variables Biológicas Críticas")
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.write("Evolución de la Temperatura Ambiente (°C)")
            st.line_chart(df_filtrado['temperatura_ambiente'])
        with col_graf2:
            st.write("Evolución de la Humedad Ambiente (%)")
            st.line_chart(df_filtrado['humedad_ambiente'])

        col_graf3, col_graf4 = st.columns(2)
        with col_graf3:
            st.write("Evolución del VPD (kPa)")
            st.line_chart(df_filtrado['vpd'])
        with col_graf4:
            st.write("Evolución de la Humedad del Suelo (%)")
            st.line_chart(df_filtrado['humedad_suelo1'])

    with st.container(border=True):
        #--------------- parametros de referencia
        st.subheader("📉 Historial de Parámetros Físicos y de Referencia")
        col_ref_graf1, col_ref_graf2 = st.columns(2)
        with col_ref_graf1:
            st.write("Intensidad Lumínica (luxes)")
            st.line_chart(df_filtrado['luxes1'])
        with col_ref_graf2:
            st.write("Presión Barométrica (hPa)")
            st.line_chart(df_filtrado['presion_ambiente'])

        col_ref_graf3, col_ref_graf4 = st.columns(2)
        with col_ref_graf3:
            st.write("Altitud Relativa (msnm)")
            st.line_chart(df_filtrado['altitud'])
        with col_ref_graf4:
            st.write("Temperatura Interna del Sensor BMP (°C)")
            st.line_chart(df_filtrado['temperatura_bmp'])


    # =========================================================
    # 5. TABLA Y BOTÓN DE EXTRACCIÓN DE DATOS
    # =========================================================
    with st.container(border=True):
        with st.expander("Ver y Descargar Registro de Datos (Tabla)"):
            st.dataframe(df_filtrado)
            
            # Lógica para generar el archivo CSV descargable
            csv = df_filtrado.to_csv().encode('utf-8')
            st.download_button(
                label="Descargar datos filtrados como CSV",
                data=csv,
                file_name='datos_invernadero_orquideas.csv',
                mime='text/csv',
                type='primary'
            )

# --- FIN DEL BLOQUE 'IF NOT DF.EMPTY' ---
else:
    st.info("Esperando datos del Google Sheet...")

# --- MODO DE MONITOREO EN VIVO (Auto-Refresh) ---
st.sidebar.divider()
auto_refresh = st.sidebar.checkbox("🔄 Activar Monitoreo en Vivo (10s)")

if auto_refresh:
    # Espera 10 segundos sin hacer nada
    time.sleep(10)
    # Limpia la caché y recarga toda la página automáticamente
    st.cache_data.clear()
    st.rerun()
