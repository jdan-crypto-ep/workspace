# importar_csv.py
import csv, sqlite3, time, requests

API_KEY = "f7403b333bfc43f9222570802979f444"  # ← tu clave de TMDb
ARCHIVO_CSV = (
    "/home/daniel/Documents/workspace/Proyectos/movies_app/Peliculas Recomendadas.csv"
)
BD = "watchlist.db"


# ---------- Leer el CSV ----------
def leer_titulos(ruta):
    # Probamos codificaciones (Excel en Windows suele guardar en latin-1)
    contenido = None
    for enc in ("utf-8-sig", "latin-1"):
        try:
            with open(ruta, encoding=enc) as f:
                contenido = f.read()
            break
        except UnicodeDecodeError:
            continue
    if contenido is None:
        raise SystemExit("❌ No se pudo leer el archivo.")

    lineas = [l for l in contenido.splitlines() if l.strip()]

    # Detectamos si usa coma o punto y coma (Excel en español suele usar ;)
    primera = lineas[0]
    delimitador = ";" if primera.count(";") > primera.count(",") else ","

    filas = list(csv.reader(lineas, delimiter=delimitador))

    # Saltamos la cabecera si existe
    cabeceras = ("titulo", "título", "title", "pelicula", "película", "nombre")
    if filas and filas[0] and filas[0][0].strip().lower() in cabeceras:
        filas = filas[1:]

    return [fila[0].strip() for fila in filas if fila and fila[0].strip()]


# ---------- Base de datos ----------
def init_db():
    con = sqlite3.connect(BD)
    con.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL, tmdb_id INTEGER, tipo TEXT,
            anio TEXT, sinopsis TEXT, poster TEXT,
            nota REAL, vista INTEGER DEFAULT 0)""")
    con.commit()
    return con


# ---------- Búsqueda en TMDb ----------
def buscar_tmdb(titulo):
    try:
        r = requests.get(
            "https://api.themoviedb.org/3/search/multi",
            params={"api_key": API_KEY, "language": "es", "query": titulo},
            timeout=10,
        )
        r.raise_for_status()
    except Exception:
        return None
    for item in r.json().get("results", []):
        if item.get("media_type") in ("movie", "tv"):
            poster = item.get("poster_path")
            return {
                "titulo": item.get("title") or item.get("name") or titulo,
                "tmdb_id": item["id"],
                "tipo": "Película" if item["media_type"] == "movie" else "Serie",
                "anio": (item.get("release_date") or item.get("first_air_date") or "")[
                    :4
                ],
                "sinopsis": item.get("overview") or "Sin sinopsis disponible.",
                "poster": f"https://image.tmdb.org/t/p/w500{poster}" if poster else "",
                "nota": round(item.get("vote_average") or 0, 1),
            }
    return None


# ---------- Importar ----------
con = init_db()
titulos = leer_titulos(ARCHIVO_CSV)
print(f"📄 Leídos {len(titulos)} títulos del CSV.\n")

nuevos, sin_info, repetidos = 0, 0, 0
for i, t in enumerate(titulos, 1):
    if con.execute(
        "SELECT id FROM items WHERE lower(titulo)=?", (t.lower(),)
    ).fetchone():
        print(f"[{i}/{len(titulos)}] ⏭️  Ya estaba: {t}")
        repetidos += 1
        continue

    info = buscar_tmdb(t)
    if info:
        con.execute(
            "INSERT INTO items (titulo,tmdb_id,tipo,anio,sinopsis,poster,nota) VALUES (?,?,?,?,?,?,?)",
            (
                info["titulo"],
                info["tmdb_id"],
                info["tipo"],
                info["anio"],
                info["sinopsis"],
                info["poster"],
                info["nota"],
            ),
        )
        nuevos += 1
        print(
            f"[{i}/{len(titulos)}] ✅ {info['titulo']} ({info['anio']}) · {info['tipo']}"
        )
    else:
        # Se guarda igualmente para no perderlo
        con.execute(
            "INSERT INTO items (titulo,tipo,sinopsis) VALUES (?,'?','No encontrado en TMDb.')",
            (t,),
        )
        sin_info += 1
        print(f"[{i}/{len(titulos)}] ❌ No encontrado: {t}")
    con.commit()
    time.sleep(0.3)  # pequeña pausa para no saturar la API

total = con.execute("SELECT COUNT(*) FROM items").fetchone()[0]
con.close()
print(
    f"\n📊 Resumen: {nuevos} añadidos con info · {sin_info} sin encontrar · {repetidos} ya estaban"
)
print(f"🎬 Total en tu lista: {total} (guardado en {BD})")
