#!/usr/bin/env python3

# mini_web.py
import sqlite3, socket, threading, webbrowser, unicodedata, random
import requests
from flask import (
    Flask,
    request,
    redirect,
    url_for,
    flash,
    render_template_string,
    session,
)

API_KEY = "f7403b333bfc43f9222570802979f444"
URL_BUSQUEDA = "https://api.themoviedb.org/3/search/multi"
BD = "/home/daniel/Documents/workspace/Proyectos/movies_app/watchlist.db"
PUERTO = 5000
POR_PAGINA = 10

app = Flask(__name__)
app.secret_key = "clave-local"

# ---------- Nombres en español ----------
PAISES = {
    "US": "Estados Unidos",
    "GB": "Reino Unido",
    "ES": "España",
    "FR": "Francia",
    "DE": "Alemania",
    "IT": "Italia",
    "JP": "Japón",
    "KR": "Corea del Sur",
    "CN": "China",
    "HK": "Hong Kong",
    "TW": "Taiwán",
    "IN": "India",
    "MX": "México",
    "AR": "Argentina",
    "BR": "Brasil",
    "CL": "Chile",
    "CO": "Colombia",
    "PE": "Perú",
    "UY": "Uruguay",
    "VE": "Venezuela",
    "CU": "Cuba",
    "CA": "Canadá",
    "AU": "Australia",
    "NZ": "Nueva Zelanda",
    "RU": "Rusia",
    "DK": "Dinamarca",
    "SE": "Suecia",
    "NO": "Noruega",
    "FI": "Finlandia",
    "IS": "Islandia",
    "NL": "Países Bajos",
    "BE": "Bélgica",
    "LU": "Luxemburgo",
    "CH": "Suiza",
    "AT": "Austria",
    "IE": "Irlanda",
    "PT": "Portugal",
    "PL": "Polonia",
    "CZ": "Chequia",
    "HU": "Hungría",
    "RO": "Rumanía",
    "GR": "Grecia",
    "TR": "Turquía",
    "IL": "Israel",
    "EG": "Egipto",
    "MA": "Marruecos",
    "ZA": "Sudáfrica",
    "TH": "Tailandia",
    "VN": "Vietnam",
    "ID": "Indonesia",
    "PH": "Filipinas",
    "AE": "Emiratos Árabes Unidos",
    "SA": "Arabia Saudí",
    "UA": "Ucrania",
    "HR": "Croacia",
    "RS": "Serbia",
}

IDIOMAS = {
    "en": "Inglés",
    "es": "Español",
    "fr": "Francés",
    "de": "Alemán",
    "it": "Italiano",
    "pt": "Portugués",
    "ja": "Japonés",
    "ko": "Coreano",
    "zh": "Chino",
    "ru": "Ruso",
    "hi": "Hindi",
    "ca": "Catalán",
    "gl": "Gallego",
    "eu": "Vasco",
    "nl": "Neerlandés",
    "sv": "Sueco",
    "da": "Danés",
    "no": "Noruego",
    "fi": "Finés",
    "pl": "Polaco",
    "cs": "Checo",
    "hu": "Húngaro",
    "ro": "Rumano",
    "el": "Griego",
    "tr": "Turco",
    "he": "Hebreo",
    "ar": "Árabe",
    "fa": "Persa",
    "th": "Tailandés",
    "vi": "Vietnamita",
    "id": "Indonesio",
    "ms": "Malayo",
    "tl": "Filipino",
    "uk": "Ucraniano",
    "bn": "Bengalí",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Maratí",
    "pa": "Panyabí",
}


def normalizar(t):
    if t is None:
        return ""
    t = t.strip().lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn"
    )


# ---------- Base de datos ----------
def get_db():
    con = sqlite3.connect(BD)
    con.row_factory = sqlite3.Row
    con.create_function("SIN_ACENTOS", 1, normalizar)
    return con


