import streamlit as st
import pandas as pd
import time
import urllib.request
import io
import plotly.graph_objects as go
import datetime
import json

#------------------------------------------------------------- CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Monitoreo invernadero", 
    page_icon="🌱",
    layout="wide"
)

#------------------------------------------------------------- ESTILOS CSS PERSONALIZADOS
st.markdown("""
<style>
    /* 1. Fondo general de la página */
    .stApp {
        background-color: #EEF5EE !important;
        color: #111111 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* 2. Textos y encabezados en negro nítido */
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #111111 !important;
    }
    h1, h2, h3 {
        font-weight: 700 !important;
    }

    /* 3. Barra lateral (Sidebar) */
    section[data-testid="stSidebar"] {
        background-color: #BDD4C1 !important;
        border-right: 1px solid #7AA688 !important;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label {
        color: #111111 !important;
    }

    /* 4. Selector de fechas e inputs de la barra lateral */
    section[data-testid="stSidebar"] div[data-baseweb="input"],
    section[data-testid="stSidebar"] div[data-baseweb="base-input"] {
        background-color: #FFFFFF !important;
        border: 1px solid #7AA688 !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] input {
        color: #111111 !important;
        background-color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* 5. Fondo de las cajas en #7AA688 (Velocímetros, mapa, clima y gráficas) */
        div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stVerticalBlockBorderWrapper"] > div,
        div[data-testid="stVerticalBlockBorderWrapper"] > div:first-child {
        background-color: #7AA688 !important;   /* Fondo verde #7AA688 forzado */
        border: 1px solid #5C8769 !important;    /*Borde exterior a tono */
        border-radius: 14px !important;
        padding: 12px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06) !important;
    }

    /* 6. Tarjetas de métricas (st.metric) */
        div[data-testid="stMetric"] {
            background-color: #CFE1D2 !important;
            border: 1px solid #5C8769 !important;
            border-radius: 12px !important;
            padding: 14px 18px !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05) !important;
        }

        /* Selector universal: fuerza 20px a TODOS los elementos internos de la etiqueta */
        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] * {
            font-size: 23px !important;
            font-weight: 800 !important;
            color: #111111 !important;
            line-height: 1.3 !important;
        }

        /* Valor numérico principal */
        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] * {
            color: #111111 !important;
            font-weight: 400 !important;
            font-size: 26px !important; /* Ajusta aquí el tamaño (ej. 22px, 24px, 26px) */
            line-height: 1.2 !important;
        }

    /* 7. Botones de acción */
    .stButton > button {
        background-color: #21593F !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 8px 18px !important;
        transition: all 0.2s ease-in-out;
    }
    .stButton > button p, .stButton > button span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    .stButton > button:hover {
        background-color: #16402C !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }

    /* 8. Alertas del sistema */
    div[data-testid="stAlert"] {
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("Invernadero inteligente - panel de monitoreo")
SHEET_URL = "https://docs.google.com/spreadsheets/d/1E-Md23GAPTStTRUPnVyDADuJuMf7v3AcwKfDUCnLats/export?format=csv"

#------------------------------------------------------------- FUNCIÓN CARGAR DATOS
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

#------------------------------------------------------------- PROCESAMIENTO FECHA Y HORA
if not df.empty:
    ultima_medicion = df.iloc[-1]
    if len(df) > 1:
        medicion_previa = df.iloc[-2]
    else:
        medicion_previa = ultima_medicion
        
    df['fecha_hora'] = df['fecha'] + ' ' + df['hora']
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'], format='%d/%m/%Y %H:%M:%S', dayfirst=True)
    df = df.set_index('fecha_hora')

    #--------------------------------------------------------- VELOCÍMETROS
    def crear_velocimetro(valor, valor_previo, titulo, sufijo, rango_min, rango_max, opt_min, opt_max):
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = valor,
                domain = {'x': [0, 1], 'y': [0, 1]},
                
                # 1. TÍTULO: Único elemento en negrita usando <b>
                title = {
                    'text': f"<b>{titulo}</b>", 
                    'font': {'size': 24, 'color': "#111111"}
                },
                
                # 2. Número central y unidad (en peso normal)
                number = {
                    'suffix': sufijo, 
                    'font': {'size': 28, 'color': "#111111"}
                },
                
                # 3. Delta inferior (en peso normal)
                delta = {
                    'reference': valor_previo,
                    'position': "bottom",
                    'valueformat': ".1f",
                    'font': {'size': 15, 'color': "#111111"}
                },
                
                gauge = {
                    'axis': {
                        'range': [rango_min, rango_max], 
                        'tickwidth': 2.5, 
                        'tickcolor': "#111111", 
                        'ticklen': 8,
                        'dtick': (rango_max - rango_min) / 5, 
                        # 4. Escala numérica del arco (en peso normal)
                        'tickfont': {'color': "#111111", 'size': 12}
                    },
                    'bar': {'color': "rgba(0,0,0,0)"}, 
                    'bgcolor': "rgba(255, 255, 255, 0.15)",
                    'borderwidth': 0,
                    'steps': [
                        {'range': [rango_min, opt_min], 'color': "#D90429", 'thickness': 0.75},
                        {'range': [opt_min, opt_max], 'color': "#237D07", 'thickness': 0.75},
                        {'range': [opt_max, rango_max], 'color': "#D90429", 'thickness': 0.75}
                    ],
                    'threshold': {
                        'line': {'color': "#FFFFFF", 'width': 5}, 
                        'thickness': 0.85, 
                        'value': valor
                    }
                }
            ))
            
            fig.update_layout(
                margin=dict(l=20, r=20, t=50, b=20), 
                height=280, 
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={'color': "#111111"}  # <-- Se eliminó 'weight': 'bold' de aquí
            )
            return fig
    
    #--------------------------------------------------------- GRÁFICAS ESTÁTICAS CON FONDO #7AA688
    def crear_grafica_estatica(fechas, valores, color_linea):
        fig = go.Figure(go.Scatter(
            x=fechas, 
            y=valores, 
            mode='lines', 
            line=dict(color=color_linea, width=2.5)
        ))
        fig.update_layout(
            margin=dict(l=15, r=15, t=15, b=15),
            height=230,
            xaxis=dict(
                fixedrange=True,
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.3)",
                linecolor="#5C8769",
                tickfont=dict(color="#111111", size=10)
            ), 
            yaxis=dict(
                fixedrange=True,
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.3)",
                linecolor="#5C8769",
                tickfont=dict(color="#111111", size=10)
            ), 
            hovermode="x unified",       
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#CFE1D2",   # Fondo exacto de la gráfica en 7AA688
            font=dict(color="#111111")
        )
        return fig

    # =========================================================
    # 1. SISTEMA DE ALERTAS VISUALES
    # =========================================================
    temp_actual = ultima_medicion['temperatura_ambiente']
    hum_actual = ultima_medicion['humedad_ambiente']
    vpd_actual = ultima_medicion.get('vpd', 0.0)
    suelo_actual = ultima_medicion['humedad_suelo1']

    alertas = 0 

    if temp_actual < 18 or temp_actual > 28:
        st.warning(f"🌡️ ALERTA TEMPERATURA: {temp_actual:.1f} °C fuera del rango óptimo (18-28 °C).")
        alertas += 1
        
    if hum_actual < 50 or hum_actual > 70:
        st.warning(f"💧 ALERTA HUMEDAD: {hum_actual:.1f} % fuera del rango óptimo (50-70 %).")
        alertas += 1

    if suelo_actual <= 10:
        st.error(f"🚨 ALERTA SUELO: {suelo_actual} %. Riesgo de deshidratación extrema del sustrato.")
        alertas += 1
    elif suelo_actual > 80:
        st.warning(f"💦 ALERTA SUELO: {suelo_actual} %. Suelo sobresaturado, riesgo de asfixia radicular.")
        alertas += 1
    
    if vpd_actual < 0.6 or vpd_actual > 1.2:
        st.warning(f"⚠️ ALERTA VPD: {vpd_actual:.3f} kPa fuera de la zona de confort transpiratorio.")
        alertas += 1

    if alertas == 0:
        st.toast('Todos los parámetros críticos están en rangos óptimos', icon='🌱')

    # =========================================================
    # 2. BARRA LATERAL (SIDEBAR) - FILTROS Y CONTROL
    # =========================================================
    st.sidebar.header("🔍 Filtros de Historial")
    st.sidebar.write("Ajusta el rango de fechas a consultar:")

    min_date = df.index.min().date()
    max_date = df.index.max().date()
    
    default_start = max_date - datetime.timedelta(days=3)
    if default_start < min_date:
        default_start = min_date 

    fechas_seleccionadas = st.sidebar.date_input(
        "Rango de fechas:",
        value=(default_start, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(fechas_seleccionadas, (tuple, list)) and len(fechas_seleccionadas) == 2:
        start_date, end_date = fechas_seleccionadas
        mask = (df.index.date >= start_date) & (df.index.date <= end_date)
        df_filtrado = df.loc[mask]
    else:
        df_filtrado = df

    # Control de Actuadores
    st.sidebar.divider()
    st.sidebar.subheader("🎛️ Control de Actuadores")
    estado_led = st.sidebar.toggle("💡 Iluminación / Actuador")

    if st.sidebar.button("Aplicar Cambio"):
        comando = "LED_ON" if estado_led else "LED_OFF"
        script_id = "AKfycbyUjFPT-FgeMGwf-IsJKb8z0tPYiO276FmsW5tywCmZBtrA7Q6zLC43ivGeDGEhhjEY"
        url_control = f"https://script.google.com/macros/s/{script_id}/exec?comando={comando}"
        
        try:
            req = urllib.request.Request(url_control, headers={'User-Agent': 'Mozilla/5.0'})
            import ssl
            contexto = ssl._create_unverified_context()
            with urllib.request.urlopen(req, context=contexto) as response:
                st.sidebar.success(f"Comando '{comando}' enviado correctamente.")
        except Exception as e:
            st.sidebar.error(f"Error al enviar comando: {e}")

    # =========================================================
    # 3. ESTADO ACTUAL (VELOCÍMETROS EN CAJA #7AA688)
    # =========================================================
    with st.container(border=True):
        st.subheader("🌿 Variables Biológicas Críticas")
        
        col1, col2 = st.columns(2)
        with col1:
            fig_temp = crear_velocimetro(ultima_medicion['temperatura_ambiente'], medicion_previa['temperatura_ambiente'], "Temperatura Ambiente", " °C", 0, 45, 18, 28)
            st.plotly_chart(fig_temp, use_container_width=True)
        with col2:
            fig_hum = crear_velocimetro(ultima_medicion['humedad_ambiente'], medicion_previa['humedad_ambiente'], "Humedad Ambiente", " %", 0, 100, 50, 70)
            st.plotly_chart(fig_hum, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            fig_vpd = crear_velocimetro(ultima_medicion.get('vpd', 0.0), medicion_previa.get('vpd', 0.0), "VPD (Déficit de Vapor)", " kPa", 0, 3, 0.6, 1.2)
            st.plotly_chart(fig_vpd, use_container_width=True)
        with col4:
            fig_suelo = crear_velocimetro(ultima_medicion['humedad_suelo1'], medicion_previa['humedad_suelo1'], "Humedad del Suelo", " %", 0, 100, 40, 80)
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
                st.metric("Altitud Barométrica", f"{ultima_medicion['altitud']:.1f} msnm")
        except KeyError as e:
            st.warning(f"Falta columna en Google Sheets: {e}")
            
    # =========================================================
    # 4. UBICACIÓN Y CLIMA EXTERIOR EN CAJA #7AA688
    # =========================================================
    with st.container(border=True):
        st.subheader("📍 Ubicación y Clima Exterior")
        
        LATITUD = 16.758311
        LONGITUD = -93.172347
        
        col_mapa, col_clima = st.columns([1.8, 1])
        
        with col_mapa:
            # Compatibilidad automática para Plotly v6+ (Scattermap) o versiones previas (Scattermapbox)
            if hasattr(go, 'Scattermap'):
                fig_mapa = go.Figure(go.Scattermap(
                    lat=[LATITUD],
                    lon=[LONGITUD],
                    mode='markers',
                    marker=dict(size=18, color="#1ED760"),
                    text=["Invernadero inteligente"]
                ))
                fig_mapa.update_layout(
                    map=dict(
                        style="carto-darkmatter",  # Fondo de mapa negro permanente
                        center=dict(lat=LATITUD, lon=LONGITUD),
                        zoom=13
                    ),
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=400,
                    paper_bgcolor="rgba(0,0,0,0)"
                )
            else:
                fig_mapa = go.Figure(go.Scattermapbox(
                    lat=[LATITUD],
                    lon=[LONGITUD],
                    mode='markers',
                    marker=dict(size=16, color="#1ED760"),
                    text=["Invernadero inteligente"]
                ))
                fig_mapa.update_layout(
                    mapbox=dict(
                        style="carto-darkmatter",
                        center=dict(lat=LATITUD, lon=LONGITUD),
                        zoom=13
                    ),
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=400,
                    paper_bgcolor="rgba(0,0,0,0)"
                )

            st.plotly_chart(fig_mapa, use_container_width=True, config={'displayModeBar': False})
            
        with col_clima:
            st.markdown("**Referencia Exterior (Open-Meteo)**")
            try:
                url_clima = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUD}&longitude={LONGITUD}&current=temperature_2m,relative_humidity_2m"
                req_clima = urllib.request.Request(url_clima, headers={'User-Agent': 'Mozilla/5.0'})
                import ssl
                contexto_ssl = ssl._create_unverified_context()
                
                with urllib.request.urlopen(req_clima, context=contexto_ssl) as response:
                    datos_clima = json.loads(response.read().decode('utf-8'))
                    
                temp_ext = datos_clima['current']['temperature_2m']
                hum_ext = datos_clima['current']['relative_humidity_2m']
                
                dif_temp = temp_actual - temp_ext
                dif_hum = hum_actual - hum_ext
                
                st.metric(
                    label="Temperatura Exterior", 
                    value=f"{temp_ext:.1f} °C", 
                    delta=f"{dif_temp:+.1f} °C vs Interior", 
                    delta_color="inverse"
                )
                
                st.metric(
                    label="Humedad Exterior", 
                    value=f"{hum_ext:.1f} %", 
                    delta=f"{dif_hum:+.1f} % vs Interior"
                )
                
            except Exception:
                st.warning("Conectando con estación meteorológica exterior...")
    
    # =========================================================
    # 5. TENDENCIAS HISTÓRICAS EN CAJAS #7AA688
    # =========================================================
    with st.container(border=True):
        st.subheader("📈 Historial de Variables Biológicas Críticas")
        config_estatica = {'displayModeBar': False}
        
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.markdown("<p style='font-size: 20px; font-weight: ; color: #111111; margin-bottom: 2px;'>Evolución de la Temperatura Ambiente (°C)</p>", unsafe_allow_html=True)
            fig1 = crear_grafica_estatica(df_filtrado.index, df_filtrado['temperatura_ambiente'], "#C0392B") 
            st.plotly_chart(fig1, use_container_width=True, config=config_estatica)

        with col_graf2:
            st.markdown("<p style='font-size: 20px; font-weight: ; color: #111111; margin-bottom: 2px;'>Evolución de la Humedad Ambiente (%)</p>", unsafe_allow_html=True)
            fig2 = crear_grafica_estatica(df_filtrado.index, df_filtrado['humedad_ambiente'], "#0E4D7A") 
            st.plotly_chart(fig2, use_container_width=True, config=config_estatica)

        col_graf3, col_graf4 = st.columns(2)
        with col_graf3:
            st.markdown("<p style='font-size: 20px; font-weight: ; color: #111111; margin-bottom: 2px;'>Evolución del VPD (kPa)</p>", unsafe_allow_html=True)
            fig3 = crear_grafica_estatica(df_filtrado.index, df_filtrado.get('vpd', 0), "#4A154B") 
            st.plotly_chart(fig3, use_container_width=True, config=config_estatica)

        with col_graf4:
            st.markdown("<p style='font-size: 20px; font-weight: ; color: #111111; margin-bottom: 2px;'>Evolución de la Humedad del Suelo (%)</p>", unsafe_allow_html=True)
            fig4 = crear_grafica_estatica(df_filtrado.index, df_filtrado['humedad_suelo1'], "#0B381C") 
            st.plotly_chart(fig4, use_container_width=True, config=config_estatica)    

    with st.container(border=True):
        st.subheader("📉 Historial de Parámetros Físicos y de Referencia")
        config_estatica = {'displayModeBar': False}
        
        col_ref_graf1, col_ref_graf2 = st.columns(2)
        with col_ref_graf1:
            st.markdown("<p style='font-size: 20px; font-weight: ; color: #111111; margin-bottom: 2px;'>Intensidad Lumínica (luxes)</p>", unsafe_allow_html=True)
            fig5 = crear_grafica_estatica(df_filtrado.index, df_filtrado['luxes1'], "#8A6508") 
            st.plotly_chart(fig5, use_container_width=True, config=config_estatica)

        with col_ref_graf2:
            st.markdown("<p style='font-size: 20px; font-weight: ; color: #111111; margin-bottom: 2px;'>Presión Barométrica (hPa)</p>", unsafe_allow_html=True)
            fig6 = crear_grafica_estatica(df_filtrado.index, df_filtrado['presion_ambiente'], "#263238") 
            st.plotly_chart(fig6, use_container_width=True, config=config_estatica)

        col_ref_graf3, col_ref_graf4 = st.columns(2)
        with col_ref_graf3:
            st.markdown("<p style='font-size: 20px; font-weight: ; color: #111111; margin-bottom: 2px;'>Altitud Relativa (msnm)</p>", unsafe_allow_html=True)
            fig7 = crear_grafica_estatica(df_filtrado.index, df_filtrado['altitud'], "#196F3D") 
            st.plotly_chart(fig7, use_container_width=True, config=config_estatica)

        with col_ref_graf4:
            st.markdown("<p style='font-size: 20px; font-weight: ; color: #111111; margin-bottom: 2px;'>Temperatura Interna del Sensor BMP (°C)</p>", unsafe_allow_html=True)
            fig8 = crear_grafica_estatica(df_filtrado.index, df_filtrado['temperatura_bmp'], "#78281F") 
            st.plotly_chart(fig8, use_container_width=True, config=config_estatica)
    # =========================================================
    # 6. TABLA Y DESCARGA DE DATOS
    # =========================================================
    with st.container(border=True):
            st.subheader("Registro histórico de datos")
            
            st.dataframe(df_filtrado, use_container_width=True)
            
            csv = df_filtrado.to_csv().encode('utf-8')
            st.download_button(
                label="Descargar datos filtrados como CSV",
                data=csv,
                file_name='datos_invernadero_orquideas.csv',
                mime='text/csv'
            )
else:
    st.info("Esperando datos del Google Sheet...")

# --- MODO DE MONITOREO EN VIVO (Auto-Refresh) ---
st.sidebar.divider()
auto_refresh = st.sidebar.checkbox("🔄 Activar Monitoreo en Vivo (10s)")
if auto_refresh:
    hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
    st.sidebar.caption(f"Última consulta: {hora_actual}")
    
    with st.spinner('Esperando nuevo ciclo de telemetría...'):
        time.sleep(10)
        st.cache_data.clear()
        st.rerun()
