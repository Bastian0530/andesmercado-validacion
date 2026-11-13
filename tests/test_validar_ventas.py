"""Pruebas de las reglas de calidad de datos de ventas.

Para cada regla hay al menos un caso válido que pasa y uno inválido que falla.
"""

from pathlib import Path

import pandas as pd
import pytest

import validar_ventas as vv

DATOS = Path(__file__).parent.parent / "datos"


@pytest.fixture
def df_valido():
    """Tres días de ventas normales en ambos canales."""
    return pd.DataFrame(
        {
            "id_venta": ["1", "2", "3", "4", "5", "6"],
            "fecha": [
                "2025-11-25",
                "2025-11-25",
                "2025-11-26",
                "2025-11-26",
                "2025-11-27",
                "2025-11-27",
            ],
            "canal": ["tienda", "en_linea"] * 3,
            "monto": ["100000", "200000", "110000", "190000", "120000", "210000"],
        }
    )


# ---------- datos válidos ----------


def test_datos_validos_pasan_todas_las_reglas(df_valido):
    assert vv.validar(df_valido) == []


# ---------- regla 1: columnas ----------


def test_columnas_correctas_pasan(df_valido):
    assert vv.regla_columnas(df_valido) == []


def test_columnas_faltantes_fallan(df_valido):
    assert vv.regla_columnas(df_valido.drop(columns=["canal"]))


def test_columna_extra_falla(df_valido):
    df_valido["descuento"] = "0"
    assert vv.regla_columnas(df_valido)


def test_columnas_en_otro_orden_fallan(df_valido):
    assert vv.regla_columnas(df_valido[["fecha", "id_venta", "canal", "monto"]])


# ---------- regla 2: id_venta ----------


def test_id_venta_valido_pasa(df_valido):
    assert vv.regla_id_venta(df_valido) == []


def test_id_venta_nulo_falla(df_valido):
    df_valido.loc[0, "id_venta"] = None
    assert vv.regla_id_venta(df_valido)


def test_id_venta_duplicado_falla(df_valido):
    df_valido.loc[1, "id_venta"] = "1"
    assert vv.regla_id_venta(df_valido)


# ---------- regla 3: canal ----------


def test_canal_valido_pasa(df_valido):
    assert vv.regla_canal(df_valido) == []


def test_canal_invalido_falla(df_valido):
    df_valido.loc[0, "canal"] = "telefono"
    assert vv.regla_canal(df_valido)


def test_canal_nulo_falla(df_valido):
    df_valido.loc[0, "canal"] = None
    assert vv.regla_canal(df_valido)


# ---------- regla 4: monto máximo ----------


def test_monto_en_el_limite_pasa(df_valido):
    df_valido.loc[0, "monto"] = "5000000"
    assert vv.regla_monto_maximo(df_valido) == []


def test_monto_sobre_el_limite_falla(df_valido):
    df_valido.loc[0, "monto"] = "5000001"
    assert vv.regla_monto_maximo(df_valido)


# ---------- regla 5: total diario ----------


def test_total_diario_normal_pasa(df_valido):
    assert vv.regla_total_diario(df_valido) == []


def test_total_diario_disparado_falla(df_valido):
    # El 27 las ventas en línea suben a 10x lo normal (sin superar los 5M por venta).
    df_valido.loc[5, "monto"] = "2100000"
    errores = vv.regla_total_diario(df_valido)
    assert errores
    assert "en_linea" in errores[0]


def test_total_diario_no_cuenta_otro_canal(df_valido):
    # Una subida en tienda no debe marcar en_linea.
    df_valido.loc[4, "monto"] = "1200000"
    errores = vv.regla_total_diario(df_valido)
    assert errores and all("tienda" in e for e in errores)


# ---------- validar() y el incidente real ----------


def test_validar_reporta_el_nombre_de_la_regla(df_valido):
    df_valido.loc[0, "canal"] = "telefono"
    resultado = vv.validar(df_valido)
    assert any(r.startswith("regla_canal") for r in resultado)


def test_validar_detecta_el_incidente_del_anexo():
    df = vv.cargar(DATOS / "ventas_anexo.csv")
    resultado = vv.validar(df)
    reglas = {r.split(":")[0] for r in resultado}
    assert "regla_monto_maximo" in reglas
    assert "regla_total_diario" in reglas


def test_validar_acepta_los_datos_corregidos():
    df = vv.cargar(DATOS / "ventas_corregido.csv")
    assert vv.validar(df) == []


# ---------- script: código de salida ----------


def test_main_devuelve_1_con_datos_invalidos():
    assert vv.main([str(DATOS / "ventas_anexo.csv")]) == 1


def test_main_devuelve_0_con_datos_validos():
    assert vv.main([str(DATOS / "ventas_corregido.csv")]) == 0
