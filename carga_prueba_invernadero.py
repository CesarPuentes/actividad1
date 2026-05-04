#!/usr/bin/env python3
"""
Evidencia de Aprendizaje 1 — Carga de Prueba de la Base de Datos
Sistema de Automatización de Cuidado de Plantas en Invernadero con Raspberry Pi

Este script implementa:
  1. Creación del esquema de base de datos en SQLite.
  2. Inserción de datos de prueba (cultivos, zonas, lecturas, eventos de riego, alertas).
  3. Consultas de verificación para validar la integridad del modelo de datos.
"""

import sqlite3
import random
import os
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "invernadero.db")
DIAS_SIMULADOS = 7        # Días de datos de prueba
INTERVALO_MINUTOS = 5     # Intervalo entre lecturas de sensores

random.seed(42)  # Reproducibilidad


# ─────────────────────────────────────────────
# 1. Creación del esquema de base de datos
# ─────────────────────────────────────────────
SCHEMA_SQL = """
-- Tabla de cultivos: define los parámetros óptimos para cada tipo de planta
CREATE TABLE IF NOT EXISTS cultivos (
    cultivo_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre              TEXT    NOT NULL UNIQUE,
    temp_min            REAL    NOT NULL,  -- Temperatura mínima óptima (°C)
    temp_max            REAL    NOT NULL,  -- Temperatura máxima óptima (°C)
    humedad_suelo_min   REAL    NOT NULL,  -- Humedad de suelo mínima para activar riego (%)
    humedad_suelo_max   REAL    NOT NULL,  -- Humedad de suelo máxima ideal (%)
    luminosidad_min     REAL    NOT NULL,  -- Luminosidad mínima recomendada (lux)
    luminosidad_max     REAL    NOT NULL,  -- Luminosidad máxima tolerada (lux)
    duracion_riego_seg  INTEGER NOT NULL   -- Duración del riego automático (segundos)
);

-- Tabla de zonas: cada zona del invernadero con un cultivo asignado
CREATE TABLE IF NOT EXISTS zonas (
    zona_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT    NOT NULL UNIQUE,
    ubicacion   TEXT    NOT NULL,
    area_m2     REAL    NOT NULL,
    cultivo_id  INTEGER NOT NULL,
    FOREIGN KEY (cultivo_id) REFERENCES cultivos(cultivo_id)
);

-- Tabla de lecturas de sensores: registro histórico de datos ambientales
CREATE TABLE IF NOT EXISTS lecturas_sensores (
    lectura_id       INTEGER  PRIMARY KEY AUTOINCREMENT,
    zona_id          INTEGER  NOT NULL,
    timestamp        DATETIME NOT NULL,
    temperatura      REAL,     -- °C
    humedad_relativa REAL,     -- %
    luminosidad      REAL,     -- lux
    humedad_suelo    REAL,     -- %
    FOREIGN KEY (zona_id) REFERENCES zonas(zona_id),
    UNIQUE(zona_id, timestamp)  -- Evitar duplicados
);

-- Tabla de eventos de riego: registra cada activación del sistema de riego
CREATE TABLE IF NOT EXISTS eventos_riego (
    evento_id        INTEGER  PRIMARY KEY AUTOINCREMENT,
    zona_id          INTEGER  NOT NULL,
    timestamp_inicio DATETIME NOT NULL,
    timestamp_fin    DATETIME NOT NULL,
    duracion_seg     INTEGER  NOT NULL,
    humedad_antes    REAL,
    humedad_despues  REAL,
    tipo             TEXT     NOT NULL CHECK(tipo IN ('automatico', 'manual')),
    FOREIGN KEY (zona_id) REFERENCES zonas(zona_id)
);

-- Tabla de alertas: registra condiciones críticas detectadas
CREATE TABLE IF NOT EXISTS alertas (
    alerta_id       INTEGER  PRIMARY KEY AUTOINCREMENT,
    zona_id         INTEGER  NOT NULL,
    timestamp       DATETIME NOT NULL,
    tipo_alerta     TEXT     NOT NULL CHECK(tipo_alerta IN (
                        'temperatura_alta', 'temperatura_baja',
                        'humedad_baja', 'sensor_fallo'
                    )),
    valor_detectado REAL,
    umbral          REAL,
    mensaje         TEXT,
    notificada      BOOLEAN  NOT NULL DEFAULT 0,
    FOREIGN KEY (zona_id) REFERENCES zonas(zona_id)
);

-- Índices para optimizar consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_lecturas_zona_ts
    ON lecturas_sensores(zona_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_eventos_zona_ts
    ON eventos_riego(zona_id, timestamp_inicio);

CREATE INDEX IF NOT EXISTS idx_alertas_zona_ts
    ON alertas(zona_id, timestamp);
"""


