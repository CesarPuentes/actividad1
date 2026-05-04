# 🌱 GreenHouse Pi — Sistema de Automatización de Cuidado de Plantas en Invernadero

Sistema de monitoreo ambiental y riego automatizado para invernaderos, construido sobre **Raspberry Pi** y **Python**. Recopila datos de sensores (temperatura, humedad, luminosidad, humedad del suelo), activa el riego de forma inteligente según umbrales configurables por cultivo y genera alertas ante condiciones críticas.

---

## Descripción General

Un invernadero de producción hortícola enfrenta pérdidas por falta de monitoreo ambiental continuo, riego ineficiente por horarios fijos y ausencia de datos históricos para tomar decisiones. Este sistema resuelve esos problemas mediante:

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
