#!/usr/bin/env python3
"""
Script de utilidad para limpiar y mantener el directorio de trabajo de CompuCell3D.
Este script ayuda a identificar y limpiar simulaciones incompletas o inactivas.
"""

import os
import time
from pathlib import Path
from datetime import datetime
import shutil
from typing import List, Dict, Any

# Ruta por defecto al directorio de trabajo de CompuCell3D
DEFAULT_WORKSPACE = "/Users/mixcoha/CC3DWorkspace"

def analizar_simulaciones(directorio_base: str = DEFAULT_WORKSPACE, horas_inactividad: int = 12) -> List[Dict[str, Any]]:
    """
    Analiza el estado de las simulaciones en el directorio especificado.
    
    Args:
        directorio_base (str): Ruta al directorio de trabajo de CompuCell3D
        horas_inactividad (int): Horas de inactividad para considerar una simulación como inactiva
        
    Returns:
        List[Dict[str, Any]]: Lista de diccionarios con información de cada simulación
    """
    ahora = time.time()
    resultados = []

    for carpeta in Path(directorio_base).iterdir():
        if not carpeta.is_dir():
            continue
        
        latticedata = carpeta / "latticedata"
        confield_dirs = [d for d in carpeta.iterdir() if d.is_dir() and d.name.endswith("_COnField")]

        vtk_archivos = list(latticedata.glob("*.vtk")) if latticedata.exists() else []
        png_archivos = [png for d in confield_dirs for png in d.glob("*.png")]

        ultima_mod = max((f.stat().st_mtime for f in carpeta.rglob("*") if f.is_file()), default=0)
        tiempo_inactivo_horas = (time.time() - ultima_mod) / 3600
        tamaño_total = sum(f.stat().st_size for f in carpeta.rglob("*") if f.is_file()) / (1024**3)

        if vtk_archivos or png_archivos:
            estado = "✅ Finalizada" if tiempo_inactivo_horas < horas_inactividad else "✅ (Inactiva)"
        else:
            estado = "⚠️ Incompleta" if tiempo_inactivo_horas > horas_inactividad else "⏳ En proceso"

        resultados.append({
            "path": carpeta,
            "Simulación": carpeta.name,
            "Estado": estado,
            "VTK archivos": len(vtk_archivos),
            "PNG archivos": len(png_archivos),
            "Última modificación": datetime.fromtimestamp(ultima_mod).strftime("%Y-%m-%d %H:%M:%S"),
            "Inactiva (hrs)": round(tiempo_inactivo_horas, 1),
            "Tamaño (GB)": round(tamaño_total, 2)
        })

    return resultados

def borrar_simulaciones_incompletas(resultados: List[Dict[str, Any]]) -> None:
    """
    Borra las simulaciones marcadas como incompletas después de confirmación del usuario.
    
    Args:
        resultados (List[Dict[str, Any]]): Lista de resultados del análisis de simulaciones
    """
    incompletas = [r for r in resultados if r["Estado"] == "⚠️ Incompleta"]

    if not incompletas:
        print("No se encontraron simulaciones incompletas.")
        return

    print("\nSimulaciones incompletas encontradas:")
    for r in incompletas:
        print(f" - {r['Simulación']} ({r['Tamaño (GB)']} GB, inactiva {r['Inactiva (hrs)']}h)")

    respuesta = input("¿Deseas borrar estas carpetas? (sí/no): ").lower().strip()
    if respuesta in ['sí', 'si', 's']:
        for r in incompletas:
            try:
                shutil.rmtree(r["path"])
                print(f"✔️ Borrado: {r['Simulación']}")
            except Exception as e:
                print(f"❌ Error al borrar {r['Simulación']}: {e}")
        print("Limpieza completada.")
    else:
        print("Operación cancelada.")

def main():
    """Función principal para ejecutar el script desde la línea de comandos."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Limpia simulaciones incompletas de CompuCell3D")
    parser.add_argument("--directorio", default=DEFAULT_WORKSPACE, 
                      help=f"Ruta al directorio de trabajo de CompuCell3D (default: {DEFAULT_WORKSPACE})")
    parser.add_argument("--horas", type=int, default=12, 
                      help="Horas de inactividad para considerar una simulación como inactiva (default: 12)")
    
    args = parser.parse_args()
    
    print(f"Analizando simulaciones en: {args.directorio}")
    resultados = analizar_simulaciones(args.directorio, args.horas)
    borrar_simulaciones_incompletas(resultados)

if __name__ == "__main__":
    main()