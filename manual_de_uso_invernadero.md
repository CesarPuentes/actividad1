# 🌿 Manual de Uso: Sistema de Automatización de Invernadero
## Guía para Exposición y Demostración Técnica

Este manual proporciona las instrucciones necesarias para demostrar el funcionamiento del sistema de monitoreo y control automatizado de un invernadero basado en **Raspberry Pi** y **SQLite**.

---

## 1. Introducción al Proyecto
El sistema resuelve la problemática de pérdida de cultivos mediante el monitoreo constante de variables ambientales y la ejecución de riego automatizado basado en las necesidades específicas de cada planta (Tomate, Lechuga, Fresa).

### Componentes Clave:
*   **Base de Datos**: SQLite (almacenamiento persistente).
*   **Lógica de Control**: Python (procesamiento de datos y reglas de negocio).
*   **Simulación**: Generación de datos realistas para demostrar el comportamiento del sistema sin necesidad de hardware físico inmediato.

---

## 2. Requisitos Previos
Para ejecutar la demostración, asegúrate de contar con:
1.  **Python 3.10 o superior**.
2.  **Librerías estándar** (vienen con Python): `sqlite3`, `random`, `os`, `datetime`.
3.  **Visualizador de SQLite** (Opcional pero recomendado): [DB Browser for SQLite](https://sqlitebrowser.org/) o la extensión "SQLite Viewer" en VS Code.

---

## 3. Instalación y Puesta en Marcha

### Paso 1: Preparar los archivos
Asegúrate de tener en la misma carpeta:
*   `carga_prueba_invernadero.py` (Script principal).
*   `evidencia_1_invernadero.md` (Documentación del modelo).

### Paso 2: Ejecutar la simulación
Abre una terminal y ejecuta:
```bash
python carga_prueba_invernadero.py
```

### ¿Qué sucede al ejecutar?
1.  **Limpieza**: Si existe una base de datos previa (`invernadero.db`), se elimina para garantizar una demostración limpia.
2.  **Creación**: Se genera el esquema de tablas (Cultivos, Zonas, Lecturas, Riego, Alertas).
3.  **Carga**: Se insertan 7 días de datos simulados (cada 5 min), incluyendo ciclos diurnos (más calor/luz de día, más fresco de noche).
4.  **Validación**: Se imprime un **Reporte de Verificación** detallado en la consola.

---

## 4. Guion de Exposición (Demo Script)

Sigue estos pasos para una presentación impactante de 5 a 10 minutos:

### A. Introducción (1-2 min)
*   "Buen día. Presentamos un sistema de automatización para invernaderos que utiliza la metodología **CRISP-DM**."
*   "El problema: El riego manual es ineficiente y la falta de datos impide tomar decisiones."
*   "Nuestra solución: Un cerebro central (Raspberry Pi) que decide cuándo regar basándose en sensores."

### B. Demostración del Código (2 min)
*   Ejecuta el script `python carga_prueba_invernadero.py`.
*   **Señala el Reporte en Consola**:
    *   Muestra cuántas lecturas se generaron (~8,000 para 7 días).
    *   Resalta la sección de **"Eventos de riego por zona"**: "Noten como la Zona B (Lechuga) necesitó más riego que la Zona A, esto es porque cada cultivo tiene sus propios umbrales de humedad."
    *   Muestra las **Alertas**: "El sistema detectó temperaturas críticas y registró alertas automáticas."

### C. Exploración de Datos en Vivo (3 min)
Si tienes un visualizador de base de datos abierto, muestra la tabla `alertas` o `lecturas_sensores`.
O bien, ejecuta estas consultas SQL para impresionar al público:

**Consulta 1: ¿Cuáles fueron las condiciones más críticas?**
```sql
SELECT timestamp, mensaje, valor_detectado 
FROM alertas 
ORDER BY valor_detectado DESC LIMIT 5;
```

**Consulta 2: Eficiencia del riego (Humedad antes vs después)**
```sql
SELECT zona_id, humedad_antes, humedad_despues, duracion_seg 
FROM eventos_riego 
WHERE tipo = 'automatico' 
LIMIT 10;
```

### D. Conclusión y Futuro (1 min)
*   "La base de datos está normalizada y lista para escalar."
*   "Próximos pasos: Implementar un dashboard web con Flask y conectar sensores físicos DHT22."

---

## 5. Interpretación del Modelo de Datos
Si el público pregunta por la estructura:
*   **Tabla `cultivos`**: Es el diccionario de reglas (temp_min, hum_min, etc.).
*   **Tabla `zonas`**: Divide el invernadero físicamente.
*   **Tabla `lecturas_sensores`**: Es el "corazón" del historial de datos.
*   **Integridad Referencial**: "No podemos borrar una zona si tiene lecturas asociadas, lo que garantiza que los datos históricos sean confiables."

---

> [!TIP]
> **Consejo para la exposición**: Si el script falla por permisos, asegúrate de estar en una carpeta donde tengas permisos de escritura, ya que SQLite creará el archivo `.db` en ese mismo directorio.