def crear_esquema(conn: sqlite3.Connection) -> None:
    """Crea todas las tablas e índices del esquema."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    print("[✓] Esquema de base de datos creado correctamente.")


# ─────────────────────────────────────────────
# 2. Inserción de datos de prueba
# ─────────────────────────────────────────────

# Datos de cultivos con parámetros reales aproximados
CULTIVOS = [
    {
        "nombre": "Tomate",
        "temp_min": 18.0, "temp_max": 30.0,
        "humedad_suelo_min": 40.0, "humedad_suelo_max": 70.0,
        "luminosidad_min": 8000.0, "luminosidad_max": 40000.0,
        "duracion_riego_seg": 300,
    },
    {
        "nombre": "Lechuga",
        "temp_min": 12.0, "temp_max": 24.0,
        "humedad_suelo_min": 50.0, "humedad_suelo_max": 80.0,
        "luminosidad_min": 5000.0, "luminosidad_max": 25000.0,
        "duracion_riego_seg": 180,
    },
    {
        "nombre": "Fresa",
        "temp_min": 15.0, "temp_max": 26.0,
        "humedad_suelo_min": 45.0, "humedad_suelo_max": 75.0,
        "luminosidad_min": 6000.0, "luminosidad_max": 35000.0,
        "duracion_riego_seg": 240,
    },
]

# Configuración de zonas del invernadero
ZONAS = [
    {"nombre": "Zona A - Norte", "ubicacion": "Sector norte, hileras 1-5",   "area_m2": 120.0, "cultivo": "Tomate"},
    {"nombre": "Zona B - Sur",   "ubicacion": "Sector sur, hileras 6-10",   "area_m2": 130.0, "cultivo": "Lechuga"},
    {"nombre": "Zona C - Este",  "ubicacion": "Sector este, hileras 11-14", "area_m2": 110.0, "cultivo": "Fresa"},
    {"nombre": "Zona D - Oeste", "ubicacion": "Sector oeste, hileras 15-18","area_m2": 140.0, "cultivo": "Tomate"},
]


def insertar_cultivos(conn: sqlite3.Connection) -> dict:
    """Inserta los tipos de cultivo y retorna un mapeo nombre → cultivo_id."""
    cursor = conn.cursor()
    cultivo_ids = {}
    for c in CULTIVOS:
        cursor.execute(
            """INSERT OR IGNORE INTO cultivos
               (nombre, temp_min, temp_max, humedad_suelo_min, humedad_suelo_max,
                luminosidad_min, luminosidad_max, duracion_riego_seg)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (c["nombre"], c["temp_min"], c["temp_max"],
             c["humedad_suelo_min"], c["humedad_suelo_max"],
             c["luminosidad_min"], c["luminosidad_max"],
             c["duracion_riego_seg"])
        )
        cultivo_ids[c["nombre"]] = cursor.lastrowid
    conn.commit()
    print(f"[✓] {len(CULTIVOS)} cultivos insertados.")
    return cultivo_ids


