# completar_datos.py
import sqlite3, time, requests

API_KEY = "PEGA_AQUI_TU_CLAVE"
BD = "watchlist.db"

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
    "NZ": "Nueva Zelanda",
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
    "da": "Danés",
    "uk": "Ucraniano",
    "bn": "Bengalí",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Maratí",
    "pa": "Panyabí",
}


def detalles(tmdb_id, tipo):
    ruta = "movie" if tipo == "Película" else "tv"
    try:
        r = requests.get(
            f"https://api.themoviedb.org/3/{ruta}/{tmdb_id}",
            params={"api_key": API_KEY, "language": "es"},
            timeout=10,
        )
        r.raise_for_status()
    except Exception:
        return None
    d = r.json()
    if d.get("production_countries"):
        paises = [
            PAISES.get(p.get("iso_3166_1"), p.get("name") or p["iso_3166_1"])
            for p in d["production_countries"]
        ]
    else:
        paises = [PAISES.get(c, c) for c in d.get("origin_country", [])]
    if d.get("spoken_languages"):
        idiomas = [
            IDIOMAS.get(l.get("iso_639_1"), l.get("name") or l.get("iso_639_1"))
            for l in d["spoken_languages"]
        ]
    else:
        idiomas = [IDIOMAS.get(c, c) for c in d.get("languages", [])]
    return ", ".join(paises), ", ".join(idiomas)


con = sqlite3.connect(BD)
con.row_factory = sqlite3.Row

# Añade las columnas si no existen todavía
for col in ("paises", "idiomas"):
    try:
        con.execute(f"ALTER TABLE items ADD COLUMN {col} TEXT")
        print(f"Columna '{col}' creada.")
    except sqlite3.OperationalError:
        pass
con.commit()

pend = con.execute(
    "SELECT id, titulo, tmdb_id, tipo FROM items "
    "WHERE tmdb_id IS NOT NULL AND (paises IS NULL OR paises = '')"
).fetchall()
print(f"Hay {len(pend)} títulos por completar.\n")

for fila in pend:
    res = detalles(fila["tmdb_id"], fila["tipo"])
    if res:
        con.execute(
            "UPDATE items SET paises=?, idiomas=? WHERE id=?",
            (res[0], res[1], fila["id"]),
        )
        con.commit()
        print(f"✅ {fila['titulo']} → 🌍 {res[0]} · 🗣️ {res[1]}")
    else:
        print(f"⚠️ No se pudo completar: {fila['titulo']}")
    time.sleep(0.3)

con.close()
print("\nListo ✔")
