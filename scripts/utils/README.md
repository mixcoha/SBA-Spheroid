# Utilidades para CompuCell3D

Este directorio contiene scripts de utilidad para el manejo y mantenimiento de simulaciones CompuCell3D.

## Scripts Disponibles

### limpiar_cc3d.py

Este script ayuda a mantener limpio el directorio de trabajo de CompuCell3D, identificando y limpiando simulaciones incompletas o inactivas.

#### Funcionalidades:
- Analiza el estado de las simulaciones en el directorio de trabajo
- Identifica simulaciones incompletas o inactivas
- Permite borrar simulaciones problemáticas de forma segura

#### Uso:
```python
from limpiar_cc3d import analizar_simulaciones, borrar_simulaciones_incompletas

# Analizar simulaciones
resultados = analizar_simulaciones("/ruta/a/CC3DWorkspace/")

# Borrar simulaciones incompletas
borrar_simulaciones_incompletas(resultados)
```

#### Parámetros:
- `directorio_base`: Ruta al directorio de trabajo de CompuCell3D
- `horas_inactividad`: Número de horas de inactividad para considerar una simulación como inactiva (default: 12) 