def insertar_zonas(conn: sqlite3.Connection, cultivo_ids: dict) -> list:
    """Inserta las zonas del invernadero y retorna lista de (zona_id, cultivo_nombre)."""
    cursor = conn.cursor()
    zonas_info = []
    for z in ZONAS:
        cursor.execute(
            """INSERT OR IGNORE INTO zonas (nombre, ubicacion, area_m2, cultivo_id)
               VALUES (?, ?, ?, ?)""",
            (z["nombre"], z["ubicacion"], z["area_m2"], cultivo_ids[z["cultivo"]])
        )
        zonas_info.append((cursor.lastrowid, z["cultivo"]))
    conn.commit()
    print(f"[✓] {len(ZONAS)} zonas insertadas.")
    return zonas_info


def generar_valor_sensor(media: float, desviacion: float, minimo: float, maximo: float) -> float:
    """Genera un valor simulado con distribución normal acotado a un rango."""
    valor = random.gauss(media, desviacion)
    return round(max(minimo, min(maximo, valor)), 2)


def simular_ciclo_diurno(hora: int) -> dict:
    """Ajusta parámetros de simulación según la hora del día (ciclo diurno)."""
    if 6 <= hora < 10:       # Mañana
        return {"temp_base": 20.0, "luz_base": 15000, "hum_rel": 70}
    elif 10 <= hora < 14:    # Mediodía
        return {"temp_base": 28.0, "luz_base": 35000, "hum_rel": 55}
    elif 14 <= hora < 18:    # Tarde
        return {"temp_base": 26.0, "luz_base": 20000, "hum_rel": 60}
    elif 18 <= hora < 22:    # Noche temprana
        return {"temp_base": 20.0, "luz_base": 500,   "hum_rel": 75}
    else:                    # Noche
        return {"temp_base": 16.0, "luz_base": 0,     "hum_rel": 80}


