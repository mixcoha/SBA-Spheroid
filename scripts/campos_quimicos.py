import os
import numpy as np
import matplotlib.pyplot as plt
import vtk
from vtk.util.numpy_support import vtk_to_numpy
from glob import glob
from matplotlib.animation import FuncAnimation

# Carpeta donde están tus archivos .vtk
carpeta_vtk = "/Users/mixcoha/CC3DWorkspace/steady_state_simulation_cc3d_04_21_2025_20_27_45_900265/LatticeData"  # <-- cámbialo

# Listar archivos
archivos = sorted(glob(os.path.join(carpeta_vtk, "*.vtk")))

# Función para leer un campo químico
def leer_campo(nombre_archivo, nombre_campo):
    reader = vtk.vtkStructuredPointsReader()
    reader.SetFileName(nombre_archivo)
    reader.Update()
    data = reader.GetOutput()
    field = data.GetPointData().GetScalars(nombre_campo)
    if field is None:
        raise ValueError(f"Campo '{nombre_campo}' no encontrado en {nombre_archivo}")
    dims = data.GetDimensions()
    array = vtk_to_numpy(field)
    array = array.reshape(dims[::-1])  # reshape en orden (z,y,x)
    return array

# Función para proyección Z
def proyeccion_Z(array, metodo="mean"):
    if metodo == "mean":
        return np.mean(array, axis=0)
    elif metodo == "max":
        return np.max(array, axis=0)
    else:
        raise ValueError("Método no reconocido")

# Función para actualizar la animación
def actualizar(frame):
    nombre_archivo = archivos[frame]
    for idx, (campo, (titulo, cmap)) in enumerate(campos.items()):
        try:
            array = leer_campo(nombre_archivo, campo)
            proy = proyeccion_Z(array, metodo="mean")
            ims[idx].set_array(proy)
        except Exception as e:
            print(f"⚠️ No se pudo cargar campo {campo} en frame {frame}: {e}")
    
    plt.suptitle(f"Proyecciones en Z (archivo: {os.path.basename(nombre_archivo)})", fontsize=18)
    return ims

# Configuración de la figura y los campos
campos = {
    "o2": ("Oxígeno", "plasma"),
    "glc": ("Glucosa", "viridis"),
    "lac": ("Lactato", "inferno"),
    "h3o": ("pH (H3O+)", "magma")
}

fig, axs = plt.subplots(2, 2, figsize=(14, 12))
axs = axs.flatten()
ims = []

# Inicializar las imágenes
for idx, (campo, (titulo, cmap)) in enumerate(campos.items()):
    try:
        array = leer_campo(archivos[0], campo)
        proy = proyeccion_Z(array, metodo="mean")
        im = axs[idx].imshow(proy, cmap=cmap, origin='lower', animated=True)
        axs[idx].set_title(titulo, fontsize=16)
        axs[idx].axis('off')
        fig.colorbar(im, ax=axs[idx], fraction=0.046, pad=0.04)
        ims.append(im)
    except Exception as e:
        axs[idx].set_visible(False)
        print(f"⚠️ No se pudo cargar campo {campo}: {e}")
        ims.append(None)

# Crear la animación
ani = FuncAnimation(fig, actualizar, frames=len(archivos), interval=200, blit=True)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()