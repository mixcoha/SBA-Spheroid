import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from scipy.spatial import distance, ConvexHull
from sklearn.cluster import DBSCAN
import vtk
from vtk.util.numpy_support import vtk_to_numpy
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

# Configuración de estilo de matplotlib
plt.style.use('default')  # Usar estilo por defecto en lugar de seaborn
plt.rcParams.update({
    'figure.figsize': (10, 6),
    'font.size': 12,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'legend.framealpha': 0.8,
    'legend.edgecolor': 'black'
})

def calcular_centroide(puntos):
    return np.mean(puntos, axis=0)

def calcular_area_superficie(puntos):
    # Implementación básica de área superficial usando la envolvente convexa
    hull = distance.pdist(puntos)
    return np.sum(hull)

def calcular_elongacion(puntos):
    # Cálculo de la elongación usando PCA
    cov_matrix = np.cov(puntos.T)
    eigenvalues = np.linalg.eigvals(cov_matrix)
    return np.max(eigenvalues) / np.min(eigenvalues)

def analizar_vecindad(celltypes, posiciones, radio=1.5):
    # Análisis de vecindad usando DBSCAN
    clustering = DBSCAN(eps=radio, min_samples=2).fit(posiciones)
    labels = clustering.labels_
    
    # Contar clusters por tipo de célula
    clusters_por_tipo = {}
    for tipo in np.unique(celltypes):
        mask = celltypes == tipo
        clusters_tipo = labels[mask]
        clusters_por_tipo[tipo] = len(np.unique(clusters_tipo[clusters_tipo != -1]))
    
    return clusters_por_tipo

def calcular_transiciones(estado_anterior, estado_actual):
    transiciones = np.zeros((5, 5))  # 5 tipos de células (0-4)
    for i in range(len(estado_anterior)):
        transiciones[estado_anterior[i], estado_actual[i]] += 1
    return transiciones

def calcular_compacidad(puntos):
    # Cálculo de la compacidad usando la relación entre volumen y área superficial
    try:
        hull = ConvexHull(puntos)
        volumen = hull.volume
        area = hull.area
        return (36 * np.pi * volumen**2) / (area**3)  # Índice de compacidad
    except:
        return np.nan

def calcular_crecimiento(df_anterior, df_actual):
    # Cálculo de tasas de crecimiento
    tasas = {}
    for tipo in [1, 2, 3, 4]:
        num_anterior = df_anterior[df_anterior["Tipo"] == tipo]["Numero"].sum()
        num_actual = df_actual[df_actual["Tipo"] == tipo]["Numero"].sum()
        if num_anterior > 0:
            tasa = (num_actual - num_anterior) / num_anterior
            tasas[tipo] = tasa
    return tasas

def visualizar_3D(posiciones, celltypes, mcs, output_dir):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Colores para cada tipo de célula
    colores = {1: 'blue', 2: 'green', 3: 'red', 4: 'purple'}
    nombres = {1: 'PROL', 2: 'RESE', 3: 'INVA', 4: 'NECR'}
    
    for tipo in [1, 2, 3, 4]:
        mask = celltypes == tipo
        if np.any(mask):
            puntos_tipo = posiciones[mask]
            ax.scatter(puntos_tipo[:, 0], puntos_tipo[:, 1], puntos_tipo[:, 2],
                      c=colores[tipo], label=nombres[tipo], alpha=0.6)
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title(f'Distribución espacial - MCS: {mcs}')
    ax.legend()
    
    # Guardar la visualización
    plt.savefig(os.path.join(output_dir, f'distribucion_3d_mcs_{mcs}.png'))
    plt.close()

# Configuración:
carpeta_vtk = "/Users/mixcoha/CC3DWorkspace/steady_state_simulation_cc3d_04_21_2025_20_27_45_900265/LatticeData"

# Verificar que la carpeta existe
if not os.path.exists(carpeta_vtk):
    print(f"❌ Error: La carpeta '{carpeta_vtk}' no existe")
    exit(1)

# Crear lista de archivos VTK ordenados
archivos_vtk = sorted(glob.glob(os.path.join(carpeta_vtk, "*.vtk")))

if not archivos_vtk:
    print(f"❌ Error: No se encontraron archivos .vtk en la carpeta '{carpeta_vtk}'")
    exit(1)

print(f"📂 Encontrados {len(archivos_vtk)} archivos VTK")

# Obtener la lista de campos disponibles del primer archivo
reader = vtk.vtkStructuredPointsReader()
reader.SetFileName(archivos_vtk[0])
reader.Update()
data = reader.GetOutput()
point_data = data.GetPointData()

campos_disponibles = []
for i in range(point_data.GetNumberOfArrays()):
    nombre_campo = point_data.GetArrayName(i)
    campos_disponibles.append(nombre_campo)

print("\n📊 Campos disponibles en los archivos VTK:")
for campo in campos_disponibles:
    print(f"  - {campo}")

# Inicializar DataFrames para diferentes análisis
datos_morfologia = []
datos_transiciones = []
datos_vecindad = []
datos_gradientes = []
datos_compacidad = []
datos_crecimiento = []
datos_distribucion = []

estado_anterior = None

# Crear directorio para visualizaciones 3D
output_3d_dir = os.path.join(carpeta_vtk, "visualizaciones_3d")
os.makedirs(output_3d_dir, exist_ok=True)

