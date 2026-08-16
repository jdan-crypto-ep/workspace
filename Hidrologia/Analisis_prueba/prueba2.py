import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. DATOS POR DEFECTO
# ==========================================
DEFAULT_DATA = {
    "Tr": [2, 5, 10, 20, 50, 100, 200, 500],
    "P_1h": [37.58, 49.57, 57.57, 65.17, 72.87, 79.89, 86.90, 98.74],
    "P_24h": [54.29, 68.745, 83.20, 94.19, 108.05, 121.41, 128.85, 146.29],
}


# ==========================================
# 2. FUNCIONES DE CÁLCULO
# ==========================================
def calculate_idf_parameters(df):
    """Calcula los parámetros 'a' y 'b' de la ecuación de Sherman simplificada."""
    df = df.copy()
    df["I_1h"] = df["P_1h"] / 1.0  # Intensidad a 1 hora (mm/h)
    df["I_24h"] = df["P_24h"] / 24.0  # Intensidad a 24 horas (mm/h)

    # a = I_1h
    df["a"] = df["I_1h"]
    # b = log(I_1h / I_24h) / log(24)
    df["b"] = np.log(df["I_1h"] / df["I_24h"]) / np.log(24)

    return df


def generate_idf_table(params_df, max_duration_min=1440):
    """Genera la tabla de intensidades cada 5 minutos."""
    durations_min = np.arange(5, max_duration_min + 1, 5)
    durations_hr = durations_min / 60.0

    table_data = {"Duracion_min": durations_min}

    for index, row in params_df.iterrows():
        tr = row["Tr"]
        a = row["a"]
        b = row["b"]
        # Ecuación IDF: I = a / t^b (t en horas)
        intensities = a / (durations_hr**b)
        table_data[f"Tr_{tr}"] = intensities

    return pd.DataFrame(table_data)


