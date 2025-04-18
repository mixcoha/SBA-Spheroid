# Simulaciones CompuCell3D

Este repositorio contiene simulaciones de CompuCell3D para el estudio de crecimiento celular y dinámica de tejidos.

## Estructura del Repositorio

```
.
├── docs/                  # Documentación y guías
├── old_simulations/       # Simulaciones antiguas y experimentales
├── projects_simulations/  # Simulaciones de proyectos actuales
├── scripts/              # Scripts de utilidad y análisis
├── requirements.txt      # Dependencias del proyecto
├── README.md            # Este archivo
└── CHANGELOG.md         # Registro de cambios
```

## Carpetas de Simulaciones

### old_simulations/
Contiene simulaciones antiguas y experimentales que sirven como referencia histórica. Estas simulaciones pueden no estar completamente documentadas o pueden requerir ajustes para funcionar con versiones actuales de CompuCell3D.

### projects_simulations/
Contiene las simulaciones activas y en desarrollo. Cada proyecto debe incluir:
- Archivos de configuración XML
- Scripts de Python personalizados
- Documentación específica del proyecto
- Resultados y análisis

## Requisitos

- Python 3.8+
- CompuCell3D
- Dependencias de Python (ver `requirements.txt`)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/mixcoha/SBA-Spheroid.git
cd SBA-Spheroid
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

Cada directorio contiene su propia documentación específica:

- `src/simulation/`: Scripts de simulación
- `results/`: Resultados de simulaciones
- `docs/`: Documentación detallada

## Documentación

La documentación detallada se encuentra en el directorio `docs/`:
- Guías de instalación
- Tutoriales de uso
- Documentación de API
- Ejemplos de simulación

## Contribución

Las contribuciones son bienvenidas. Por favor, consulta las guías de contribución en `docs/CONTRIBUTING.md`.

## Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.