def insertar_lecturas_y_eventos(conn: sqlite3.Connection, zonas_info: list) -> tuple:
    """
    Genera lecturas de sensores simuladas y eventos de riego automático.
    Retorna (total_lecturas, total_eventos_riego, total_alertas).
    """
    cursor = conn.cursor()
    inicio = datetime.now() - timedelta(days=DIAS_SIMULADOS)
    total_lecturas = 0
    total_eventos = 0
    total_alertas = 0

    # Obtener parámetros de cultivos
    cultivos_params = {}
    for c in CULTIVOS:
        cultivos_params[c["nombre"]] = c

    # Estado de humedad del suelo por zona (simulación)
    humedad_suelo_actual = {}
    for zona_id, cultivo in zonas_info:
        params = cultivos_params[cultivo]
        humedad_suelo_actual[zona_id] = random.uniform(
            params["humedad_suelo_min"] + 10,
            params["humedad_suelo_max"]
        )

    # Generar lecturas cada INTERVALO_MINUTOS minutos
    lecturas_batch = []
    eventos_batch = []
    alertas_batch = []

    ts = inicio
    fin = datetime.now()

    while ts <= fin:
        hora = ts.hour
        ciclo = simular_ciclo_diurno(hora)

        for zona_id, cultivo in zonas_info:
            params = cultivos_params[cultivo]

            # Simular valores con variación natural
            temperatura = generar_valor_sensor(ciclo["temp_base"], 2.5, 5.0, 50.0)
            humedad_relativa = generar_valor_sensor(ciclo["hum_rel"], 5.0, 20.0, 100.0)
            luminosidad = generar_valor_sensor(ciclo["luz_base"], 3000, 0, 65535)

            # La humedad del suelo decrece gradualmente (evaporación y absorción)
            humedad_suelo_actual[zona_id] -= random.uniform(0.1, 0.5)
            humedad_suelo_actual[zona_id] = max(5.0, humedad_suelo_actual[zona_id])
            humedad_suelo = round(humedad_suelo_actual[zona_id], 2)

            # Registrar lectura
            lecturas_batch.append((
                zona_id, ts.strftime("%Y-%m-%d %H:%M:%S"),
                temperatura, humedad_relativa, luminosidad, humedad_suelo
            ))
            total_lecturas += 1

            # ¿Activar riego automático?
            if humedad_suelo < params["humedad_suelo_min"]:
                ts_fin_riego = ts + timedelta(seconds=params["duracion_riego_seg"])
                humedad_despues = round(humedad_suelo + random.uniform(15, 30), 2)
                humedad_despues = min(humedad_despues, params["humedad_suelo_max"])

                eventos_batch.append((
                    zona_id,
                    ts.strftime("%Y-%m-%d %H:%M:%S"),
                    ts_fin_riego.strftime("%Y-%m-%d %H:%M:%S"),
                    params["duracion_riego_seg"],
                    humedad_suelo,
                    humedad_despues,
                    "automatico"
                ))
                total_eventos += 1

                # Actualizar humedad del suelo post-riego
                humedad_suelo_actual[zona_id] = humedad_despues

            # ¿Generar alerta?
            if temperatura > params["temp_max"] + 3:
                alertas_batch.append((
                    zona_id, ts.strftime("%Y-%m-%d %H:%M:%S"),
                    "temperatura_alta", temperatura, params["temp_max"],
                    f"Temperatura de {temperatura}°C supera el máximo de {params['temp_max']}°C en zona {zona_id}",
                    1
                ))
                total_alertas += 1
            elif temperatura < params["temp_min"] - 3:
                alertas_batch.append((
                    zona_id, ts.strftime("%Y-%m-%d %H:%M:%S"),
                    "temperatura_baja", temperatura, params["temp_min"],
                    f"Temperatura de {temperatura}°C por debajo del mínimo de {params['temp_min']}°C en zona {zona_id}",
                    1
                ))
                total_alertas += 1

        ts += timedelta(minutes=INTERVALO_MINUTOS)

    # Inserción en lotes para mejor rendimiento
    cursor.executemany(
        """INSERT INTO lecturas_sensores
           (zona_id, timestamp, temperatura, humedad_relativa, luminosidad, humedad_suelo)
           VALUES (?, ?, ?, ?, ?, ?)""",
        lecturas_batch
    )

    cursor.executemany(
        """INSERT INTO eventos_riego
           (zona_id, timestamp_inicio, timestamp_fin, duracion_seg,
            humedad_antes, humedad_despues, tipo)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        eventos_batch
    )

    cursor.executemany(
        """INSERT INTO alertas
           (zona_id, timestamp, tipo_alerta, valor_detectado, umbral, mensaje, notificada)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        alertas_batch
    )

    conn.commit()
    print(f"[✓] {total_lecturas:,} lecturas de sensores insertadas.")
    print(f"[✓] {total_eventos:,} eventos de riego insertados.")
    print(f"[✓] {total_alertas:,} alertas insertadas.")

    return total_lecturas, total_eventos, total_alertas


# ─────────────────────────────────────────────
# 3. Consultas de verificación
# ─────────────────────────────────────────────

