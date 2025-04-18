# Documentación de Simulaciones

Este documento describe las simulaciones implementadas en el proyecto.

## Estructura de Directorios

### old_simulations/
Contiene simulaciones antiguas y experimentales. Estas simulaciones se mantienen como referencia histórica y pueden requerir ajustes para funcionar con versiones actuales de CompuCell3D.

#### Contenido:
- Simulaciones iniciales de prueba
- Versiones antiguas de simulaciones actuales
- Experimentos no concluidos
- Referencias históricas

### projects_simulations/
Contiene las simulaciones activas y en desarrollo. Cada proyecto debe seguir una estructura estándar:

```
project_name/
├── config/              # Archivos de configuración XML
├── scripts/            # Scripts de Python personalizados
├── docs/              # Documentación específica del proyecto
└── results/           # Resultados y análisis
```

## Tipos de Simulaciones

### 1. Simulaciones de Esferoides
- Propósito: Estudio del crecimiento tumoral en 3D
- Características:
  - Modelo de esferoide multicelular
  - Interacciones célula-célula
  - Gradientes de nutrientes

### 2. Simulaciones Metabólicas
- Propósito: Análisis del metabolismo celular
- Características:
  - Modelos de consumo de nutrientes
  - Producción de metabolitos
  - Respuesta a condiciones hipóxicas

### 3. Simulaciones de Plasticidad Fenotípica
- Propósito: Estudio de transiciones celulares
- Características:
  - Modelos de transición entre fenotipos
  - Respuesta a señales ambientales
  - Dinámica de población

## Configuración de Simulaciones

### Archivos XML
Cada simulación requiere un archivo de configuración XML que define:
- Parámetros del modelo Potts
- Condiciones iniciales
- Propiedades de las células
- Condiciones de frontera

### Scripts de Python
Los scripts personalizados permiten:
- Inicialización de condiciones
- Control de la simulación
- Análisis de resultados
- Visualización de datos

## Análisis de Resultados

### Herramientas Disponibles
1. Scripts de Python para análisis
2. Visualización con matplotlib
3. Procesamiento de datos con pandas
4. Análisis estadístico con scipy

### Formatos de Salida
- Archivos VTK para visualización
- Datos CSV para análisis
- Gráficos y figuras
- Reportes en formato Word

## Solución de Problemas

### Errores Comunes
1. Problemas de convergencia
2. Errores de memoria
3. Inestabilidades numéricas
4. Problemas de visualización

### Soluciones Recomendadas
1. Ajustar parámetros de simulación
2. Reducir el tamaño del sistema
3. Modificar condiciones iniciales
4. Actualizar scripts de análisis

## Contacto y Soporte

Para reportar problemas o solicitar ayuda:
- Crear un issue en GitHub
- Contactar al administrador del repositorio
- Consultar la documentación en línea

## Simulación Steady State

### Descripción
La simulación Steady State modela el crecimiento y comportamiento de esferoides celulares bajo condiciones de estado estacionario. Esta simulación es fundamental para entender la dinámica celular en condiciones controladas.

### Estructura de Archivos
```
projects_simulations/steady_state/
├── Simulation/
│   ├── steady_state_simulation.py      # Script principal de simulación
│   ├── steady_state_simulation.xml     # Configuración XML
│   └── steady_state_simulationSteppables.py  # Comportamientos personalizados
└── steady_state_simulation.cc3d        # Archivo de proyecto CompuCell3D
```

### Parámetros de Simulación

#### Configuración General
- Tamaño del dominio: 100x100x100
- Condiciones de frontera: Periódicas
- Paso de tiempo: 1 MCS

#### Parámetros Celulares
- Energía de contacto entre células
- Tasa de crecimiento
- Umbrales metabólicos
- Propiedades de secreción

#### Campos de Difusión
- Oxígeno (O2)
- Glucosa (GLC)
- Ácido láctico (LAC)

### Ejecución
1. Abrir el archivo `steady_state_simulation.cc3d` en CompuCell3D
2. Configurar los parámetros deseados en el archivo XML
3. Ejecutar la simulación
4. Los resultados se guardan en el directorio `screenshot_data/`

### Análisis de Resultados
Los resultados incluyen:
- Evolución temporal del esferoide
- Distribución de campos de difusión
- Estadísticas celulares
- Métricas de crecimiento

### Visualización
Los resultados pueden visualizarse usando:
- Visor 3D de CompuCell3D
- Scripts de Python para análisis
- Herramientas de visualización personalizadas

## Otras Simulaciones

### Simulaciones Antiguas
Las simulaciones antiguas se encuentran en el directorio `old_simulations/` y sirven como referencia histórica. Estas incluyen:
- Variaciones en parámetros
- Diferentes condiciones iniciales
- Experimentos de validación 