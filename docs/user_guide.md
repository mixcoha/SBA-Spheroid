# Guía de Usuario

## Instalación

### Requisitos Previos

- Python 3.8 o superior
- CompuCell3D 4.0 o superior
- Git

### Pasos de Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/project_simulations.git
cd project_simulations
```

2. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso Básico

### Ejecutar una Simulación

1. Navegar al directorio de la simulación:
```bash
cd sphe_6metabo_G-M-CH-D
```

2. Ejecutar la simulación:
```bash
python run_simulation.py
```

### Parámetros de Configuración

Los parámetros principales se pueden ajustar en:
- `config/simulation/parameters.xml`
- `config/simulation/cell_types.xml`

### Visualización de Resultados

1. Usar el visor de CompuCell3D:
```bash
cc3d_player results/simulation.vtk
```

2. Generar gráficos:
```bash
python scripts/plot_results.py
```

## Tipos de Simulaciones

### Simulación de Esferoides

- **Propósito**: Modelar crecimiento tumoral en 3D
- **Parámetros clave**:
  - Radio inicial
  - Tasa de proliferación
  - Condiciones de borde

### Simulación Metabólica

- **Propósito**: Estudiar dinámica metabólica
- **Parámetros clave**:
  - Concentraciones iniciales
  - Tasas de reacción
  - Umbrales metabólicos

### Simulación de Hipoxia

- **Propósito**: Analizar efectos de hipoxia
- **Parámetros clave**:
  - Umbral de O2
  - Tiempo de adaptación
  - Respuesta celular

## Análisis de Datos

### Procesamiento de Resultados

1. Extraer métricas:
```bash
python scripts/extract_metrics.py
```

2. Generar reportes:
```bash
python scripts/generate_report.py
```

### Visualización

- Gráficos de evolución temporal
- Mapas de concentración
- Distribuciones celulares
- Análisis estadístico

## Solución de Problemas

### Errores Comunes

1. **Error de memoria**:
   - Reducir tamaño de simulación
   - Ajustar parámetros de caché
   - Limpiar resultados antiguos

2. **Error de convergencia**:
   - Ajustar Delta T
   - Verificar condiciones iniciales
   - Revisar parámetros de difusión

3. **Error de visualización**:
   - Actualizar CompuCell3D
   - Verificar formatos de archivo
   - Reinstalar dependencias

### Contacto

Para reportar problemas o sugerencias:
- Abrir un issue en GitHub
- Contactar al mantenedor: tu-email@ejemplo.com 