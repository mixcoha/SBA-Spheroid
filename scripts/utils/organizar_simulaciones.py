#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
import json
from datetime import datetime

def crear_estructura_simulacion(nombre_simulacion):
    """Crea la estructura de directorios para una simulación."""
    base_path = Path("simulaciones")
    sim_path = base_path / nombre_simulacion
    
    # Crear estructura de directorios
    for subdir in ["configs", "python", "results", "docs", "Simulation", "screen_shotdata"]:
        (sim_path / subdir).mkdir(parents=True, exist_ok=True)
    
    # Crear README.md para la simulación
    readme_content = f"""# {nombre_simulacion}

## Descripción
Simulación realizada en {datetime.now().strftime('%Y-%m-%d')}

## Estructura
- `configs/`: Archivos de configuración
- `python/`: Scripts de Python
- `results/`: Resultados y análisis
- `docs/`: Documentación
- `Simulation/`: Archivos de simulación
- `screen_shotdata/`: Capturas de pantalla

## Parámetros
[Documentar parámetros importantes]

## Resultados
[Documentar resultados principales]
"""
    
    with open(sim_path / "README.md", "w") as f:
        f.write(readme_content)
    
    return sim_path

def encontrar_simulaciones_cc3d(directorio_base):
    """Encuentra todas las carpetas que contienen archivos .cc3d."""
    simulaciones = []
    directorio_base = Path(directorio_base)
    
    for root, dirs, files in os.walk(directorio_base):
        if any(f.endswith('.cc3d') for f in files):
            # Obtener la ruta relativa desde el directorio base
            rel_path = Path(root).relative_to(directorio_base)
            simulaciones.append(str(rel_path))
    
    return simulaciones

def copiar_archivos(origen, destino, patrones=None):
    """Copia archivos según patrones específicos."""
    if patrones is None:
        patrones = {
            "configs": [".cc3d"],
            "python": [".py"],
            "results": [".srn", ".vtk", ".csv", ".txt"],
            "docs": [".md", ".pdf", ".doc", ".docx"],
            "Simulation": ["Simulation"],
            "screen_shotdata": ["screen_shotdata"]
        }
    
    origen_path = Path(origen)
    if not origen_path.exists():
        print(f"❌ El directorio {origen} no existe")
        return
    
    for tipo, extensiones in patrones.items():
        destino_dir = destino / tipo
        for ext in extensiones:
            if ext in [".cc3d", ".py", ".srn", ".vtk", ".csv", ".txt", ".md", ".pdf", ".doc", ".docx"]:
                # Para archivos
                for archivo in origen_path.rglob(f"*{ext}"):
                    try:
                        # Crear estructura de directorios si no existe
                        rel_path = archivo.relative_to(origen_path)
                        dest_path = destino_dir / rel_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Copiar archivo
                        shutil.copy2(archivo, dest_path)
                        print(f"✅ Copiado: {archivo} -> {dest_path}")
                    except Exception as e:
                        print(f"❌ Error al copiar {archivo}: {e}")
            else:
                # Para directorios
                for dir_path in origen_path.rglob(ext):
                    if dir_path.is_dir():
                        try:
                            # Crear estructura de directorios si no existe
                            rel_path = dir_path.relative_to(origen_path)
                            dest_path = destino_dir / rel_path
                            dest_path.mkdir(parents=True, exist_ok=True)
                            
                            # Copiar directorio completo
                            shutil.copytree(dir_path, dest_path, dirs_exist_ok=True)
                            print(f"✅ Copiado directorio: {dir_path} -> {dest_path}")
                        except Exception as e:
                            print(f"❌ Error al copiar directorio {dir_path}: {e}")

def copiar_simulacion(origen, destino):
    """Copia una carpeta de simulación completa."""
    origen_path = Path(origen)
    if not origen_path.exists():
        print(f"❌ El directorio {origen} no existe")
        return
    
    try:
        # Crear el directorio de destino si no existe
        destino_path = Path(destino)
        destino_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copiar todo el directorio
        shutil.copytree(origen_path, destino_path, dirs_exist_ok=True)
        print(f"✅ Copiada simulación: {origen} -> {destino}")
    except Exception as e:
        print(f"❌ Error al copiar {origen}: {e}")

def main():
    # Definir las simulaciones a copiar
    directorios_base = {
        "simulation_results": "/Users/mixcoha/simulation_results",
        "esf6dias": "/Users/mixcoha/esf6dias",
        "sphe_6metabo_G-M-CH-D": "/Users/mixcoha/sphe_6metabo_G-M-CH-D"
    }
    
    # Crear directorio projects_simulations
    projects_dir = Path("projects_simulations")
    projects_dir.mkdir(exist_ok=True)
    
    for nombre, ruta in directorios_base.items():
        print(f"\n🔄 Buscando simulaciones en: {nombre}")
        
        # Encontrar todas las simulaciones con archivos .cc3d
        sub_simulaciones = encontrar_simulaciones_cc3d(ruta)
        
        if not sub_simulaciones:
            print(f"  ℹ️ No se encontraron simulaciones en {nombre}")
            continue
            
        # Procesar cada sub-simulación encontrada
        for sub_sim in sub_simulaciones:
            origen = os.path.join(ruta, sub_sim)
            destino = projects_dir / nombre / sub_sim
            print(f"  📁 Procesando: {sub_sim}")
            copiar_simulacion(origen, destino)
        
        print(f"✅ Procesado directorio {nombre}")

if __name__ == "__main__":
    main() 