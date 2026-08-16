"""
=============================================================
  CURVAS IDF, TABLA DE INTENSIDADES Y HIETOGRAMAS
  Análisis hidrológico preliminar - Método de Bell (1969)
  con corrección de Frederich (duración < 60 min)
=============================================================

DATOS REQUERIDOS:
  - Precipitación para cada periodo de retorno a 24h (P24)
  - Precipitación para cada periodo de retorno a 1h  (P1h)

MÉTODOS UTILIZADOS:
  - Relación de Bell (1969): Pt,T = (0.54*t^0.25 - 0.50) * P60,TP
  - Relación P60,T / P24,T ≈ 0.40 ~ 0.45 (IILA / Témez)
  - Hietograma: Método de los Bloques Alternos
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import LogLocator, LogFormatter
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
#  CONFIGURACIÓN DE ESTILO
# ─────────────────────────────────────────────
plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "legend.fontsize": 8,
        "grid.alpha": 0.3,
    }
)

COLORES = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]


# ─────────────────────────────────────────────
#  1. INGRESO DE DATOS
# ─────────────────────────────────────────────
def ingresar_datos():
    print("\n" + "=" * 60)
    print("   ANÁLISIS HIDROLÓGICO PRELIMINAR — CURVAS IDF")
    print("=" * 60)
    print("\nIngresa las precipitaciones para cada periodo de retorno.")
    print("(Presiona Enter para usar los valores de ejemplo)\n")

    # Periodos de retorno disponibles
    periodos = [2, 5, 10, 25, 50, 100]

    datos = {}
    usar_ejemplo = input("¿Usar datos de ejemplo? (s/n) [s]: ").strip().lower()

    if usar_ejemplo in ("", "s", "si", "sí"):
        # Datos de ejemplo típicos para zona tropical/andina
        datos = {
            2: {"P24": 55.0, "P1h": 24.0},
            5: {"P24": 72.0, "P1h": 32.0},
            10: {"P24": 84.0, "P1h": 38.0},
            25: {"P24": 100.0, "P1h": 46.0},
            50: {"P24": 112.0, "P1h": 52.0},
            100: {"P24": 124.0, "P1h": 58.0},
        }
        print("\nUsando datos de ejemplo:")
        print(f"{'TR (años)':<12} {'P24h (mm)':<14} {'P1h (mm)'}")
        print("-" * 38)
        for tr, v in datos.items():
            print(f"{tr:<12} {v['P24']:<14.1f} {v['P1h']:.1f}")
    else:
        print("\nIngresa los datos (deja en blanco para omitir un periodo):\n")
        print(f"{'TR (años)':<12} {'P24h (mm)':<14} {'P1h (mm)'}")
        print("-" * 38)
        for tr in periodos:
            try:
                p24_str = input(f"TR={tr:>3} años → P24h = ").strip()
                if not p24_str:
                    continue
                p1h_str = input(f"             → P1h  = ").strip()
                if not p1h_str:
                    continue
                datos[tr] = {"P24": float(p24_str), "P1h": float(p1h_str)}
            except ValueError:
                print("  ⚠ Valor inválido, omitiendo este periodo.")

        if len(datos) < 2:
            print("\n⚠ Se necesitan al menos 2 periodos. Usando datos de ejemplo.")
            datos = {
                2: {"P24": 55.0, "P1h": 24.0},
                5: {"P24": 72.0, "P1h": 32.0},
                10: {"P24": 84.0, "P1h": 38.0},
                25: {"P24": 100.0, "P1h": 46.0},
                50: {"P24": 112.0, "P1h": 52.0},
                100: {"P24": 124.0, "P1h": 58.0},
            }

    return datos


# ─────────────────────────────────────────────
#  2. CÁLCULO DE INTENSIDADES — MÉTODO DE BELL
# ─────────────────────────────────────────────
def calcular_intensidades(datos, duraciones=None):
    """
    Fórmula de Bell (1969):
        Pt,T = (0.54 * t^0.25 - 0.50) * P60,T

    Donde:
        t     = duración en minutos (5 ≤ t ≤ 120)
        P60,T = precipitación en 60 min para TR dado
        P60,T se estima como: P60,T = P1h directamente (dato ingresado)

    Intensidad: I = P / t  [mm/min] → convertir a mm/h multiplicando x60
    """
    if duraciones is None:
        duraciones = [5, 10, 15, 20, 30, 40, 60, 90, 120, 180, 240, 360, 720, 1440]

    resultados = {}

    for tr, vals in datos.items():
        P60 = vals["P1h"]  # Precipitación a 60 min = dato P1h ingresado
        P24 = vals["P24"]

        intensidades = []
        precipitaciones = []

        for t in duraciones:
            if t <= 120:
                # Fórmula de Bell para t ≤ 120 min
                Pt = (0.54 * (t**0.25) - 0.50) * P60
            else:
                # Para duraciones largas: interpolación con P24
                # Usando relación potencial entre P60 y P24
                # Pt = P60 * (t/60)^n  donde n = log(P24/P60)/log(1440/60)
                n = np.log(P24 / P60) / np.log(1440 / 60)
                Pt = P60 * (t / 60) ** n

            Pt = max(Pt, 0.1)  # mínimo físico
            I_mm_h = (Pt / t) * 60  # intensidad en mm/h

            intensidades.append(round(I_mm_h, 2))
            precipitaciones.append(round(Pt, 2))

        resultados[tr] = {
            "duraciones": duraciones,
            "intensidades": intensidades,
            "precipitaciones": precipitaciones,
        }

    return resultados


# ─────────────────────────────────────────────
#  3. AJUSTE DE CURVA IDF  I = a / (t + b)^c
# ─────────────────────────────────────────────
def ajustar_idf(resultados):
    """
    Ajusta la ecuación de Sherman:  I = a / (t + b)^c
    Simplificado: I = K / t^n  (b=0, más simple para preliminar)
    """
    from scipy.optimize import curve_fit

    def modelo(t, K, n):
        return K / (t**n)

    ajustes = {}
    for tr, vals in resultados.items():
        t_arr = np.array(vals["duraciones"], dtype=float)
        I_arr = np.array(vals["intensidades"], dtype=float)
        try:
            popt, _ = curve_fit(modelo, t_arr, I_arr, p0=[500, 0.6], maxfev=5000)
            ajustes[tr] = {"K": popt[0], "n": popt[1]}
        except Exception:
            # Regresión manual en log-log
            log_t = np.log(t_arr)
            log_I = np.log(I_arr)
            n_fit = -np.polyfit(log_t, log_I, 1)[0]
            K_fit = np.exp(np.mean(log_I + n_fit * log_t))
            ajustes[tr] = {"K": K_fit, "n": n_fit}

    return ajustes


# ─────────────────────────────────────────────
#  4. HIETOGRAMA — BLOQUES ALTERNOS
# ─────────────────────────────────────────────
def calcular_hietograma(
    datos, tr_seleccionados=None, dt_min=10, duracion_total_min=120
):
    """
    Método de los Bloques Alternos:
    1. Calcular precipitaciones acumuladas Pt para t = dt, 2dt, 3dt, ...
    2. Obtener incrementos ΔP = P(t) - P(t-dt)
    3. Reordenar: pico en centro, alternando mayor-menor a los lados
    """
    if tr_seleccionados is None:
        tr_seleccionados = list(datos.keys())

    hietogramas = {}
    n_intervalos = duracion_total_min // dt_min
    tiempos = [dt_min * (i + 1) for i in range(n_intervalos)]

    for tr in tr_seleccionados:
        if tr not in datos:
            continue

        P60 = datos[tr]["P1h"]
        P24 = datos[tr]["P24"]

        # Precipitación acumulada en cada intervalo
        Pt_acum = []
        for t in tiempos:
            if t <= 120:
                Pt = (0.54 * (t**0.25) - 0.50) * P60
            else:
                n = np.log(P24 / P60) / np.log(1440 / 60)
                Pt = P60 * (t / 60) ** n
            Pt_acum.append(max(Pt, 0.0))

        # Incrementos
        incrementos = [Pt_acum[0]] + [
            Pt_acum[i] - Pt_acum[i - 1] for i in range(1, n_intervalos)
        ]
        incrementos_sorted = sorted(incrementos, reverse=True)

        # Reordenamiento: pico al centro
        bloques = np.zeros(n_intervalos)
        izq = n_intervalos // 2 - 1
        der = n_intervalos // 2
        for i, val in enumerate(incrementos_sorted):
            if i % 2 == 0:
                bloques[der] = val
                der += 1
            else:
                bloques[izq] = val
                izq -= 1
            if izq < 0 or der >= n_intervalos:
                # Llenar resto
                for j, v in enumerate(incrementos_sorted[i + 1 :], start=i + 1):
                    if der < n_intervalos:
                        bloques[der] = v
                        der += 1
                    elif izq >= 0:
                        bloques[izq] = v
                        izq -= 1
                break

        hietogramas[tr] = {
            "tiempos_inicio": [dt_min * i for i in range(n_intervalos)],
            "intensidades": [b / (dt_min / 60) for b in bloques],  # mm/h
            "precipitaciones": list(bloques),
            "dt": dt_min,
        }

    return hietogramas


# ─────────────────────────────────────────────
#  5. TABLA DE RESULTADOS
# ─────────────────────────────────────────────
def imprimir_tabla(resultados):
    print("\n" + "=" * 80)
    print("  TABLA DE INTENSIDADES (mm/h)")
    print("=" * 80)

    periodos = sorted(resultados.keys())
    durs = resultados[periodos[0]]["duraciones"]

    # Encabezado
    header = f"{'Duración':>10}" + "".join(f"  TR={tr:>4}a" for tr in periodos)
    print(header)
    print("-" * len(header))

    for i, d in enumerate(durs):
        if d < 60:
            dur_str = f"{d} min"
        elif d == 60:
            dur_str = "1 h"
        elif d < 1440:
            dur_str = f"{d//60} h"
        else:
            dur_str = "24 h"

        row = f"{dur_str:>10}"
        for tr in periodos:
            row += f"  {resultados[tr]['intensidades'][i]:>8.2f}"
        print(row)

    print("\n" + "=" * 80)
    print("  TABLA DE PRECIPITACIONES (mm)")
    print("=" * 80)
    print(header)
    print("-" * len(header))

    for i, d in enumerate(durs):
        if d < 60:
            dur_str = f"{d} min"
        elif d == 60:
            dur_str = "1 h"
        elif d < 1440:
            dur_str = f"{d//60} h"
        else:
            dur_str = "24 h"

        row = f"{dur_str:>10}"
        for tr in periodos:
            row += f"  {resultados[tr]['precipitaciones'][i]:>8.2f}"
        print(row)

    print()


# ─────────────────────────────────────────────
#  6. GRAFICACIÓN
# ─────────────────────────────────────────────
def graficar_todo(resultados, ajustes, hietogramas, datos):
    periodos = sorted(resultados.keys())
    n_tr = len(periodos)

    # Layout: curvas IDF | hietogramas en grid
    n_hiet_cols = min(3, n_tr)
    n_hiet_rows = int(np.ceil(n_tr / n_hiet_cols))

    fig = plt.figure(figsize=(16, 10))
    fig.patch.set_facecolor("#F8F9FA")

    gs_top = gridspec.GridSpec(
        1, 2, figure=fig, top=0.93, bottom=0.55, left=0.06, right=0.97, wspace=0.35
    )
    gs_bot = gridspec.GridSpec(
        n_hiet_rows,
        n_hiet_cols,
        figure=fig,
        top=0.46,
        bottom=0.06,
        left=0.06,
        right=0.97,
        wspace=0.35,
        hspace=0.5,
    )

    # ── 6a. Curvas IDF (escala log-log) ──────────────────────────
    ax1 = fig.add_subplot(gs_top[0, 0])
    ax1.set_facecolor("#FFFFFF")

    t_cont = np.logspace(np.log10(5), np.log10(1440), 200)

    for idx, tr in enumerate(periodos):
        color = COLORES[idx % len(COLORES)]
        # Puntos calculados
        ax1.scatter(
            resultados[tr]["duraciones"],
            resultados[tr]["intensidades"],
            color=color,
            s=20,
            zorder=5,
        )
        # Curva ajustada
        K, n = ajustes[tr]["K"], ajustes[tr]["n"]
        I_fit = K / (t_cont**n)
        ax1.plot(t_cont, I_fit, color=color, linewidth=1.5, label=f"TR = {tr} años")

    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.set_xlabel("Duración (min)")
    ax1.set_ylabel("Intensidad (mm/h)")
    ax1.set_title("Curvas IDF  —  I = K / tⁿ", fontweight="bold")
    ax1.legend(loc="upper right", framealpha=0.8)
    ax1.grid(True, which="both", linestyle="--", alpha=0.4)
    ax1.set_xlim(5, 1500)

    # ── 6b. Curvas P-D-F (precipitación vs duración) ─────────────
    ax2 = fig.add_subplot(gs_top[0, 1])
    ax2.set_facecolor("#FFFFFF")

    for idx, tr in enumerate(periodos):
        color = COLORES[idx % len(COLORES)]
        ax2.plot(
            resultados[tr]["duraciones"],
            resultados[tr]["precipitaciones"],
            color=color,
            linewidth=1.8,
            marker="o",
            markersize=3,
            label=f"TR = {tr} años",
        )

    ax2.set_xlabel("Duración (min)")
    ax2.set_ylabel("Precipitación (mm)")
    ax2.set_title("Curvas Precipitación–Duración–Frecuencia (PDF)", fontweight="bold")
    ax2.legend(loc="upper left", framealpha=0.8)
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.set_xscale("log")
    ax2.set_xlim(5, 1500)

    # ── 6c. Hietogramas por periodo de retorno ────────────────────
    for idx, tr in enumerate(periodos):
        row = idx // n_hiet_cols
        col = idx % n_hiet_cols
        ax = fig.add_subplot(gs_bot[row, col])
        ax.set_facecolor("#FFFFFF")

        if tr in hietogramas:
            h = hietogramas[tr]
            dt = h["dt"]
            tiempos = h["tiempos_inicio"]
            intensidades = h["intensidades"]

            ax.bar(
                tiempos,
                intensidades,
                width=dt * 0.85,
                align="edge",
                color=COLORES[idx % len(COLORES)],
                alpha=0.75,
                edgecolor="white",
                linewidth=0.5,
            )

            ax.set_title(f"Hietograma TR = {tr} años", fontweight="bold")
            ax.set_xlabel("Tiempo (min)")
            ax.set_ylabel("I (mm/h)")
            ax.grid(True, axis="y", linestyle="--", alpha=0.4)
            ax.set_xlim(0, max(tiempos) + dt)

            # Anotar precipitación total
            P_total = sum(h["precipitaciones"])
            ax.text(
                0.97,
                0.95,
                f"P = {P_total:.1f} mm",
                transform=ax.transAxes,
                ha="right",
                va="top",
                fontsize=7.5,
                color="#333333",
                bbox=dict(boxstyle="round,pad=0.3", fc="#EEF2F7", ec="none"),
            )

    # Ocultar subplots vacíos
    total_slots = n_hiet_rows * n_hiet_cols
    for k in range(n_tr, total_slots):
        row = k // n_hiet_cols
        col = k % n_hiet_cols
        fig.add_subplot(gs_bot[row, col]).set_visible(False)

    # Título general
    fig.suptitle(
        "ANÁLISIS HIDROLÓGICO PRELIMINAR — Curvas IDF y Hietogramas\n"
        "Método de Bell (1969) · Hietograma de Bloques Alternos",
        fontsize=11,
        fontweight="bold",
        color="#1A1A2E",
        y=0.98,
    )

    plt.savefig(
        "curvas_idf.png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor()
    )
    print("📊 Gráfica guardada: curvas_idf.png")
    plt.show()


# ─────────────────────────────────────────────
#  7. EXPORTAR TABLA A CSV
# ─────────────────────────────────────────────
def exportar_csv(resultados):
    periodos = sorted(resultados.keys())
    durs = resultados[periodos[0]]["duraciones"]

    rows = []
    for i, d in enumerate(durs):
        row = {"Duracion_min": d}
        for tr in periodos:
            row[f"I_TR{tr}_mmh"] = resultados[tr]["intensidades"][i]
            row[f"P_TR{tr}_mm"] = resultados[tr]["precipitaciones"][i]
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv("tabla_idf.csv", index=False)
    print("📄 Tabla exportada: tabla_idf.csv")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    # 1. Ingreso de datos
    datos = ingresar_datos()

    # 2. Calcular intensidades y precipitaciones
    print("\n⚙  Calculando curvas IDF...")
    resultados = calcular_intensidades(datos)

    # 3. Ajuste de ecuación
    print("⚙  Ajustando ecuación I = K/tⁿ...")
    ajustes = ajustar_idf(resultados)

    # 4. Imprimir parámetros del ajuste
    print("\n" + "=" * 50)
    print("  PARÁMETROS AJUSTADOS  I = K / t^n  (I en mm/h, t en min)")
    print("=" * 50)
    print(f"{'TR (años)':<12} {'K':>10} {'n':>10}")
    print("-" * 34)
    for tr in sorted(ajustes.keys()):
        print(f"{tr:<12} {ajustes[tr]['K']:>10.3f} {ajustes[tr]['n']:>10.4f}")

    # 5. Tabla de resultados
    imprimir_tabla(resultados)

    # 6. Hietogramas (bloques alternos, dt=10 min, duración=120 min)
    print("⚙  Calculando hietogramas (Bloques Alternos, dt=10 min)...")
    hietogramas = calcular_hietograma(datos, dt_min=10, duracion_total_min=120)

    # 7. Exportar CSV
    exportar_csv(resultados)

    # 8. Graficar
    print("📈 Generando gráficas...\n")
    graficar_todo(resultados, ajustes, hietogramas, datos)

    print("\n✅ Análisis completo. Archivos generados:")
    print("   • curvas_idf.png  — Gráficas IDF + hietogramas")
    print("   • tabla_idf.csv   — Tabla de intensidades y precipitaciones\n")


if __name__ == "__main__":
    main()
