import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime, timezone

# Configuración del Dashboard
st.set_page_config(page_title="Monitoreo Hidro-Climático ZMG", layout="wide")

st.title("⛈️ Sistema de Monitoreo - Zona Metropolitana de Guadalajara")
st.markdown(
    "Visualización en tiempo real: Satélite Infrarrojo (animación tipo SMN), "
    "Radar de lluvia con su alcance real, e Indicadores Climáticos locales."
)

# 1. COORDENADAS DE LA ZMG
zmg_zonas = {
    "Guadalajara (Centro)": {"lat": 20.6767, "lon": -103.3475},
    "Zapopan (Norte/Oeste)": {"lat": 20.7236, "lon": -103.3848},
    "Tlaquepaque / Tonalá": {"lat": 20.6394, "lon": -103.3134},
    "Tlajomulco (Sur)": {"lat": 20.4744, "lon": -103.4449},
}

# Centro y zoom FIJOS que cubren toda la Zona Metropolitana (mapa de radar).
# El selector de municipio NUNCA mueve el mapa: solo cambia los datos meteorológicos.
ZMG_CENTRO = {"lat": 20.6285, "lon": -103.3730}
ZMG_ZOOM = 11
RAINVIEWER_MAX_NATIVE_ZOOM = 7  # RainViewer solo genera tiles reales hasta zoom 7

# Radar Meteorológico Doppler IAM-Universidad de Guadalajara.
# Ubicado en las instalaciones del IAM (Av. Vallarta 2602, Col. Arcos Vallarta, Guadalajara).
# Alcance teórico: 240 km. Por la orografía de Jalisco, el alcance efectivo publicado es ~150 km.
# Coordenadas aproximadas (domicilio del IAM); ajústalas si cuentas con el dato exacto de la antena.
RADAR_UDG = {"lat": 20.6740, "lon": -103.3830}
RADAR_UDG_ALCANCE_KM = 150

# Selector de zona en la barra lateral (afecta SOLO los indicadores de clima, no los mapas)
st.sidebar.header("📍 Datos meteorológicos por sector")
zona_elegida = st.sidebar.selectbox(
    "Selecciona un municipio/sector:", list(zmg_zonas.keys())
)

coords = zmg_zonas[zona_elegida]
lat, lon = coords["lat"], coords["lon"]

# Botón de actualización manual (fuerza refresco inmediato de todas las APIs)
if st.sidebar.button("🔄 Actualizar ahora"):
    st.cache_data.clear()
    st.rerun()


# 2. CLIMA EN TIEMPO REAL (Open-Meteo API) - datos ampliados, según municipio elegido
WMO_CODES = {
    0: ("Despejado", "☀️"),
    1: ("Mayormente despejado", "🌤️"),
    2: ("Parcialmente nublado", "⛅"),
    3: ("Nublado", "☁️"),
    45: ("Niebla", "🌫️"),
    48: ("Niebla escarchada", "🌫️"),
    51: ("Llovizna ligera", "🌦️"),
    53: ("Llovizna moderada", "🌦️"),
    55: ("Llovizna densa", "🌧️"),
    61: ("Lluvia ligera", "🌦️"),
    63: ("Lluvia moderada", "🌧️"),
    65: ("Lluvia fuerte", "🌧️"),
    71: ("Nieve ligera", "🌨️"),
    73: ("Nieve moderada", "🌨️"),
    75: ("Nieve fuerte", "🌨️"),
    80: ("Chubascos ligeros", "🌦️"),
    81: ("Chubascos moderados", "🌧️"),
    82: ("Chubascos violentos", "⛈️"),
    95: ("Tormenta eléctrica", "⛈️"),
    96: ("Tormenta con granizo ligero", "⛈️"),
    99: ("Tormenta con granizo fuerte", "⛈️"),
}


def descr_clima(codigo):
    return WMO_CODES.get(codigo, ("Condición no disponible", "❓"))


@st.cache_data(ttl=600)  # Open-Meteo actualiza aprox. cada 10-15 min
def obtener_clima_zmg(latitude, longitude):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        "&current=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,"
        "weather_code,cloud_cover,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m"
        "&hourly=precipitation_probability"
        "&forecast_days=1&timezone=America/Mexico_City"
    )
    respuesta = requests.get(url, timeout=10)
    respuesta.raise_for_status()
    return respuesta.json()


try:
    datos = obtener_clima_zmg(lat, lon)
    actual = datos["current"]
    temp = actual["temperature_2m"]
    sensacion = actual["apparent_temperature"]
    humedad = actual["relative_humidity_2m"]
    lluvia = actual["precipitation"]
    viento = actual["wind_speed_10m"]
    rafagas = actual["wind_gusts_10m"]
    presion = actual["surface_pressure"]
    nubes = actual["cloud_cover"]
    desc, icono = descr_clima(actual["weather_code"])

    # Probabilidad de lluvia en las próximas 3 horas
    horas = datos["hourly"]["time"]
    prob_lluvia = datos["hourly"]["precipitation_probability"]
    idx = horas.index(actual["time"]) if actual["time"] in horas else 0
    prob_prox_3h = (
        max(prob_lluvia[idx : idx + 3]) if prob_lluvia[idx : idx + 3] else None
    )