for archivo in archivos_vtk:
    try:
        reader = vtk.vtkStructuredPointsReader()
        reader.SetFileName(archivo)
        reader.Update()

        data = reader.GetOutput()
        point_data = data.GetPointData()
        
        # Obtener MCS del nombre del archivo
        mcs = int(os.path.basename(archivo).split("_")[1].split(".")[0])
        
        # Obtener coordenadas y tipos de células
        celltypes = vtk_to_numpy(point_data.GetArray("CellType"))
        posiciones = np.array([data.GetPoint(i) for i in range(data.GetNumberOfPoints())])
        
        # Análisis morfológico
        for tipo in [1, 2, 3, 4]:  # Tipos de células
            mask = celltypes == tipo
            if np.any(mask):
                puntos_tipo = posiciones[mask]
                morfologia = {
                    "MCS": mcs,
                    "Tipo": tipo,
                    "Numero": np.sum(mask),
                    "Area": calcular_area_superficie(puntos_tipo),
                    "Elongacion": calcular_elongacion(puntos_tipo),
                    "Centroide_X": calcular_centroide(puntos_tipo)[0],
                    "Centroide_Y": calcular_centroide(puntos_tipo)[1],
                    "Centroide_Z": calcular_centroide(puntos_tipo)[2]
                }
                datos_morfologia.append(morfologia)
        
        # Análisis de transiciones
        if estado_anterior is not None:
            transiciones = calcular_transiciones(estado_anterior, celltypes)
            for i in range(5):
                for j in range(5):
                    if transiciones[i,j] > 0:
                        datos_transiciones.append({
                            "MCS": mcs,
                            "De": i,
                            "A": j,
                            "Cantidad": transiciones[i,j]
                        })
        estado_anterior = celltypes
        
        # Análisis de vecindad
        clusters = analizar_vecindad(celltypes, posiciones)
        for tipo, num_clusters in clusters.items():
            datos_vecindad.append({
                "MCS": mcs,
                "Tipo": tipo,
                "NumClusters": num_clusters
            })
        
        # Análisis de gradientes para campos químicos
        for campo in campos_disponibles:
            if campo != "CellType":
                valores = vtk_to_numpy(point_data.GetArray(campo))
                if len(valores.shape) == 1:  # Solo para campos escalares
                    gradiente = np.gradient(valores.reshape(data.GetDimensions()))
                    magnitud_gradiente = np.sqrt(sum(g**2 for g in gradiente))
                    datos_gradientes.append({
                        "MCS": mcs,
                        "Campo": campo,
                        "Gradiente_Medio": np.mean(magnitud_gradiente),
                        "Gradiente_Max": np.max(magnitud_gradiente)
                    })
        
        # Análisis de compacidad
        for tipo in [1, 2, 3, 4]:
            mask = celltypes == tipo
            if np.any(mask):
                puntos_tipo = posiciones[mask]
                compacidad = calcular_compacidad(puntos_tipo)
                datos_compacidad.append({
                    "MCS": mcs,
                    "Tipo": tipo,
                    "Compacidad": compacidad
                })
        
        # Análisis de crecimiento
        if estado_anterior is not None:
            tasas_crecimiento = calcular_crecimiento(
                pd.DataFrame(datos_morfologia[-4:]),  # Últimos datos de morfología
                pd.DataFrame([m for m in datos_morfologia if m["MCS"] == mcs])
            )
            for tipo, tasa in tasas_crecimiento.items():
                datos_crecimiento.append({
                    "MCS": mcs,
                    "Tipo": tipo,
                    "Tasa_Crecimiento": tasa
                })
        
        # Visualización 3D
        visualizar_3D(posiciones, celltypes, mcs, output_3d_dir)
        
        print(f"✅ Procesado: {os.path.basename(archivo)}")
    except Exception as e:
        print(f"⚠️ Error procesando {archivo}: {str(e)}")
        continue

# Guardar todos los análisis
analisis = {
    "morfologia": pd.DataFrame(datos_morfologia),
    "transiciones": pd.DataFrame(datos_transiciones),
    "vecindad": pd.DataFrame(datos_vecindad),
    "gradientes": pd.DataFrame(datos_gradientes),
    "compacidad": pd.DataFrame(datos_compacidad),
    "crecimiento": pd.DataFrame(datos_crecimiento)
}

for nombre, df in analisis.items():
    if not df.empty:
        output_csv = os.path.join(carpeta_vtk, f"analisis_{nombre}.csv")
        df.to_csv(output_csv, index=False)
        print(f"✅ CSV guardado para {nombre}: {output_csv}")

# Generar gráficos adicionales
try:
    # Gráfico de compacidad
    if not analisis["compacidad"].empty:
        plt.figure()
        for tipo in [1, 2, 3, 4]:
            df_tipo = analisis["compacidad"][analisis["compacidad"]["Tipo"] == tipo]
            if not df_tipo.empty:
                plt.plot(df_tipo["MCS"], df_tipo["Compacidad"], 
                        label=f"Tipo {tipo}", marker='o')
        plt.xlabel("MCS")
        plt.ylabel("Índice de Compacidad")
        plt.title("Evolución de la Compacidad por Tipo de Célula")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(carpeta_vtk, "compacidad_celular.png"))
        plt.close()

    # Gráfico de tasas de crecimiento
    if not analisis["crecimiento"].empty:
        plt.figure()
        for tipo in [1, 2, 3, 4]:
            df_tipo = analisis["crecimiento"][analisis["crecimiento"]["Tipo"] == tipo]
            if not df_tipo.empty:
                plt.plot(df_tipo["MCS"], df_tipo["Tasa_Crecimiento"], 
                        label=f"Tipo {tipo}", marker='o')
        plt.xlabel("MCS")
        plt.ylabel("Tasa de Crecimiento")
        plt.title("Evolución de las Tasas de Crecimiento")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(carpeta_vtk, "tasas_crecimiento.png"))
        plt.close()

except Exception as e:
    print(f"⚠️ Error al generar gráficos: {str(e)}")

print("\n✨ Análisis completado!")