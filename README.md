# 🌱 GreenHouse Pi — Sistema de Automatización de Cuidado de Plantas en Invernadero

Sistema de monitoreo ambiental y riego automatizado para invernaderos, construido sobre **Raspberry Pi** y **Python**. Recopila datos de sensores (temperatura, humedad, luminosidad, humedad del suelo), activa el riego de forma inteligente según umbrales configurables por cultivo y genera alertas ante condiciones críticas.

---

## 📑 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Modelo de Datos](#modelo-de-datos)
- [Manual de Funcionamiento](#manual-de-funcionamiento)
  - [Ejecución de la Carga de Prueba](#ejecución-de-la-carga-de-prueba)
  - [Interpretación del Reporte](#interpretación-del-reporte)
  - [Consultas Útiles](#consultas-útiles)
- [Guía para Desarrolladores](#guía-para-desarrolladores)
  - [Convenciones del Código](#convenciones-del-código)
  - [Agregar un Nuevo Cultivo](#agregar-un-nuevo-cultivo)
  - [Agregar una Nueva Zona](#agregar-una-nueva-zona)
  - [Modificar la Lógica de Riego](#modificar-la-lógica-de-riego)
  - [Agregar un Nuevo Tipo de Alerta](#agregar-un-nuevo-tipo-de-alerta)
  - [Extender el Esquema de Datos](#extender-el-esquema-de-datos)
  - [Simulación de Datos](#simulación-de-datos)
- [Conexión de Hardware (Referencia)](#conexión-de-hardware-referencia)
- [Metodología CRISP-DM](#metodología-crisp-dm)
- [Solución de Problemas](#solución-de-problemas)
- [Licencia](#licencia)

---

## Descripción General

Un invernadero de producción hortícola enfrenta pérdidas por falta de monitoreo ambiental continuo, riego ineficiente por horarios fijos y ausencia de datos históricos para tomar decisiones. Este sistema resuelve esos problemas mediante:

| Función | Descripción |
|---------|-------------|
| **Monitoreo continuo** | Lectura de temperatura, humedad relativa, luminosidad y humedad del suelo cada 5 minutos por zona |
| **Riego inteligente** | Activación automática cuando la humedad del suelo cae por debajo del umbral del cultivo |
| **Alertas** | Notificaciones cuando se detectan condiciones críticas (temperatura extrema, fallo de sensor) |
| **Historial de datos** | Almacenamiento persistente en SQLite para análisis posterior |

---

## Arquitectura del Sistema

```
 SENSORES                PROCESAMIENTO            ACTUADORES
┌──────────────┐        ┌──────────────────┐     ┌──────────────────┐
│ DHT22        │        │                  │     │ Módulo relé      │
│ (temp + hum) │──GPIO──│                  │─GPIO│ 4 canales        │
│              │        │   Raspberry Pi   │     │                  │
│ BH1750       │        │   4 Model B      │     │ Electroválvulas  │
│ (luminosidad)│──I2C───│                  │     │ de riego         │
│              │        │  Python 3.11+    │     └──────────────────┘
│ Sensor suelo │        │  SQLite          │
│ (capacitivo) │──ADC───│                  │     ┌──────────────────┐
└──────────────┘        │                  │─────│ Dashboard web    │
                        │                  │     │ Alertas Telegram │
                        └────────┬─────────┘     └──────────────────┘
                                 │
                        ┌────────▼─────────┐
                        │  invernadero.db  │
                        │  (SQLite)        │
                        └──────────────────┘
```

---

## Requisitos

### Software

| Componente | Versión mínima | Notas |
|------------|---------------|-------|
| Python | 3.8+ | Probado con 3.11 |
| SQLite | 3.x | Incluido en la biblioteca estándar de Python (`sqlite3`) |
| pip | 21+ | Solo si se agregan dependencias externas |

> **Nota:** El script de carga de prueba (`carga_prueba_invernadero.py`) **no requiere dependencias externas**. Utiliza únicamente módulos de la biblioteca estándar: `sqlite3`, `random`, `os`, `datetime`.

### Hardware (para despliegue real)

| Componente | Cantidad | Propósito |
|------------|----------|-----------|
| Raspberry Pi 4 Model B (4 GB) | 1 | Unidad central de procesamiento |
| Sensor DHT22 | 4 | Temperatura y humedad del aire (1 por zona) |
| Sensor BH1750 | 4 | Intensidad lumínica (1 por zona) |
| Sensor de humedad de suelo capacitivo | 4 | Humedad volumétrica del suelo (1 por zona) |
| MCP3008 (ADC) | 1 | Convertidor analógico-digital para sensores de suelo |
| Módulo relé de 4 canales | 1 | Activación de electroválvulas |
| Electroválvulas de riego | 4 | Control del flujo de agua (1 por zona) |
| Fuente de alimentación 5V/3A | 1 | Alimentación de la Raspberry Pi |

---

## Instalación

### 1. Clonar o descargar el proyecto

```bash
git clone <url-del-repositorio>
cd ProgramacionAnalisisDatos
```

### 2. Verificar la versión de Python

```bash
python3 --version
# Debe ser 3.8 o superior
```

### 3. Ejecutar la carga de prueba

```bash
python3 carga_prueba_invernadero.py
```

Esto creará el archivo `invernadero.db` en el mismo directorio con datos simulados de 7 días.

---

## Estructura del Proyecto

```
ProgramacionAnalisisDatos/
│
├── README.md                        ← Este archivo
├── evidencia_1_invernadero.md       ← Documento de la evidencia (CRISP-DM fases 1 y 2)
├── carga_prueba_invernadero.py      ← Script principal: esquema + datos de prueba
├── invernadero.db                   ← Base de datos SQLite (generada por el script)
│
├── actividad_1.txt                  ← Instrucciones de la actividad
└── unidad_1.txt                     ← Material de referencia de la Unidad 1
```

---

## Modelo de Datos

La base de datos contiene **5 tablas** organizadas en un esquema relacional:

```
cultivos (1) ──────< (N) zonas (1) ──────< (N) lecturas_sensores
                          │
                          ├──────< (N) eventos_riego
                          │
                          └──────< (N) alertas
```

### Tablas

#### `cultivos`

Define los parámetros óptimos para cada tipo de planta.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `cultivo_id` | INTEGER PK | Identificador único |
| `nombre` | TEXT UNIQUE | Nombre del cultivo (e.g., "Tomate") |
| `temp_min` | REAL | Temperatura mínima óptima (°C) |
| `temp_max` | REAL | Temperatura máxima óptima (°C) |
| `humedad_suelo_min` | REAL | Umbral mínimo de humedad del suelo para activar riego (%) |
| `humedad_suelo_max` | REAL | Humedad del suelo máxima ideal (%) |
| `luminosidad_min` | REAL | Luminosidad mínima recomendada (lux) |
| `luminosidad_max` | REAL | Luminosidad máxima tolerada (lux) |
| `duracion_riego_seg` | INTEGER | Duración del riego automático (segundos) |

#### `zonas`

Cada zona del invernadero con un cultivo asignado.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `zona_id` | INTEGER PK | Identificador único |
| `nombre` | TEXT UNIQUE | Nombre descriptivo (e.g., "Zona A - Norte") |
| `ubicacion` | TEXT | Descripción física de la ubicación |
| `area_m2` | REAL | Superficie en metros cuadrados |
| `cultivo_id` | INTEGER FK → `cultivos` | Cultivo asignado a esta zona |

#### `lecturas_sensores`

Registro histórico de datos ambientales. Restricción `UNIQUE(zona_id, timestamp)` para evitar duplicados.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `lectura_id` | INTEGER PK | Identificador único |
| `zona_id` | INTEGER FK → `zonas` | Zona de origen |
| `timestamp` | DATETIME | Momento de la lectura |
| `temperatura` | REAL | Temperatura del aire (°C) |
| `humedad_relativa` | REAL | Humedad relativa del aire (%) |
| `luminosidad` | REAL | Intensidad lumínica (lux) |
| `humedad_suelo` | REAL | Humedad volumétrica del suelo (%) |

#### `eventos_riego`

Registra cada activación del sistema de riego.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `evento_id` | INTEGER PK | Identificador único |
| `zona_id` | INTEGER FK → `zonas` | Zona regada |
| `timestamp_inicio` | DATETIME | Inicio del riego |
| `timestamp_fin` | DATETIME | Fin del riego |
| `duracion_seg` | INTEGER | Duración en segundos |
| `humedad_antes` | REAL | Humedad del suelo antes del riego (%) |
| `humedad_despues` | REAL | Humedad del suelo después del riego (%) |
| `tipo` | TEXT | `'automatico'` o `'manual'` |

#### `alertas`

Registra condiciones críticas detectadas.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `alerta_id` | INTEGER PK | Identificador único |
| `zona_id` | INTEGER FK → `zonas` | Zona afectada |
| `timestamp` | DATETIME | Momento de la alerta |
| `tipo_alerta` | TEXT | `'temperatura_alta'`, `'temperatura_baja'`, `'humedad_baja'`, `'sensor_fallo'` |
| `valor_detectado` | REAL | Valor que disparó la alerta |
| `umbral` | REAL | Umbral configurado que se superó |
| `mensaje` | TEXT | Descripción legible de la alerta |
| `notificada` | BOOLEAN | Si ya se envió la notificación |

### Índices

| Índice | Tabla | Columnas | Propósito |
|--------|-------|----------|-----------|
| `idx_lecturas_zona_ts` | `lecturas_sensores` | `(zona_id, timestamp)` | Optimizar consultas de series de tiempo por zona |
| `idx_eventos_zona_ts` | `eventos_riego` | `(zona_id, timestamp_inicio)` | Búsqueda rápida de eventos de riego por zona |
| `idx_alertas_zona_ts` | `alertas` | `(zona_id, timestamp)` | Filtrado eficiente de alertas por zona y fecha |

---

## Manual de Funcionamiento

### Ejecución de la Carga de Prueba

```bash
python3 carga_prueba_invernadero.py
```

**Comportamiento:**

1. Si existe una base de datos previa (`invernadero.db`), se **elimina** para garantizar una carga limpia.
2. Se crea el esquema completo (tablas, índices, restricciones).
3. Se insertan 3 cultivos y 4 zonas predefinidas.
4. Se simulan **7 días** de lecturas de sensores con intervalos de **5 minutos**.
5. Se generan eventos de riego automático cuando la humedad del suelo cae por debajo del umbral.
6. Se generan alertas cuando la temperatura supera rangos críticos.
7. Se ejecutan consultas de verificación y se imprime un reporte en consola.

### Interpretación del Reporte

El reporte de verificación incluye las siguientes secciones:

| Sección | Qué muestra |
|---------|-------------|
| 📊 **Conteo de registros** | Número de filas en cada tabla |
| 🌡️ **Promedios por zona** | Media de temperatura, humedad, luminosidad y humedad de suelo |
| 💧 **Eventos de riego** | Cantidad de riegos y horas totales de riego por zona |
| 🚨 **Alertas por tipo** | Distribución de alertas según su clasificación |
| 📅 **Rango temporal** | Fecha/hora de la primera y última lectura |
| 🔗 **Integridad referencial** | Verifica que no existan registros huérfanos (sin zona válida) |

**Resultado esperado:** todas las tablas con datos, promedios coherentes, y ✅ en integridad referencial.

### Consultas Útiles

Puedes inspeccionar la base de datos directamente con `sqlite3`:

```bash
sqlite3 invernadero.db
```

#### Ver las últimas 10 lecturas de una zona

```sql
SELECT timestamp, temperatura, humedad_relativa, humedad_suelo
FROM lecturas_sensores
WHERE zona_id = 1
ORDER BY timestamp DESC
LIMIT 10;
```

#### Promedio diario de temperatura por zona

```sql
SELECT z.nombre,
       DATE(l.timestamp) AS fecha,
       ROUND(AVG(l.temperatura), 1) AS temp_promedio,
       ROUND(MIN(l.temperatura), 1) AS temp_min,
       ROUND(MAX(l.temperatura), 1) AS temp_max
FROM lecturas_sensores l
JOIN zonas z ON l.zona_id = z.zona_id
GROUP BY z.nombre, DATE(l.timestamp)
ORDER BY z.nombre, fecha;
```

#### Eventos de riego con información del cultivo

```sql
SELECT z.nombre AS zona,
       c.nombre AS cultivo,
       e.timestamp_inicio,
       e.duracion_seg,
       e.humedad_antes,
       e.humedad_despues
FROM eventos_riego e
JOIN zonas z ON e.zona_id = z.zona_id
JOIN cultivos c ON z.cultivo_id = c.cultivo_id
ORDER BY e.timestamp_inicio DESC
LIMIT 20;
```

#### Alertas de las últimas 24 horas

```sql
SELECT a.timestamp, z.nombre, a.tipo_alerta, a.valor_detectado, a.umbral
FROM alertas a
JOIN zonas z ON a.zona_id = z.zona_id
WHERE a.timestamp >= datetime('now', '-1 day')
ORDER BY a.timestamp DESC;
```

#### Eficiencia del riego (incremento promedio de humedad por evento)

```sql
SELECT z.nombre,
       COUNT(*) AS total_riegos,
       ROUND(AVG(e.humedad_despues - e.humedad_antes), 1) AS incremento_promedio,
       ROUND(SUM(e.duracion_seg) / 3600.0, 2) AS horas_riego_total
FROM eventos_riego e
JOIN zonas z ON e.zona_id = z.zona_id
GROUP BY z.nombre;
```

---

## Guía para Desarrolladores

### Convenciones del Código

| Aspecto | Convención |
|---------|-----------|
| **Lenguaje** | Python 3.8+ |
| **Estilo** | PEP 8 |
| **Docstrings** | Google style |
| **Nombres de tablas** | `snake_case`, plural (e.g., `lecturas_sensores`) |
| **Nombres de columnas** | `snake_case` (e.g., `humedad_relativa`) |
| **Claves primarias** | `<tabla_singular>_id` (e.g., `zona_id`) |
| **Claves foráneas** | Mismo nombre que la PK referenciada |
| **Tipos SQL** | `INTEGER`, `REAL`, `TEXT`, `DATETIME`, `BOOLEAN` |
| **Semilla aleatoria** | `random.seed(42)` para reproducibilidad en simulaciones |

### Agregar un Nuevo Cultivo

1. Localiza el diccionario `CULTIVOS` en `carga_prueba_invernadero.py` (~línea 115).
2. Agrega una nueva entrada con los parámetros del cultivo:

```python
{
    "nombre": "Pepino",
    "temp_min": 20.0, "temp_max": 32.0,
    "humedad_suelo_min": 55.0, "humedad_suelo_max": 80.0,
    "luminosidad_min": 10000.0, "luminosidad_max": 45000.0,
    "duracion_riego_seg": 240,
},
```

3. *(Opcional)* Asigna el nuevo cultivo a una zona existente o crea una nueva zona.

### Agregar una Nueva Zona

1. Localiza el diccionario `ZONAS` (~línea 137).
2. Agrega una entrada referenciando un cultivo existente:

```python
{"nombre": "Zona E - Centro", "ubicacion": "Sector central, hileras 19-22", "area_m2": 100.0, "cultivo": "Pepino"},
```

3. El campo `"cultivo"` debe coincidir exactamente con el `nombre` de un cultivo en `CULTIVOS`.

### Modificar la Lógica de Riego

La lógica de riego automático se encuentra en la función `insertar_lecturas_y_eventos()` (~línea 185). El bloque relevante es:

```python
# ¿Activar riego automático?
if humedad_suelo < params["humedad_suelo_min"]:
    # ... activar riego ...
```

**Para modificar el comportamiento:**

- **Cambiar umbrales:** Modifica `humedad_suelo_min` en la configuración del cultivo.
- **Agregar condiciones adicionales:** Añade lógica antes de activar el riego (e.g., no regar de noche, no regar si llueve).
- **Riego proporcional:** Ajusta `duracion_riego_seg` dinámicamente según qué tan por debajo del umbral esté la humedad.

**Ejemplo — no regar entre las 22:00 y las 06:00:**

```python
if humedad_suelo < params["humedad_suelo_min"] and not (22 <= hora or hora < 6):
    # activar riego...
```

### Agregar un Nuevo Tipo de Alerta

1. En el esquema SQL, la restricción `CHECK` de la tabla `alertas` define los tipos válidos:

```sql
CHECK(tipo_alerta IN (
    'temperatura_alta', 'temperatura_baja',
    'humedad_baja', 'sensor_fallo'
))
```

   Agrega el nuevo tipo al `CHECK`. Ejemplo para agregar `'luminosidad_excesiva'`:

```sql
CHECK(tipo_alerta IN (
    'temperatura_alta', 'temperatura_baja',
    'humedad_baja', 'sensor_fallo',
    'luminosidad_excesiva'
))
```

2. Agrega la lógica de detección en `insertar_lecturas_y_eventos()`, después del bloque de alertas de temperatura (~línea 260):

```python
if luminosidad > params["luminosidad_max"]:
    alertas_batch.append((
        zona_id, ts.strftime("%Y-%m-%d %H:%M:%S"),
        "luminosidad_excesiva", luminosidad, params["luminosidad_max"],
        f"Luminosidad de {luminosidad} lux supera el máximo de {params['luminosidad_max']} lux",
        1
    ))
    total_alertas += 1
```

### Extender el Esquema de Datos

Si necesitas agregar una nueva tabla (e.g., `usuarios` para control de acceso):

1. Agrega el `CREATE TABLE` al string `SCHEMA_SQL` (~línea 27).
2. Si la tabla necesita datos iniciales, crea una función `insertar_<tabla>()` siguiendo el patrón de `insertar_cultivos()`.
3. Llama a la nueva función desde `main()`.
4. Agrega consultas de verificación en `ejecutar_verificaciones()` si es necesario.

**Importante:** Siempre incluye `IF NOT EXISTS` en los `CREATE TABLE` y `CREATE INDEX` para que el script sea idempotente.

### Simulación de Datos

La simulación utiliza dos mecanismos para generar datos realistas:

#### Ciclo Diurno (`simular_ciclo_diurno()`)

Ajusta los parámetros base según la hora del día:

| Hora | Temperatura base | Luminosidad base | Humedad relativa |
|------|-----------------|------------------|------------------|
| 06:00 – 10:00 | 20 °C | 15,000 lux | 70 % |
| 10:00 – 14:00 | 28 °C | 35,000 lux | 55 % |
| 14:00 – 18:00 | 26 °C | 20,000 lux | 60 % |
| 18:00 – 22:00 | 20 °C | 500 lux | 75 % |
| 22:00 – 06:00 | 16 °C | 0 lux | 80 % |

Para cambiar estos valores, modifica la función `simular_ciclo_diurno()` (~línea 155).

#### Distribución Normal Acotada (`generar_valor_sensor()`)

Cada lectura se genera con `random.gauss(media, desviacion)` y se acota al rango `[minimo, maximo]` para evitar valores físicamente imposibles.

#### Parámetros de Simulación

| Parámetro | Variable | Valor por defecto | Ubicación |
|-----------|----------|-------------------|-----------|
| Días simulados | `DIAS_SIMULADOS` | 7 | Línea 13 |
| Intervalo entre lecturas | `INTERVALO_MINUTOS` | 5 | Línea 14 |
| Semilla aleatoria | `random.seed(42)` | 42 | Línea 16 |

---

## Conexión de Hardware (Referencia)

> **Nota:** Esta sección es una referencia para el despliegue real en Raspberry Pi. No es necesaria para ejecutar la carga de prueba.

### Diagrama de Conexiones GPIO

```
Raspberry Pi 4 GPIO Header
─────────────────────────────
Pin 1  (3.3V)   ──── VCC sensor BH1750
Pin 2  (5V)     ──── VCC sensor DHT22
Pin 3  (GPIO 2) ──── SDA sensor BH1750 (I2C)
Pin 5  (GPIO 3) ──── SCL sensor BH1750 (I2C)
Pin 7  (GPIO 4) ──── DATA sensor DHT22 (Zona A)
Pin 11 (GPIO 17)──── DATA sensor DHT22 (Zona B)
Pin 13 (GPIO 27)──── DATA sensor DHT22 (Zona C)
Pin 15 (GPIO 22)──── DATA sensor DHT22 (Zona D)
Pin 19 (GPIO 10)──── MOSI → MCP3008 (SPI)
Pin 21 (GPIO 9) ──── MISO ← MCP3008 (SPI)
Pin 23 (GPIO 11)──── SCLK → MCP3008 (SPI)
Pin 24 (GPIO 8) ──── CS   → MCP3008 (SPI)
Pin 29 (GPIO 5) ──── IN1 módulo relé (Zona A)
Pin 31 (GPIO 6) ──── IN2 módulo relé (Zona B)
Pin 33 (GPIO 13)──── IN3 módulo relé (Zona C)
Pin 35 (GPIO 19)──── IN4 módulo relé (Zona D)
Pin 6  (GND)    ──── GND común
```

### Dependencias Adicionales para Hardware

```bash
pip install adafruit-circuitpython-dht adafruit-circuitpython-bh1750 adafruit-circuitpython-mcp3xxx RPi.GPIO
```

---

## Metodología CRISP-DM

Este proyecto sigue la metodología **CRISP-DM** (Cross-Industry Standard Process for Data Mining). La implementación actual cubre las **fases 1 y 2**:

| Fase | Nombre | Estado | Entregable |
|------|--------|--------|------------|
| 1 | Comprensión del negocio | ✅ Completada | `evidencia_1_invernadero.md` §1 |
| 2 | Comprensión de los datos | ✅ Completada | `evidencia_1_invernadero.md` §2–4 |
| 3 | Preparación de los datos | 🔲 Pendiente | — |
| 4 | Modelado | 🔲 Pendiente | — |
| 5 | Evaluación | 🔲 Pendiente | — |
| 6 | Despliegue | 🔲 Pendiente | — |

El documento `evidencia_1_invernadero.md` contiene el detalle completo de los objetivos del negocio, requerimientos, diagramas de flujo, modelo de datos y resultados de la carga de prueba.

---

## Solución de Problemas

| Problema | Causa probable | Solución |
|----------|---------------|----------|
| `ModuleNotFoundError: No module named 'sqlite3'` | Instalación de Python incompleta | Reinstalar Python con soporte para SQLite: `sudo apt install python3 libsqlite3-dev` |
| El script termina sin errores pero no genera `invernadero.db` | Permisos de escritura en el directorio | Verificar con `ls -la` y ajustar permisos: `chmod 755 .` |
| `UNIQUE constraint failed: lecturas_sensores.zona_id, lecturas_sensores.timestamp` | Se ejecutó el script dos veces sin eliminar la BD previa | El script ya elimina la BD previa automáticamente; si persiste, borrar manualmente: `rm invernadero.db` |
| Los promedios de temperatura parecen altos/bajos | Configuración del ciclo diurno | Ajustar los valores en `simular_ciclo_diurno()` |
| `OperationalError: database is locked` | Otra aplicación tiene abierta la BD | Cerrar otros clientes SQLite (e.g., DB Browser) antes de ejecutar |

---

## Licencia

Proyecto académico — **Programación para Análisis de Datos**, Ingeniería de Software y Datos.
