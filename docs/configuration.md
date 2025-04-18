# Configuración del Proyecto

## Parámetros de Simulación

### Parámetros Generales

- **Tamaño de la Simulación**:
  - Dimensión X: 100
  - Dimensión Y: 100
  - Dimensión Z: 100

- **Tiempo de Simulación**:
  - Pasos MCS: 1000
  - Delta T: 0.1

### Parámetros de Células

- **Tipos de Células**:
  - Proliferativas
  - Quiescentes
  - Invasivas
  - Necróticas

- **Propiedades Metabólicas**:
  - Consumo de O2: 0.1
  - Consumo de GLC: 0.05
  - Producción de LAC: 0.02

### Condiciones Iniciales

- **Concentraciones Iniciales**:
  - O2: 1.0
  - GLC: 1.0
  - LAC: 0.0

- **Distribución de Células**:
  - Radio inicial: 20
  - Número de células: 1000

## Configuración de Archivos

### Estructura de Directorios

```
project_simulations/
├── config/          # Archivos de configuración
│   ├── simulation/  # Configuraciones de simulación
│   └── analysis/    # Configuraciones de análisis
├── data/            # Datos de entrada
│   ├── initial/     # Condiciones iniciales
│   └── parameters/  # Parámetros
└── output/          # Resultados
    ├── plots/       # Gráficos
    └── reports/     # Reportes
```

### Formatos de Archivo

- **Simulaciones**: `.xml`, `.cc3d`
- **Resultados**: `.vtk`, `.dat`
- **Análisis**: `.csv`, `.txt`
- **Visualización**: `.png`, `.pdf`

## Variables de Entorno

```bash
export CC3D_HOME=/path/to/compucell3d
export PYTHONPATH=$PYTHONPATH:$CC3D_HOME
export PATH=$PATH:$CC3D_HOME/bin
```

## Configuración de Rendimiento

### Optimizaciones

- **Paralelización**:
  - Número de hilos: 4
  - Tamaño de bloque: 32

- **Memoria**:
  - Tamaño máximo de caché: 1GB
  - Intervalo de limpieza: 100 pasos

### Monitoreo

- **Logging**:
  - Nivel: INFO
  - Formato: %(asctime)s - %(name)s - %(levelname)s - %(message)s
  - Archivo: simulation.log

- **Métricas**:
  - Intervalo de guardado: 10 pasos
  - Métricas a registrar: tiempo, memoria, células 