def init_db():
    con = get_db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL, tmdb_id INTEGER, tipo TEXT,
            anio TEXT, sinopsis TEXT, poster TEXT,
            nota REAL, vista INTEGER DEFAULT 0)""")
    con.commit()
    for col, tipo_col in (
        ("paises", "TEXT"),
        ("idiomas", "TEXT"),
        ("anime", "INTEGER DEFAULT 0"),
        ("fav", "INTEGER DEFAULT 0"),
    ):
        try:
            con.execute(f"ALTER TABLE items ADD COLUMN {col} {tipo_col}")
        except sqlite3.OperationalError:
            pass
    con.commit()
    con.close()


# ---------- TMDb ----------
def buscar_tmdb(texto):
    r = requests.get(
        URL_BUSQUEDA,
        params={"api_key": API_KEY, "language": "es", "query": texto},
        timeout=10,
    )
    r.raise_for_status()
    return [
        x for x in r.json().get("results", []) if x.get("media_type") in ("movie", "tv")
    ]


def detalles_tmdb(tmdb_id, tipo):
    ruta = "movie" if tipo == "Película" else "tv"
    r = requests.get(
        f"https://api.themoviedb.org/3/{ruta}/{tmdb_id}",
        params={"api_key": API_KEY, "language": "es"},
        timeout=10,
    )
    r.raise_for_status()
    d = r.json()
    poster = d.get("poster_path")
    if d.get("production_countries"):
        paises = [
            PAISES.get(p.get("iso_3166_1"), p.get("name") or p["iso_3166_1"])
            for p in d["production_countries"]
        ]
    else:
        paises = [PAISES.get(c, c) for c in d.get("origin_country", [])]
    if d.get("spoken_languages"):
        idiomas = [
            IDIOMAS.get(l.get("iso_639_1"), l.get("name") or l["iso_639_1"])
            for l in d["spoken_languages"]
        ]
    else:
        idiomas = [IDIOMAS.get(c, c) for c in d.get("languages", [])]
    return dict(
        titulo=d.get("title") or d.get("name"),
        tmdb_id=tmdb_id,
        tipo=tipo,
        anio=(d.get("release_date") or d.get("first_air_date") or "")[:4],
        sinopsis=d.get("overview") or "Sin sinopsis disponible.",
        poster=f"https://image.tmdb.org/t/p/w500{poster}" if poster else "",
        nota=round(d.get("vote_average") or 0, 1),
        paises=", ".join(paises),
        idiomas=", ".join(idiomas),
    )


def guardar_titulo(tmdb_id, tipo):
    """Obtiene toda la info de TMDb y la guarda. Devuelve (ok, mensaje)."""
    try:
        info = detalles_tmdb(tmdb_id, tipo)
    except Exception:
        return False, "❌ No se pudo obtener la información de TMDb."
    con = get_db()
    if con.execute(
        "SELECT id FROM items WHERE tmdb_id=? OR lower(titulo)=?",
        (tmdb_id, info["titulo"].lower()),
    ).fetchone():
        con.close()
        return False, f"'{info['titulo']}' ya estaba en tu lista."
    con.execute(
        """INSERT INTO items
        (titulo,tmdb_id,tipo,anio,sinopsis,poster,nota,paises,idiomas)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            info["titulo"],
            info["tmdb_id"],
            info["tipo"],
            info["anio"],
            info["sinopsis"],
            info["poster"],
            info["nota"],
            info["paises"],
            info["idiomas"],
        ),
    )
    con.commit()
    con.close()
    return True, f"✅ '{info['titulo']}' añadida a tu lista."


# ---------- Plantillas ----------
ESTILOS = """<style>
  body{font-family:system-ui,sans-serif;background:#15151f;color:#eee;padding:2rem;max-width:960px;margin:auto}
  form{display:flex;gap:.5rem;margin:1rem 0 1.5rem}
  input[type=text]{flex:1;padding:.7rem;border-radius:8px;border:1px solid #444;background:#222;color:#eee;font-size:1rem}
  button,.btn{background:#e50914;color:#fff;border:0;border-radius:8px;padding:.7rem 1.2rem;
       font-size:1rem;cursor:pointer;text-decoration:none;display:inline-block}
  .sec{background:#3a3a4a}
  .mini{padding:.35rem .7rem;font-size:.8rem;margin-top:.3rem}
  .flash{background:#2e7d32;padding:.6rem 1rem;border-radius:8px;margin:.5rem 0}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:1rem}
  .card{background:#1e1e2c;border-radius:10px;overflow:hidden;padding-bottom:.8rem}
  .card.vista{outline:3px solid #2e7d32;outline-offset:-3px}
  .card img{width:100%;display:block}
  .info{padding:0 .8rem}
  .badge{display:inline-block;background:#3a3a4a;border-radius:5px;padding:.1rem .5rem;font-size:.75rem;margin-top:.3rem}
  .t-peli{background:#8b2020}
  .t-serie{background:#1f4f8b}
  .ok{background:#2e7d32}
  .gris{color:#999;font-size:.85rem}
  .sinfoto{height:250px;display:flex;align-items:center;justify-content:center;background:#222}
  .cardgrande{display:flex;gap:1.5rem;background:#1e1e2c;border-radius:12px;padding:1.5rem;flex-wrap:wrap}
  .cardgrande img{max-width:280px;border-radius:10px}
  .cardgrande.vista{outline:3px solid #2e7d32}
  .stats{display:flex;gap:.8rem;flex-wrap:wrap;margin:1rem 0}
  .stat{background:#1e1e2c;border-radius:10px;padding:.6rem 1rem;text-align:center;min-width:90px}
  .stat b{display:block;font-size:1.4rem}
  .stat span{color:#999;font-size:.8rem}
  .ani{background:#7c3aed}
  .fav{background:#c0264b}
</style>"""