except Exception:
    temp = sensacion = humedad = lluvia = viento = rafagas = presion = nubes = "--"
    desc, icono = "Sin datos disponibles", "❓"
    prob_prox_3h = None

st.markdown(f"#### {icono} {desc} — {zona_elegida}")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(
    "🌡️ Temperatura",
    f"{temp} °C",
    f"Sensación {sensacion} °C" if sensacion != "--" else None,
)
col2.metric("💧 Humedad", f"{humedad} %")
col3.metric("🌧️ Lluvia (última hora)", f"{lluvia} mm")
col4.metric(
    "💨 Viento",
    f"{viento} km/h",
    f"Ráfagas {rafagas} km/h" if rafagas != "--" else None,
)
col5.metric(
    "☔ Prob. lluvia (3h)", f"{prob_prox_3h} %" if prob_prox_3h is not None else "--"
)

st.caption(f"☁️ Nubosidad: {nubes}% · 📉 Presión: {presion} hPa")
st.caption(
    "ℹ️ El selector de municipio solo actualiza estos indicadores; los mapas de abajo siempre cubren toda la región."
)


# 3. DATOS DE SATÉLITE/RADAR EN TIEMPO REAL (RainViewer)
@st.cache_data(ttl=600)  # RainViewer genera nuevos cuadros cada 10 min
def obtener_datos_rainviewer():
    respuesta = requests.get(
        "https://api.rainviewer.com/public/weather-maps.json", timeout=10
    )
    respuesta.raise_for_status()
    return respuesta.json()


host = radar_actual = generado = None
radar_pronostico = []

try:
    rv = obtener_datos_rainviewer()
    host = rv["host"]
    radar_actual = rv["radar"]["past"][-1]  # cuadro de radar más reciente
    radar_pronostico = rv["radar"].get(
        "nowcast", []
    )  # pronóstico a corto plazo ("dónde lloverá")
    generado = datetime.fromtimestamp(rv["generated"], tz=timezone.utc)
except Exception:
    st.warning(
        "No se pudo obtener el radar en tiempo real. Reintentando en el próximo refresco."
    )

if generado:
    st.sidebar.caption(
        f"🌧️ Radar actualizado: {generado.astimezone().strftime('%H:%M:%S')} hora local "
        "(la fuente se refresca cada ~10 min)"
    )

# Nota: RainViewer documenta un campo "satellite.infrared" en su API pública, pero en la
# práctica ese producto ya no viene poblado en el nivel gratuito (parece requerir su API de
# pago). Por eso el satélite infrarrojo de abajo usa una fuente distinta y confirmada: NOAA.


# =========================================================================
# SECCIÓN A — VISOR DE SATÉLITE INFRARROJO (estilo SMN: imagen aislada,
# sin mapa de calles debajo). Fuente: NOAA/NESDIS/STAR, satélite GOES-19 (Este),
# sector "México", Banda 13 (10.3 µm, IR de onda larga limpia / "Tope de Nubes").
# Es el mismo producto físico que usa el visor de CONAGUA-SMN para GOES Este.
# Gobierno de EE. UU., dato público, sin necesidad de API key ni robots.txt que lo bloquee.
# La imagen se sobrescribe en la misma URL cada ~10 min, así que basta con
# volver a descargarla; no requiere JavaScript ni un mapa Leaflet.
# =========================================================================
NOAA_GOES_MEX_IR_URL = (
    "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/mex/13/2000x2000.jpg"
)

st.subheader("🛰️ Satélite Infrarrojo — Sector México (GOES-19, Banda 13)")
st.caption(
    "Mismo producto (Tope de Nubes / IR limpio) que usa el visor del SMN-CONAGUA para GOES Este. "
    "Fuente: NOAA/NESDIS/STAR — se sobrescribe cada ~10 min."
)


@st.cache_data(ttl=600)  # coincide con la cadencia real de actualización de NOAA
def obtener_imagen_goes_mex():
    respuesta = requests.get(NOAA_GOES_MEX_IR_URL, timeout=15)
    respuesta.raise_for_status()
    return respuesta.content


try:
    imagen_ir = obtener_imagen_goes_mex()
    st.image(
        imagen_ir,
        caption="GOES-19 · Banda 13 · IR onda larga limpia (10.3 µm) · Sector México — NOAA/NESDIS/STAR",
        use_container_width=True,
    )