def ejecutar_verificaciones(conn: sqlite3.Connection) -> None:
    """Ejecuta consultas de verificación para validar la integridad de los datos."""
    cursor = conn.cursor()

    print("\n" + "=" * 70)
    print("  REPORTE DE VERIFICACIÓN DE LA BASE DE DATOS")
    print("=" * 70)

    # Conteo de registros por tabla
    print("\n Conteo de registros por tabla:")
    print("-" * 40)
    for tabla in ["cultivos", "zonas", "lecturas_sensores", "eventos_riego", "alertas"]:
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        conteo = cursor.fetchone()[0]
        print(f"   {tabla:.<30} {conteo:>6}")

    # Estadísticas de lecturas por zona
    print("\n🌡️  Promedios de lecturas por zona:")
    print("-" * 80)
    print(f"   {'Zona':<20} {'Temp (°C)':>10} {'Hum. Rel (%)':>13} {'Luz (lux)':>12} {'Hum. Suelo (%)':>15}")
    print("   " + "-" * 70)
    cursor.execute("""
        SELECT z.nombre,
               ROUND(AVG(l.temperatura), 1),
               ROUND(AVG(l.humedad_relativa), 1),
               ROUND(AVG(l.luminosidad), 0),
               ROUND(AVG(l.humedad_suelo), 1)
        FROM lecturas_sensores l
        JOIN zonas z ON l.zona_id = z.zona_id
        GROUP BY z.nombre
        ORDER BY z.nombre
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]:<20} {row[1]:>10} {row[2]:>13} {row[3]:>12,.0f} {row[4]:>15}")

    # Eventos de riego por zona
    print("\n Eventos de riego por zona:")
    print("-" * 50)
    cursor.execute("""
        SELECT z.nombre, COUNT(e.evento_id), SUM(e.duracion_seg)
        FROM eventos_riego e
        JOIN zonas z ON e.zona_id = z.zona_id
        GROUP BY z.nombre
        ORDER BY z.nombre
    """)
    for row in cursor.fetchall():
        horas_riego = row[2] / 3600 if row[2] else 0
        print(f"   {row[0]:<20} {row[1]:>5} eventos  ({horas_riego:.1f} horas totales)")

    # Alertas por tipo
    print("\n Alertas por tipo:")
    print("-" * 50)
    cursor.execute("""
        SELECT tipo_alerta, COUNT(*)
        FROM alertas
        GROUP BY tipo_alerta
        ORDER BY COUNT(*) DESC
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]:<25} {row[1]:>5} alertas")

    # Rango de fechas cubierto
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM lecturas_sensores")
    rango = cursor.fetchone()
    print(f"\n Rango temporal de datos: {rango[0]} → {rango[1]}")

    # Verificar integridad referencial
    print("\n Verificación de integridad referencial:")
    cursor.execute("""
        SELECT COUNT(*) FROM lecturas_sensores l
        LEFT JOIN zonas z ON l.zona_id = z.zona_id
        WHERE z.zona_id IS NULL
    """)
    huerfanos_lecturas = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*) FROM eventos_riego e
        LEFT JOIN zonas z ON e.zona_id = z.zona_id
        WHERE z.zona_id IS NULL
    """)
    huerfanos_eventos = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*) FROM alertas a
        LEFT JOIN zonas z ON a.zona_id = z.zona_id
        WHERE z.zona_id IS NULL
    """)
    huerfanos_alertas = cursor.fetchone()[0]

    print(f"   Lecturas huérfanas (sin zona válida): {huerfanos_lecturas}")
    print(f"   Eventos huérfanos (sin zona válida):  {huerfanos_eventos}")
    print(f"   Alertas huérfanas (sin zona válida):  {huerfanos_alertas}")

    if huerfanos_lecturas == 0 and huerfanos_eventos == 0 and huerfanos_alertas == 0:
        print("   Integridad referencial: OK")
    else:
        print("   Se detectaron registros huérfanos")

    print("\n" + "=" * 70)
    print("  CARGA DE PRUEBA COMPLETADA EXITOSAMENTE")
    print("=" * 70)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    # Eliminar base de datos previa si existe (para pruebas limpias)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"[i] Base de datos previa eliminada: {DB_PATH}")

    print(f"[i] Creando base de datos: {DB_PATH}")
    print()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")  # Activar integridad referencial

    try:
        # Paso 1: Crear esquema
        crear_esquema(conn)

        # Paso 2: Insertar datos de prueba
        cultivo_ids = insertar_cultivos(conn)
        zonas_info = insertar_zonas(conn, cultivo_ids)
        insertar_lecturas_y_eventos(conn, zonas_info)

        # Paso 3: Verificar datos cargados
        ejecutar_verificaciones(conn)

    finally:
        conn.close()

    print(f"\n[i] Archivo de base de datos: {DB_PATH}")
    print(f"[i] Tamaño: {os.path.getsize(DB_PATH) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
