# Validación de calidad de datos – AndesMercado

Parte 4 del estudio de caso *DevOps en la arquitectura de datos de AndesMercado*
(Arquitectura de Software, Universidad EAN).

Este repositorio valida el archivo de ventas **antes** de que se cargue al data
warehouse. Si alguna regla de calidad falla, el script termina con código de
salida 1 y el flujo de GitHub Actions se pone en rojo, bloqueando la carga.

## Estructura

```
validar_ventas.py              # reglas de calidad, validar(df) y script de línea de comandos
tests/test_validar_ventas.py   # pruebas con pytest
datos/ventas_anexo.csv         # datos originales del anexo (contienen el incidente)
datos/ventas_corregido.csv     # los mismos datos con los montos en pesos (válidos)
ventas.csv                     # archivo que valida el flujo de CI
.github/workflows/validar-datos.yml
requirements.txt
pytest.ini
```

## Reglas de calidad

| Función | Regla |
|---|---|
| `regla_columnas` | El archivo tiene exactamente las columnas `id_venta, fecha, canal, monto` |
| `regla_id_venta` | `id_venta` no tiene nulos ni duplicados |
| `regla_canal` | `canal` solo toma los valores `tienda` o `en_linea` |
| `regla_monto_maximo` | Ninguna venta individual supera COP 5.000.000 |
| `regla_total_diario` | El total diario por canal no supera 3 veces el promedio de los días anteriores |

`validar(df)` ejecuta todas las reglas y devuelve la lista de las que se
incumplen (lista vacía si todo está bien).

## Cómo ejecutarlo

Requiere Python 3.9 o superior.

```bash
# 1. (opcional) crear un entorno virtual
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate

# 2. instalar dependencias
pip install -r requirements.txt

# 3. correr las pruebas
pytest -v

# 4. validar un archivo de ventas
python validar_ventas.py ventas.csv
echo $?                          # 0 = datos válidos, 1 = hay reglas incumplidas
                                 # (en Windows PowerShell: echo $LASTEXITCODE)
```

## Integración continua

El flujo `.github/workflows/validar-datos.yml` se ejecuta en cada `push` y en
cada pull request:

1. Instala las dependencias.
2. Ejecuta `pytest`.
3. Ejecuta `python validar_ventas.py ventas.csv`.

Con el `ventas.csv` del anexo el último paso falla (❌) y bloquea la carga.
Con los datos corregidos (`datos/ventas_corregido.csv`) pasa (✅).

## Resultado sobre el anexo

Las reglas `regla_monto_maximo` y `regla_total_diario` detectan el incidente
del 28 de noviembre: las ventas en línea de ese día llegaron multiplicadas por
100 (columna `monto` en centavos). El error no habría llegado al tablero.