HOME = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Mi lista</title>{{ estilos|safe }}</head><body>

{% macro tarjeta(i) %}
    <div class="card {{ 'vista' if i.vista else '' }}">
      {% if i.poster %}<a href="/ver/{{ i.id }}"><img src="{{ i.poster }}" loading="lazy"></a>
      {% else %}<div class="sinfoto">🎞️</div>{% endif %}
      <div class="info">
        <h3 style="margin:.6rem 0 .2rem;font-size:1rem">{{ i.titulo }}</h3>
        <span class="badge {{ 't-peli' if i.tipo == 'Película' else ('t-serie' if i.tipo == 'Serie' else '') }}">{{ i.tipo }}</span>
        {% if i.vista %}<span class="badge ok">✔ Vista</span>{% endif %}
        {% if i.anime %}<span class="badge ani">🎌 Anime</span>{% endif %}
        {% if i.fav %}<span class="badge fav">❤️ Favorito</span>{% endif %}
        {% if i.nota %}<span class="badge">⭐ {{ i.nota }}</span>{% endif %}
        <p class="gris">{{ i.anio }}</p>
        <p class="gris">🌍 {{ i.paises or '—' }}</p>
        <p class="gris">🗣️ {{ i.idiomas or '—' }}</p>
        <p style="margin:.3rem 0 0">
          <a class="btn sec mini" href="/vista/{{ i.id }}">{{ '↩️ No vista' if i.vista else '✅ Vista' }}</a>
          <a class="btn sec mini" href="/anime/{{ i.id }}">{{ '🎌 Anime ✓' if i.anime else '🎌 Anime' }}</a>
          <a class="btn sec mini" href="/fav/{{ i.id }}">{{ '❤️ Favorito ✓' if i.fav else '🤍 Favorito' }}</a>
          <a class="btn sec mini" href="/editar/{{ i.id }}?volver=ver">✏️</a>
          <a class="btn sec mini" href="/borrar/{{ i.id }}" onclick="return confirm('¿Quitar este título de la lista?')">🗑️</a>
        </p>
      </div>
    </div>
{% endmacro %}

<h1>🎬 Mi lista de visionado</h1>
{% for m in get_flashed_messages() %}<div class="flash">{{ m }}</div>{% endfor %}

<p><a class="btn" style="font-size:1.1rem" href="/aleatorio{% if anime %}?anime=1{% endif %}">🎲 Sorpréndeme{% if anime %} (anime){% endif %}</a></p>

<form method="get" action="/" style="margin-bottom:.5rem">
  <input type="text" name="b" value="{{ busqueda }}" placeholder="🔍 Buscar en tu lista (por título)…">
  <button type="submit">Buscar</button>
</form>

<form method="get" action="/">
  <input type="text" name="q" value="{{ query }}" placeholder="O busca en TMDb para añadir algo nuevo…">
  <button>Buscar</button>
</form>