def plot_idf_curves(table_df, params_df, max_duration_plot=60):
    """Genera la gráfica IDF en escala log-log."""
    # Filtrar solo hasta la duración deseada
    table_filtered = table_df[table_df["Duracion_min"] <= max_duration_plot].copy()

    if len(table_filtered) == 0:
        print(f"Error: No hay datos hasta {max_duration_plot} minutos")
        return

    plt.figure(figsize=(12, 8))

    for index, row in params_df.iterrows():
        tr = row["Tr"]
        plt.plot(
            table_filtered["Duracion_min"],
            table_filtered[f"Tr_{tr}"],
            marker=".",
            linestyle="-",
            linewidth=2,
            label=f"Tr = {tr} años",
        )

    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Duración (minutos)", fontsize=12)
    plt.ylabel("Intensidad (mm/h)", fontsize=12)
    plt.title(
        f"Curvas IDF - Método Sherman Simplificado\n(Duración: 5 - {max_duration_plot} minutos)",
        fontsize=14,
        fontweight="bold",
    )
    plt.legend(title="Período de Retorno", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.tight_layout()
    plt.show()


def estimate_return_period(params_df, table_df, duration_min, rain_mm):
    """Estima el Periodo de Retorno basado en un evento real."""
    duration_hr = duration_min / 60.0
    intensity_real = rain_mm / duration_hr

    print(f"\n{'='*50}")
    print(f"--- Análisis de Evento Real ---")
    print(f"{'='*50}")
    print(f"Duración: {duration_min} min")
    print(f"Lluvia acumulada: {rain_mm} mm")
    print(f"Intensidad real calculada: {intensity_real:.2f} mm/h\n")

    # Buscar la fila de la duración en la tabla
    row_idx = table_df[table_df["Duracion_min"] == duration_min].index
    if len(row_idx) == 0:
        # Si no es múltiplo exacto de 5, usar el más cercano
        closest_min = table_df.loc[
            (table_df["Duracion_min"] - duration_min).abs().idxmin(), "Duracion_min"
        ]
        row_idx = table_df[table_df["Duracion_min"] == closest_min].index
        print(
            f"(Nota: Se usó la duración más cercana de la tabla: {int(closest_min)} min)"
        )

    tr_columns = [col for col in table_df.columns if col.startswith("Tr_")]
    design_intensities = table_df.loc[row_idx[0], tr_columns].values
    tr_values = [int(col.split("_")[1]) for col in tr_columns]

    print("Comparación con intensidades de diseño:")
    print(f"{'Tr (años)':<12} {'Intensidad (mm/h)':<20}")
    print("-" * 32)
    for tr, intensity in zip(tr_values, design_intensities):
        print(f"{tr:<12} {intensity:>15.2f}")

    # Encontrar el Tr más cercano
    diffs = np.abs(design_intensities - intensity_real)
    closest_idx = np.argmin(diffs)
    estimated_tr = tr_values[closest_idx]

    print(f"\n{'='*50}")
    print(f"RESULTADO:")
    print(f"{'='*50}")
    print(f"Intensidad real: {intensity_real:.2f} mm/h")
    print(
        f"Intensidad de diseño más cercana: {design_intensities[closest_idx]:.2f} mm/h (Tr = {estimated_tr} años)"
    )
    print(f"\n👉 El Período de Retorno estimado es: Tr = {estimated_tr} años")

    # Clasificación de alerta
    if estimated_tr <= 5:
        print("Estado: ✓ NORMAL")
    elif estimated_tr <= 20:
        print("Estado: ⚠️ MODERADO")
    elif estimated_tr <= 100:
        print("Estado: ⚠️ ALTO")
    else:
        print("Estado: 🚨 CRÍTICO")
    print(f"{'='*50}\n")


# ==========================================
# 3. INTERFAZ DE USUARIO (CLI)
# ==========================================
def main():
    print("=" * 60)
    print("   SISTEMA DE CÁLCULO Y MONITOREO IDF")
    print("   Método Sherman Simplificado")
    print("=" * 60)

    # Selección de datos
    while True:
        use_default = input("\n¿Usar datos predeterminados? (s/n): ").strip().lower()
        if use_default in ["s", "n"]:
            break
        print("Por favor ingrese 's' para sí o 'n' para no")

    if use_default == "s":
        df = pd.DataFrame(DEFAULT_DATA)
        print("\n✓ Se cargaron los datos predeterminados.")
    else:
        print("\n" + "=" * 60)
        print("Ingrese los datos manualmente")
        print("(Presione Enter sin escribir nada en 'Tr' para terminar)")
        print("=" * 60)
        tr_list, p1_list, p24_list = [], [], []
        i = 1
        while True:
            try:
                print(f"\nRegistro {i}:")
                tr_input = input("  Período de Retorno (años): ").strip()
                if tr_input == "":
                    if len(tr_list) == 0:
                        print("  Error: Debe ingresar al menos un registro")
                        continue
                    break

                tr = int(tr_input)
                p1 = float(input("  Lluvia 1h (mm): ").strip())
                p24 = float(input("  Lluvia 24h (mm): ").strip())

                if tr in tr_list:
                    print(f"  Advertencia: Tr={tr} ya existe, se actualizará")
                    idx = tr_list.index(tr)
                    p1_list[idx] = p1
                    p24_list[idx] = p24
                else:
                    tr_list.append(tr)
                    p1_list.append(p1)
                    p24_list.append(p24)
                    i += 1

            except ValueError:
                print("  ERROR: Ingrese valores numéricos válidos")
            except KeyboardInterrupt:
                print("\n\nEntrada cancelada por el usuario")
                if len(tr_list) == 0:
                    return
                break

        df = pd.DataFrame({"Tr": tr_list, "P_1h": p1_list, "P_24h": p24_list})
        df = df.sort_values("Tr").reset_index(drop=True)

    # Mostrar datos cargados
    print("\n" + "=" * 60)
    print("Datos cargados:")
    print("=" * 60)
    print(df.to_string(index=False))

    # Cálculos
    print("\nCalculando parámetros IDF...")
    params_df = calculate_idf_parameters(df)
    print("\nParámetros calculados (a y b):")
    print(params_df[["Tr", "a", "b"]].to_string(index=False))

    # Generar tabla
    print("\nGenerando tabla de intensidades cada 5 minutos...")
    table_df = generate_idf_table(params_df, max_duration_min=1440)

    # Guardar tabla en CSV
    csv_filename = "tabla_idf_5min.csv"
    table_df.to_csv(csv_filename, index=False, decimal=",", sep=";")
    print(f"\n✓ Tabla guardada exitosamente en '{csv_filename}'")

    # Mostrar primeras filas de la tabla
    print("\nVista previa de la tabla (primeras 5 duraciones):")
    print(table_df.head().to_string(index=False))

    # Gráfica
    while True:
        plot_choice = input("\n¿Desea generar la gráfica IDF? (s/n): ").strip().lower()
        if plot_choice in ["s", "n"]:
            break
        print("Por favor ingrese 's' o 'n'")

    if plot_choice == "s":
        # Preguntar el rango de la gráfica
        while True:
            try:
                max_dur = input(
                    "\nDuración máxima para la gráfica en minutos (default=60): "
                ).strip()
                if max_dur == "":
                    max_dur = 60
                else:
                    max_dur = int(max_dur)
                if max_dur < 5:
                    print("La duración mínima es 5 minutos")
                    continue
                break
            except ValueError:
                print("Por favor ingrese un número válido")

        plot_idf_curves(table_df, params_df, max_duration_plot=max_dur)

    # Herramienta de Monitoreo
    while True:
        monitor_choice = (
            input("\n¿Desea estimar el Tr de un evento de lluvia real? (s/n): ")
            .strip()
            .lower()
        )
        if monitor_choice in ["s", "n"]:
            break
        print("Por favor ingrese 's' o 'n'")

    if monitor_choice == "s":
        while True:
            try:
                print("\n" + "-" * 50)
                dur_input = input(
                    "Duración del evento en minutos (o 'salir' para terminar): "
                ).strip()
                if dur_input.lower() == "salir":
                    break

                dur = float(dur_input)
                if dur < 5:
                    print("Error: La duración mínima es 5 minutos")
                    continue

                rain = float(input("Lluvia acumulada en ese tiempo (mm): ").strip())
                if rain < 0:
                    print("Error: La lluvia no puede ser negativa")
                    continue

                estimate_return_period(params_df, table_df, dur, rain)

            except ValueError:
                print("ERROR: Ingrese valores numéricos válidos")
            except KeyboardInterrupt:
                print("\n\nSaliendo del modo monitoreo...")
                break

    print("\n" + "=" * 60)
    print("¡Proceso finalizado!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPrograma cancelado por el usuario")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        import traceback

        traceback.print_exc()
