# Configuración del Proyecto

Este documento describe la configuración del proyecto y sus componentes.

## Requisitos del Sistema

### Software Requerido
- Python 3.8 o superior
- CompuCell3D 4.0 o superior
- Git

### Dependencias de Python
Las dependencias están listadas en `requirements.txt`:
```bash
numpy>=1.21.0
matplotlib>=3.4.0
python-docx>=0.8.11
scipy>=1.7.0
pandas>=1.3.0
```

## Configuración del Entorno

### Instalación de Dependencias
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Configuración de CompuCell3D
1. Instalar CompuCell3D
2. Configurar las variables de entorno:
   ```bash
   export CC3D_HOME=/ruta/a/compucell3d
   export PATH=$PATH:$CC3D_HOME
   ```

## Configuración de Simulaciones

### Parámetros de Simulación
Los parámetros de simulación se configuran en los archivos XML:
```xml
<Steppable Type="DiffusionSolverFE">
    <Field Name="O2">
        <DiffusionData>
            <DiffusionConstant>1000</DiffusionConstant>
            <DecayConstant>0.1</DecayConstant>
        </DiffusionData>
    </Field>
</Steppable>
```

### Configuración de Campos
- Campos de difusión
- Condiciones de frontera
- Tasas de secreción
- Umbrales metabólicos

## Configuración de Desarrollo

### Estructura del Proyecto
```
.
├── docs/                  # Documentación
├── projects_simulations/  # Simulaciones actuales
├── old_simulations/      # Simulaciones antiguas
├── scripts/             # Scripts de utilidad
└── requirements.txt     # Dependencias
```

### Convenciones de Código
- PEP 8 para Python
- Documentación en formato Markdown
- Comentarios en inglés

## Configuración de Git

### .gitignore
El archivo `.gitignore` excluye:
- Archivos temporales
- Resultados de simulación
- Archivos de configuración local

### Flujo de Trabajo
1. Crear rama para nuevas características
2. Hacer commits descriptivos
3. Revisar cambios antes de merge
4. Mantener la rama main estable

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