{% if query %}
  <h2>Resultados en TMDb para "{{ query }}"</h2>
  {% if not resultados %}<p>No se encontró nada 😕</p>{% endif %}
  <div class="grid">
  {% for item in resultados %}
    <div class="card">
      {% if item.poster_path %}<img src="https://image.tmdb.org/t/p/w500{{ item.poster_path }}" loading="lazy">
      {% else %}<div class="sinfoto">🎞️</div>{% endif %}
      <div class="info">
        <h3 style="margin:.6rem 0 .2rem;font-size:1rem">{{ item.title or item.name }}</h3>
        <span class="badge {{ 't-peli' if item.media_type == 'movie' else 't-serie' }}">
          {{ 'Película' if item.media_type == 'movie' else 'Serie' }}</span>
        <span class="badge">⭐ {{ item.vote_average }}</span>
        <p class="gris">{{ (item.release_date or item.first_air_date or '')[:4] }}</p>
        <form method="post" action="/agregar" style="margin:0">
          <input type="hidden" name="tmdb_id" value="{{ item.id }}">
          <input type="hidden" name="tipo" value="{{ 'Película' if item.media_type == 'movie' else 'Serie' }}">
          <button type="submit" class="btn mini">➕ Añadir a mi lista</button>
        </form>
      </div>
    </div>
  {% endfor %}
  </div>
{% elif busqueda %}
  <h2>En tu lista: "{{ busqueda }}" <span class="gris">({{ busqueda_items|length }} coincidencias)</span></h2>
  {% if not busqueda_items %}<p>No hay nada en tu lista que coincida 😕</p>{% endif %}
  <div class="grid">
  {% for i in busqueda_items %}{{ tarjeta(i) }}{% endfor %}
  </div>
  <p style="margin-top:1rem"><a class="btn sec" href="/">← Volver a la lista</a></p>
{% else %}
  <h2>Mi lista {% if filtro_texto %}<span class="gris">· {{ filtro_texto }}</span>{% endif %}</h2>
  <div class="stats">
    <div class="stat"><b>{{ animes }}</b><span>🎌 Anime</span></div>
    <div class="stat"><b>{{ favs }}</b><span>❤️ Favoritos</span></div>
    <div class="stat"><b>{{ total }}</b><span>Registros</span></div>
    <div class="stat"><b>{{ peliculas }}</b><span>🎬 Películas</span></div>
    <div class="stat"><b>{{ series }}</b><span>📺 Series</span></div>
    <div class="stat"><b>{{ vistas }}</b><span>✔ Vistas</span></div>
    <div class="stat"><b>{{ pendientes }}</b><span>⏳ Pendientes</span></div>
    {% if sin_datos %}<div class="stat"><b>{{ sin_datos }}</b><span>❓ Sin encontrar</span></div>{% endif %}
  </div>

  <p style="margin:1rem 0 .3rem">
    <a class="btn mini {{ 'sec' if tipo != 'peliculas' else '' }}"
       href="{{ url_filtro(tipo='' if tipo == 'peliculas' else 'peliculas') }}">🎬 Películas</a>
    <a class="btn mini {{ 'sec' if tipo != 'series' else '' }}"
       href="{{ url_filtro(tipo='' if tipo == 'series' else 'series') }}">📺 Series</a>
  </p>
      <p style="margin:0 0 .3rem">
    <span class="gris">Mostrar:</span>
    <a class="btn mini {{ 'sec' if estado == 'vistas' else '' }}"
       href="{{ url_filtro(estado='' if estado == 'vistas' else 'vistas') }}">✔ Vistas</a>
    <a class="btn mini {{ 'sec' if estado == 'sin_datos' else '' }}"
       href="{{ url_filtro(estado='' if estado == 'sin_datos' else 'sin_datos') }}">❓ Sin encontrar</a>
    <a class="btn mini {{ 'sec' if anime != '1' else '' }}"
       href="{{ url_filtro(anime='' if anime == '1' else '1') }}">🎌 Anime</a>
    <a class="btn mini {{ 'sec' if fav != '1' else '' }}"
       href="{{ url_filtro(fav='' if fav == '1' else '1') }}">❤️ Favoritos</a>
    <a class="btn mini {{ 'sec' if nota != '7' else '' }}"
       href="{% if nota == '7' %}{{ url_filtro(nota='') }}{% else %}{{ url_filtro(nota='7', orden='nota') }}{% endif %}">⭐ 7+</a>
  </p>
  <p class="gris" style="margin:0 0 1rem">Las marcadas como vistas se ocultan aquí; actívalas con ✔ Vistas.</p>
  
    <p style="margin:0 0 1rem">
    <span class="gris">Ordenar por:</span>
    <a class="btn mini {{ 'sec' if orden else '' }}" href="{{ url_filtro(orden='') }}">🔀 Al azar</a>
    <a class="btn mini {{ 'sec' if orden == 'nota' else '' }}" href="{{ url_filtro(orden='nota') }}">🏆 Nota (mayor primero)</a>
    <a class="btn mini {{ 'sec' if orden != 'alfabeto' else '' }}" href="{{ url_filtro(orden='alfabeto') }}">🔤 A-Z</a>
    {% if hay_filtros %}<a class="btn mini" href="/" style="background:#5a2a2a">✖ Quitar filtros</a>{% endif %}
  </p>

  <div class="grid">
  {% for i in items %}{{ tarjeta(i) }}{% endfor %}
  </div>
  {% if not items %}<p>No hay títulos con esta combinación de filtros 😕</p>{% endif %}
  <p class="gris" style="margin-top:1rem">Mostrando {{ items|length }} de {{ total_filtrado }}</p>
  {% if items|length < total_filtrado %}
        <a class="btn sec" href="/?pagina={{ pagina + 1 }}{% if tipo %}&tipo={{ tipo }}{% endif %}{% if estado %}&estado={{ estado }}{% endif %}{% if nota %}&nota={{ nota }}{% endif %}{% if anime %}&anime={{ anime }}{% endif %}{% if fav %}&fav={{ fav }}{% endif %}{% if orden %}&orden={{ orden }}{% endif %}">Ver 10 más ↓</a>
  {% endif %}
{% endif %}


