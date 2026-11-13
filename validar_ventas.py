"""Validaciones de calidad de datos para las ventas de AndesMercado.

Cada regla es una función que recibe un DataFrame y devuelve una lista de
mensajes de error. Si la lista está vacía, la regla se cumple.

Uso desde la terminal:
    python validar_ventas.py ventas.csv

El script termina con código de salida 0 si todo está bien y con código 1 si
alguna regla falla (así bloquea la carga y hace fallar el flujo de CI).
"""

import sys

import pandas as pd

COLUMNAS_ESPERADAS = ["id_venta", "fecha", "canal", "monto"]
CANALES_VALIDOS = {"tienda", "en_linea"}
MONTO_MAXIMO = 5_000_000  # COP, regla de negocio de AndesMercado
FACTOR_TOTAL_DIARIO = 3  # el total diario no puede superar 3x el promedio previo


def regla_columnas(df):
    """El archivo tiene exactamente las columnas id_venta, fecha, canal y monto."""
    if list(df.columns) != COLUMNAS_ESPERADAS:
        return [
            f"columnas esperadas {COLUMNAS_ESPERADAS}, "
            f"pero llegaron {list(df.columns)}"
        ]
    return []


def regla_id_venta(df):
    """id_venta no tiene nulos ni duplicados."""
    errores = []
    nulos = int(df["id_venta"].isna().sum())
    if nulos:
        errores.append(f"id_venta tiene {nulos} valor(es) nulo(s)")
    duplicados = df.loc[df["id_venta"].notna(), "id_venta"]
    repetidos = sorted(duplicados[duplicados.duplicated()].unique())
    if repetidos:
        errores.append(f"id_venta tiene duplicados: {repetidos}")
    return errores


def regla_canal(df):
    """canal solo toma los valores tienda o en_linea."""
    invalidos = df.loc[~df["canal"].isin(CANALES_VALIDOS), "canal"]
    if len(invalidos):
        valores = sorted(invalidos.astype(str).unique())
        return [f"canal con valores no permitidos: {valores}"]
    return []


def regla_monto_maximo(df):
    """Ninguna venta individual supera COP 5.000.000."""
    montos = pd.to_numeric(df["monto"], errors="coerce")
    excedidas = df.loc[montos > MONTO_MAXIMO, "id_venta"].tolist()
    if excedidas:
        return [
            f"{len(excedidas)} venta(s) superan COP {MONTO_MAXIMO:,}: "
            f"id_venta {excedidas}"
        ]
    return []


def regla_total_diario(df):
    """El total diario por canal no supera 3 veces el promedio de los días anteriores."""
    datos = df.copy()
    datos["monto"] = pd.to_numeric(datos["monto"], errors="coerce")
    datos["fecha"] = pd.to_datetime(datos["fecha"], errors="coerce")
    datos = datos.dropna(subset=["monto", "fecha"])

    errores = []
    totales = datos.groupby(["canal", "fecha"])["monto"].sum().reset_index()
    for canal, grupo in totales.groupby("canal"):
        grupo = grupo.sort_values("fecha").reset_index(drop=True)
        for i in range(1, len(grupo)):  # el primer día no tiene historial
            promedio_previo = grupo.loc[: i - 1, "monto"].mean()
            total = grupo.loc[i, "monto"]
            if total > FACTOR_TOTAL_DIARIO * promedio_previo:
                dia = grupo.loc[i, "fecha"].date()
                errores.append(
                    f"canal '{canal}' el {dia}: total {total:,.2f} supera "
                    f"{FACTOR_TOTAL_DIARIO}x el promedio previo "
                    f"({promedio_previo:,.2f})"
                )
    return errores


# Reglas en el orden en que se ejecutan.
REGLAS = [
    regla_columnas,
    regla_id_venta,
    regla_canal,
    regla_monto_maximo,
    regla_total_diario,
]


def validar(df):
    """Devuelve la lista de reglas incumplidas (vacía si todo está bien).

    Cada elemento tiene el formato "nombre_de_la_regla: detalle".
    """
    # Sin las columnas correctas las demás reglas no pueden ejecutarse.
    errores_columnas = regla_columnas(df)
    if errores_columnas:
        return [f"regla_columnas: {e}" for e in errores_columnas]

    incumplidas = []
    for regla in REGLAS[1:]:
        for detalle in regla(df):
            incumplidas.append(f"{regla.__name__}: {detalle}")
    return incumplidas


def cargar(ruta):
    """Lee el CSV tal como llega (todo como texto, sin convertir nada)."""
    return pd.read_csv(ruta, dtype=str)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ruta = argv[0] if argv else "ventas.csv"

    df = cargar(ruta)
    incumplidas = validar(df)

    if incumplidas:
        print(f"VALIDACIÓN FALLIDA para {ruta}: {len(incumplidas)} problema(s)")
        for linea in incumplidas:
            print(f"  - {linea}")
        return 1

    print(f"VALIDACIÓN EXITOSA para {ruta}: todas las reglas se cumplen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