except Exception:
    st.info(
        "No se pudo descargar la imagen de NOAA en este momento (puede estar caída temporalmente "
        "por mantenimiento). Puedes verla directamente en: "
        "https://www.star.nesdis.noaa.gov/goes/sector_band.php?sat=G19&sector=mex&band=13"
    )


# =========================================================================
# SECCIÓN B — RADAR DE LLUVIA SOBRE LA ZMG (segundo mapa, con calles/satélite
# de fondo y el círculo de alcance real del Radar Doppler IAM-UDG)
# =========================================================================
st.subheader(
    "🗺️ Radar de Lluvia y Riesgo de Inundación — Zona Metropolitana de Guadalajara"
)

st.sidebar.header("🔮 Pronóstico de lluvia")
mostrar_pronostico = st.sidebar.checkbox(
    "Mostrar dónde lloverá (próximos minutos)", value=False
)
frame_pronostico, etiqueta_pronostico = None, None
if mostrar_pronostico and radar_pronostico:
    opciones = {
        datetime.fromtimestamp(f["time"], tz=timezone.utc)
        .astimezone()
        .strftime("%H:%M"): f
        for f in radar_pronostico
    }
    etiqueta_pronostico = st.sidebar.select_slider(
        "Minutos hacia adelante:", options=list(opciones.keys())
    )
    frame_pronostico = opciones[etiqueta_pronostico]
elif mostrar_pronostico:
    st.sidebar.info("El pronóstico no está disponible en este momento.")

m = folium.Map(
    location=[ZMG_CENTRO["lat"], ZMG_CENTRO["lon"]],
    zoom_start=ZMG_ZOOM,
    max_zoom=16,
    tiles=None,
)

# Capa base: Satélite real ESRI (terreno e infraestructura)
folium.raster_layers.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    name="Mapa Satelital (Base ESRI)",
    attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
).add_to(m)

# Capa: Radar de lluvia ACTUAL (maxNativeZoom evita el error "zoom no soportado")
if host and radar_actual:
    folium.raster_layers.TileLayer(
        tiles=f"{host}{radar_actual['path']}/256/{{z}}/{{x}}/{{y}}/2/1_1.png",
        name="🌧️ Radar de lluvia (ahora)",
        attr="RainViewer",
        overlay=True,
        opacity=0.6,
        show=True,
        max_zoom=16,
        max_native_zoom=RAINVIEWER_MAX_NATIVE_ZOOM,
    ).add_to(m)

# Capa: Pronóstico de lluvia (nowcast) - "dónde lloverá"
if host and frame_pronostico:
    folium.raster_layers.TileLayer(
        tiles=f"{host}{frame_pronostico['path']}/256/{{z}}/{{x}}/{{y}}/2/1_1.png",
        name=f"🔮 Pronóstico de lluvia ({etiqueta_pronostico})",
        attr="RainViewer",
        overlay=True,
        opacity=0.6,
        show=True,
        max_zoom=16,
        max_native_zoom=RAINVIEWER_MAX_NATIVE_ZOOM,
    ).add_to(m)

# Círculo: alcance real del Radar Meteorológico Doppler IAM-Universidad de Guadalajara
folium.Circle(
    location=[RADAR_UDG["lat"], RADAR_UDG["lon"]],
    radius=RADAR_UDG_ALCANCE_KM * 1000,
    color="#00BFFF",
    weight=2,
    dash_array="6,6",
    fill=True,
    fill_color="#00BFFF",
    fill_opacity=0.05,
    popup=f"Alcance aproximado del Radar Doppler IAM-UDG (~{RADAR_UDG_ALCANCE_KM} km)",
    tooltip="Cobertura del Radar Meteorológico Doppler (IAM - Universidad de Guadalajara)",
).add_to(m)

folium.Marker(
    location=[RADAR_UDG["lat"], RADAR_UDG["lon"]],
    popup="<b>Radar Meteorológico Doppler</b><br>IAM - Universidad de Guadalajara",
    icon=folium.Icon(color="blue", icon="satellite-dish", prefix="fa"),
).add_to(m)

# Punto crítico local de inundación
folium.Marker(
    location=[20.7132, -103.3768],
    popup="<b>Punto Crítico Local:</b> Historial de inundación desbordamiento Canal Patria.",
    icon=folium.Icon(color="red", icon="warning", prefix="fa"),
).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

st_folium(m, width=1200, height=600, returned_objects=[])

st.caption(
    "El círculo punteado indica el alcance efectivo aproximado (~150 km) del Radar Doppler operado por el "
    "IAM de la Universidad de Guadalajara; la ubicación de la antena es aproximada. "
    "Los datos de satélite/radar y clima se refrescan automáticamente cada 10 minutos "
    "(misma cadencia que las fuentes RainViewer y Open-Meteo). Usa '🔄 Actualizar ahora' "
    "en la barra lateral para forzar un refresco inmediato."
)