</body></html>"""

AZAR = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Sorpresa</title>{{ estilos|safe }}</head><body>

<h1>{% if solo_anime %}🎲 Hoy toca anime…{% else %}🎲 Hoy toca ver…{% endif %}</h1>
{% for m in get_flashed_messages() %}<div class="flash">{{ m }}</div>{% endfor %}
{% if item %}
<div class="cardgrande {{ 'vista' if item.vista else '' }}">
  {% if item.poster %}<img src="{{ item.poster }}">
  {% else %}<div class="sinfoto" style="width:280px">🎞️</div>{% endif %}
  <div style="max-width:520px">
    <h2 style="margin:0 0 .3rem">{{ item.titulo }} {% if item.anio %}({{ item.anio }}){% endif %}</h2>
    <span class="badge {{ 't-peli' if item.tipo == 'Película' else ('t-serie' if item.tipo == 'Serie' else '') }}">{{ item.tipo }}</span>
    {% if item.anime %}<span class="badge ani">🎌 Anime</span>{% endif %}
    {% if item.fav %}<span class="badge fav">❤️ Favorito</span>{% endif %}
    {% if item.vista %}<span class="badge ok">✔ Ya la viste</span>{% endif %}
    {% if item.nota %}<span class="badge">⭐ {{ item.nota }}</span>{% endif %}
    <p class="gris">🌍 {{ item.paises or '—' }}</p>
    <p class="gris">🗣️ {{ item.idiomas or '—' }}</p>
    <p style="margin-top:1rem">{{ item.sinopsis }}</p>
    <p style="margin-top:1rem">
      <a class="btn sec mini" href="/vista/{{ item.id }}">{{ '↩️ Marcar no vista' if item.vista else '✅ La he visto' }}</a>
      <a class="btn sec mini" href="/fav/{{ item.id }}">{{ '❤️ Es favorito ✓' if item.fav else '🤍 Marcar favorito' }}</a>
      <a class="btn sec mini" href="/anime/{{ item.id }}">{{ '🎌 Es anime ✓' if item.anime else '🎌 Marcar anime' }}</a>
      <a class="btn sec mini" href="/editar/{{ item.id }}?volver={{ item.id }}">✏️ Corregir título</a>
      <a class="btn sec mini" href="/borrar/{{ item.id }}" onclick="return confirm('¿Quitar este título de la lista?')">🗑️ Quitar</a>
    </p>
  </div>
</div>
<p style="margin-top:1.2rem">
  <a class="btn" href="/aleatorio{% if solo_anime %}?anime=1{% endif %}">🎲 Otra</a>
  <a class="btn sec" href="/">🏠 Volver a la lista</a>
</p>
{% else %}
<p>Tu lista está vacía todavía. 🙁</p>
<a class="btn sec" href="/">🏠 Volver</a>
{% endif %}

</body></html>"""

EDITAR = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Corregir título</title>{{ estilos|safe }}</head><body>

<h1>✏️ Corregir título</h1>
{% for m in get_flashed_messages() %}<div class="flash">{{ m }}</div>{% endfor %}

<div class="cardgrande">
  {% if item.poster %}<img src="{{ item.poster }}" style="max-width:160px">{% endif %}
  <div>
    <h2 style="margin:0 0 .3rem">{{ item.titulo }} {% if item.anio %}({{ item.anio }}){% endif %}</h2>
    <span class="badge">{{ item.tipo }}</span>
    <p class="gris">{{ item.sinopsis[:160] }}…</p>
  </div>
</div>

<form method="post" style="display:block">
  <input type="hidden" name="volver" value="{{ volver }}">
  <p class="gris" style="margin-bottom:.3rem">Título correcto:</p>
  <input type="text" name="titulo" value="{{ item.titulo }}" autofocus>
  <p><label class="gris" style="font-size:.9rem">
    <input type="checkbox" name="rebuscar" checked>
    Buscar en TMDb con este título y actualizar también póster, sinopsis, país e idiomas
  </label></p>
  <button type="submit">💾 Guardar</button>
  <a class="btn sec" href="{{ cancelar }}">Cancelar</a>
</form>

</body></html>"""


# ---------- Rutas ----------
@app.route("/")
def inicio():
    query = request.args.get("q", "").strip()
    busqueda = request.args.get("b", "").strip()

    if query:
        resultados = []
        try:
            resultados = buscar_tmdb(query)
        except Exception:
            flash("Problema de conexión con TMDb.")
        return render_template_string(
            HOME,
            estilos=ESTILOS,
            query=query,
            resultados=resultados,
            items=[],
            total=0,
            vistas=0,
            peliculas=0,
            series=0,
            sin_datos=0,
            pagina=1,
            busqueda="",
            busqueda_items=[],
        )

    if busqueda:
        con = get_db()
        busqueda_items = con.execute(
            "SELECT * FROM items WHERE SIN_ACENTOS(titulo) LIKE '%' || SIN_ACENTOS(?) || '%' "
            "ORDER BY titulo",
            (busqueda,),
        ).fetchall()
        con.close()
        return render_template_string(
            HOME,
            estilos=ESTILOS,
            query="",
            resultados=[],
            items=[],
            total=0,
            vistas=0,
            peliculas=0,
            series=0,
            sin_datos=0,
            pagina=1,
            busqueda=busqueda,
            busqueda_items=busqueda_items,
        )

    # ---------- Filtros combinables ----------
    tipo = request.args.get("tipo", "")
    if tipo not in ("peliculas", "series"):
        tipo = ""
    estado = request.args.get("estado", "")
    if estado not in ("pendientes", "vistas", "sin_datos"):
        estado = ""
    nota = "7" if request.args.get("nota") == "7" else ""
    anime = "1" if request.args.get("anime") == "1" else ""
    fav = "1" if request.args.get("fav") == "1" else ""
    orden = request.args.get("orden", "")
    if orden not in ("nota", "alfabeto"):
        orden = ""

    condiciones = []
    if tipo == "peliculas":
        condiciones.append("tipo='Película'")
    elif tipo == "series":
        condiciones.append("tipo='Serie'")
    if estado == "vistas":
        condiciones.append("vista=1")
    elif estado == "sin_datos":
        condiciones.append("tmdb_id IS NULL")
    else:
        condiciones.append("vista=0")
    if nota:
        condiciones.append("nota >= 7")
    # El anime es una categoría aparte: si el filtro no está activo se oculta,
    # y si está activo solo se muestran animes
    condiciones.append("anime=1" if anime else "anime=0")
    # Favoritos es una categoría aparte: ocultos salvo con el filtro ❤️
    condiciones.append("fav=1" if fav else "fav=0")
    where = "WHERE " + " AND ".join(condiciones) if condiciones else ""
    if orden == "nota":
        orden_sql = "ORDER BY nota DESC"
    elif orden == "alfabeto":
        orden_sql = (
            "ORDER BY (SIN_ACENTOS(titulo) GLOB '[0-9]*') DESC, " "SIN_ACENTOS(titulo)"
        )
    else:
        # Orden por defecto: al azar. Nueva semilla en cada recarga completa,
        # pero se conserva al paginar con "Ver 10 más"
        if "pagina" not in request.args or "seed" not in session:
            session["seed"] = random.randint(1, 1000000)
        orden_sql = f"ORDER BY (id * {int(session['seed'])}) % 1000003"

    try:
        pagina = max(1, int(request.args.get("pagina", 1)))
    except ValueError:
        pagina = 1

    def url_filtro(**cambios):
        params = {
            "tipo": tipo,
            "estado": estado,
            "nota": nota,
            "anime": anime,
            "fav": fav,
            "orden": orden,
        }
        params.update(cambios)
        qs = "&".join(f"{k}={v}" for k, v in params.items() if v)
        return f"/?{qs}" if qs else "/"

    con = get_db()
    total = con.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    vistas = con.execute(
        "SELECT COUNT(*) FROM items WHERE vista=1 AND anime=0 AND fav=0"
    ).fetchone()[0]
    pendientes = con.execute(
        "SELECT COUNT(*) FROM items WHERE vista=0 AND anime=0 AND fav=0"
    ).fetchone()[0]
    peliculas = con.execute(
        "SELECT COUNT(*) FROM items WHERE tipo='Película'"
    ).fetchone()[0]
    series = con.execute("SELECT COUNT(*) FROM items WHERE tipo='Serie'").fetchone()[0]
    sin_datos = con.execute(
        "SELECT COUNT(*) FROM items WHERE tmdb_id IS NULL"
    ).fetchone()[0]
    animes = con.execute("SELECT COUNT(*) FROM items WHERE anime=1").fetchone()[0]
    favs = con.execute("SELECT COUNT(*) FROM items WHERE fav=1").fetchone()[0]
    total_filtrado = con.execute(f"SELECT COUNT(*) FROM items {where}").fetchone()[0]
    items = con.execute(
        f"SELECT * FROM items {where} {orden_sql} LIMIT ?", (pagina * POR_PAGINA,)
    ).fetchall()
    con.close()

    etiquetas = []
    if tipo == "peliculas":
        etiquetas.append("🎬 películas")
    elif tipo == "series":
        etiquetas.append("📺 series")
    if estado == "vistas":
        etiquetas.append("mostrando ✔ VISTAS")
    elif estado == "sin_datos":
        etiquetas.append("❓ sin encontrar")
    else:
        etiquetas.append("⏳ solo pendientes")
    if anime:
        etiquetas.append("🎌 solo anime")
    if fav:
        etiquetas.append("❤️ solo favoritos")
    if nota:
        etiquetas.append("⭐ 7+")
    if orden == "nota":
        etiquetas.append("ordenado por nota (mayor primero)")
    elif orden == "alfabeto":
        etiquetas.append("ordenado A-Z (números primero)")

    return render_template_string(
        HOME,
        estilos=ESTILOS,
        query="",
        resultados=[],
        items=items,
        total=total,
        vistas=vistas,
        pendientes=pendientes,
        peliculas=peliculas,
        series=series,
        sin_datos=sin_datos,
        pagina=pagina,
        busqueda="",
        busqueda_items=[],
        tipo=tipo,
        estado=estado,
        nota=nota,
        anime=anime,
        fav=fav,
        favs=favs,
        orden=orden,
        animes=animes,
        url_filtro=url_filtro,
        filtro_texto=" · ".join(etiquetas),
        hay_filtros=bool(etiquetas),
        total_filtrado=total_filtrado,
    )


@app.route("/agregar", methods=["POST"])
def agregar():
    tmdb_id = request.form.get("tmdb_id", type=int)
    tipo = request.form.get("tipo", "Película")
    if tmdb_id:
        ok, msg = guardar_titulo(tmdb_id, tipo)
        flash(msg)
    return redirect(request.referrer or url_for("inicio"))


@app.route("/agregar_rapido", methods=["POST"])
def agregar_rapido():
    titulo = request.form.get("titulo", "").strip()
    if titulo:
        try:
            res = buscar_tmdb(titulo)
        except Exception:
            res = []
        if res:
            p = res[0]
            ok, msg = guardar_titulo(
                p["id"], "Película" if p["media_type"] == "movie" else "Serie"
            )
            flash(msg)
        else:
            flash(
                f"No encontré '{titulo}'. Usa el buscador para elegir el resultado exacto."
            )
    return redirect(url_for("inicio"))


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    con = get_db()
    item = con.execute("SELECT * FROM items WHERE id=?", (id,)).fetchone()
    if item is None:
        con.close()
        return redirect(url_for("inicio"))

    volver = request.args.get("volver") or request.form.get("volver") or ""
    if volver == "ver":
        destino = url_for("ver", id=id)  # quedarse en este mismo título
    elif volver.isdigit():
        destino = url_for("ver", id=int(volver))
    else:
        destino = url_for("inicio")

    if request.method == "POST":
        nuevo = request.form.get("titulo", "").strip()
        if not nuevo:
            flash("El título no puede estar vacío.")
        else:
            actualizado = False
            if request.form.get("rebuscar") == "on":
                try:
                    res = buscar_tmdb(nuevo)
                except Exception:
                    res = []
                if res:
                    p = res[0]
                    tipo = "Película" if p["media_type"] == "movie" else "Serie"
                    try:
                        info = detalles_tmdb(p["id"], tipo)
                        con.execute(
                            """UPDATE items SET titulo=?, tmdb_id=?, tipo=?, anio=?,
                            sinopsis=?, poster=?, nota=?, paises=?, idiomas=? WHERE id=?""",
                            (
                                info["titulo"],
                                info["tmdb_id"],
                                info["tipo"],
                                info["anio"],
                                info["sinopsis"],
                                info["poster"],
                                info["nota"],
                                info["paises"],
                                info["idiomas"],
                                id,
                            ),
                        )
                        con.commit()
                        flash(
                            f"✅ Corregida con la información de TMDb: '{info['titulo']}'"
                        )
                        actualizado = True
                    except Exception:
                        flash(
                            "TMDb dio error al obtener los detalles; guardo solo el título."
                        )
                else:
                    flash("No encontré ese título en TMDb; guardo solo el texto.")
            if not actualizado:
                con.execute("UPDATE items SET titulo=? WHERE id=?", (nuevo, id))
                con.commit()
                flash("✅ Título guardado.")
        con.close()
        return redirect(destino)

    con.close()
    return render_template_string(
        EDITAR, estilos=ESTILOS, item=item, volver=volver, cancelar=destino
    )


@app.route("/aleatorio")
def aleatorio():
    solo_anime = request.args.get("anime") == "1"
    categoria = "anime=1" if solo_anime else "anime=0"
    con = get_db()
    item = con.execute(
        f"SELECT * FROM items WHERE vista=0 AND {categoria} ORDER BY RANDOM() LIMIT 1"
    ).fetchone()
    if item is None:
        item = con.execute(
            f"SELECT * FROM items WHERE {categoria} ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
    con.close()
    return render_template_string(
        AZAR, estilos=ESTILOS, item=item, solo_anime=solo_anime
    )


@app.route("/ver/<int:id>")
def ver(id):
    con = get_db()
    item = con.execute("SELECT * FROM items WHERE id=?", (id,)).fetchone()
    con.close()
    if item is None:
        flash("Ese título ya no está en la lista.")
        return redirect(url_for("inicio"))
    return render_template_string(AZAR, estilos=ESTILOS, item=item)


@app.route("/vista/<int:id>")
def marcar_vista(id):
    con = get_db()
    con.execute("UPDATE items SET vista = 1 - vista WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect(request.referrer or url_for("inicio"))


@app.route("/anime/<int:id>")
def marcar_anime(id):
    con = get_db()
    con.execute("UPDATE items SET anime = 1 - anime WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect(request.referrer or url_for("inicio"))


@app.route("/fav/<int:id>")
def marcar_fav(id):
    con = get_db()
    con.execute("UPDATE items SET fav = 1 - fav WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect(request.referrer or url_for("inicio"))


@app.route("/borrar/<int:id>")
def borrar(id):
    con = get_db()
    con.execute("DELETE FROM items WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect(request.referrer or url_for("inicio"))


# ---------- Arranque con doble clic ----------
def puerto_libre():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", PUERTO))
            return True
        except OSError:
            return False


if __name__ == "__main__":
    init_db()
    if puerto_libre():
        # Abre el navegador solo cuando el servidor esté listo
        threading.Timer(
            1.2, lambda: webbrowser.open(f"http://127.0.0.1:{PUERTO}")
        ).start()
        print("Iniciando… se abrirá el navegador automáticamente.")
        print("Deja esta ventana abierta mientras uses la aplicación.")
        app.run(port=PUERTO, debug=False)
    else:
        webbrowser.open(f"http://127.0.0.1:{PUERTO}")
        print("La aplicación ya estaba en marcha; abriendo en el navegador.")
