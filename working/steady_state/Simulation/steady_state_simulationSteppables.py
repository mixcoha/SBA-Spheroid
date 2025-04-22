# ------------- CONFIGURACIÓN GLOBAL -------------
from cc3d.core.PySteppables import *
from cc3d import CompuCellSetup
import numpy as np
import random
import logging
import gc
import os
import tracemalloc
import csv

class LoggerConfig:
    _instance = None
    _initialized = False
    _loggers = {}
    _output_dir = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerConfig, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self._output_dir = os.path.join(current_dir, "results")
            print(f"📁 Directorio de salida configurado en: {self._output_dir}")
            os.makedirs(self._output_dir, exist_ok=True)

            # Configura solo el logger principal inicialmente
            self.setup_logger('SimulationLogger', os.path.join(self._output_dir, "simulation.log"))

    def setup_logger(self, name, filepath):
        """Configura un logger individual."""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        # Evitar duplicar handlers
        if not logger.handlers:
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

            file_handler = logging.FileHandler(filepath, mode='w')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            if name == 'SimulationLogger':
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)

        self._loggers[name] = logger

    @classmethod
    def get_logger(cls, name='SimulationLogger'):
        """Obtiene o crea el logger que se necesite."""
        instance = cls()
        if name not in instance._loggers:
            # Si no existe todavía ese logger, lo crea
            log_filename = f"{name.lower()}.log"
            filepath = os.path.join(instance._output_dir, log_filename)
            instance.setup_logger(name, filepath)
        return instance._loggers[name]

    @classmethod
    def get_output_dir(cls):
        """Obtiene el directorio de salida."""
        instance = cls()
        return instance._output_dir

# Singleton del logger
logger_main = LoggerConfig.get_logger()

# -----------------------------------------------------------------------------------
# Definición de constantes para la simulación
#  Fuentes de datos experimentales:
# - Volumen celular y tiempos de duplicación:
#   - Chen et al., 2013, "Single-cell analysis of cell size and cell cycle phase in MCF7 cells"
#   - Sinha et al., 2011, "Cell volume and drug uptake in MCF7 breast cancer cells"
#   - Gong et al., 2015, "Tracking volume and density of MCF7 cells using digital holographic microscopy"
# - Consumo metabólico (glucosa, oxígeno):
#   - Basado en simulaciones de CompuCell3D de tejido tumoral estándar.
#   - Consumo tumoral de glucosa: Cancer Res, 1988 ([enlace](http://cancerres.aacrjournals.org/content/48/24_Part_1/7264.short)).
#
#  Justificación de tiempos de transición fenotípica y muerte celular:
# - Tiempos de ciclo celular: ~30-50 horas para células tumorales MCF7 bajo condiciones favorables.
# - Transiciones de estrés/muerte definidas en escalas de:
#   - 6–12 horas (transición leve: PROL → RESE)
#   - 24–48 horas (transición severa: RESE → INVA)
#   - 8–12 horas (recuperación: RESE → PROL)
#   - 16–48 horas (reversión: INVA → RESE)
# - Muerte celular: Acumulación de daño severo ≥15 horas continuas (DEATH_DELAY + DEATH_MCS_THRESHOLD).
# -----------------------------------------------------------------------------------

# Definición de constantes para los tipos de células
CELL_TYPE_PROL = 1  # Proliferativa
CELL_TYPE_RESE = 2  # Reserva
CELL_TYPE_INVA = 3  # Invasiva
CELL_TYPE_NECR = 4  # Necrótica

# Definición de constantes para umbrales y parámetros metabólicos
o2_THRESHOLD = 180  # µM - nivel óptimo de oxígeno
o2_THRESHOLD_HIPO = 15  # µM - hipoxia severa
glc_THRESHOLD = 10  # mM - concentración alta de glucosa
glc_THRESHOLD_HIPO = 0.5  # mM - hipoglucemia severa
lac_THRESHOLD_ACIDIC = 10  # mM - estrés ácido
lac_THRESHOLD_TOXIC = 20   # mM - toxicidad severa

# Parámetros de volumen y crecimiento
MCS_INIT_EVO = 7   # (Acortado) ~6 horas para formación inicial del microambiente
INITIAL_TARGET_VOLUME = 32  # voxels (~2048 µm³)
INITIAL_LAMBDA_VOLUME = 2.0
MITOSIS_VOLUME_THRESHOLD = 64  # Volumen duplicado para división
GROWTH_RATE_PROL = 0.22  # voxels por MCS

# pH óptimo para proliferación
OPTIMAL_h3o = 7.2  # pH 7.2 (condiciones fisiológicas)

# Parámetros de mutación y muerte
MUTATION_PERC = 0.05  # 5% de células elegibles para mutar
MUTATION_DELAY = 28  # ~24 horas para permitir microambiente maduro
DEATH_DELAY = 18     # ~15 horas de exposición crítica para activar muerte
MUTATION_PROBABILITY = 0.01  # Baja tasa de mutación aleatoria

# Umbrales de cambio fenotípico (en MCS)
MCS_PROL_TO_RESE = 14     # 6–12 horas (estrés moderado)
MCS_RESE_TO_INVA = 28     # 24–48 horas (estrés severo)
MCS_RESE_TO_PROL = 10      # 8–12 horas (recuperación parcial)
MCS_INVA_TO_RESE = 19     # 16–48 horas (normalización ambiental)
DEATH_MCS_THRESHOLD = 36  # Aumentado de 18 a 36 MCS para dar más tiempo de recuperación

# ------------- FIELDACCESSOR Y ENVIRONMENT -------------

class FieldAccessor:
    def __init__(self, field_obj, default=0.0):
        self.fields = field_obj
        self.default = default
        self.cached_fields = {}
        self.dim = None
        self.logger = LoggerConfig.get_logger('growth')
        self.output_dir = LoggerConfig.get_output_dir()

        try:
            # Obtener el simulador a través del campo
            if hasattr(field_obj, 'simulator'):
                simulator = field_obj.simulator
                if simulator is not None and hasattr(simulator, 'getPotts'):
                    potts = simulator.getPotts()
                    if potts is not None and hasattr(potts, 'getCellFieldG'):
                        cell_field = potts.getCellFieldG()
                        if cell_field is not None:
                            self.dim = cell_field.getDim()
                            self.logger.info("✅ Dimensiones del simulador obtenidas correctamente")
        except Exception as e:
            self.logger.warning(f"⚠️ FieldAccessor: no se pudo obtener dimensiones del simulador: {e}")

    def get(self, cell, field_name):
        """Accede a los campos químicos de manera segura."""
        if cell is None:
            return self.default

        try:
            field_name = field_name.lower()

            if field_name not in self.cached_fields:
                if hasattr(self.fields, field_name):
                    field = getattr(self.fields, field_name)
                    if field is not None:
                        self.cached_fields[field_name] = field
                    else:
                        self.logger.warning(f"⚠️ Campo '{field_name}' es None")
                        return self.default
                else:
                    self.logger.warning(f"⚠️ Campo '{field_name}' no disponible")
                    return self.default

            field = self.cached_fields.get(field_name)
            if field is None:
                return self.default

            # Verificar que las coordenadas existen
            if not all(hasattr(cell, attr) for attr in ['xCOM', 'yCOM', 'zCOM']):
                return self.default

            x, y, z = int(cell.xCOM), int(cell.yCOM), int(cell.zCOM)

            if self.dim:
                if not (0 <= x < self.dim.x and 0 <= y < self.dim.y and 0 <= z < self.dim.z):
                    self.logger.warning(f"⚠️ Coordenadas fuera de rango para célula {getattr(cell, 'id', 'None')}: ({x}, {y}, {z})")
                    return self.default

            return field[x, y, z]

        except Exception as e:
            self.logger.warning(f"⚠️ Error accediendo a campo '{field_name}' en célula {getattr(cell, 'id', 'None')}: {e}")
            return self.default

class EnvironmentEvaluator:
    def __init__(self, field_accessor):
        self.fields = field_accessor
        self.logger = LoggerConfig.get_logger('env_eval')
        self.output_dir = LoggerConfig.get_output_dir()
        
        # Valores metabólicos ideales (condiciones fisiológicas)
        self.O2_OPTIMAL = 180  # µM
        self.GLC_OPTIMAL = 10  # mM
        self.LAC_OPTIMAL = 2.0 # mM
        
        # Tolerancias para considerar condiciones "óptimas"
        self.TOL_O2 = 40
        self.TOL_GLC = 2
        self.TOL_LAC = 1

    def is_optimal(self, cell):
        """Retorna True si el ambiente es óptimo para crecimiento."""
        try:
            o2 = self.fields.get(cell, 'o2')
            glc = self.fields.get(cell, 'glc')
            lac = self.fields.get(cell, 'lac')

            o2_ok = abs(o2 - self.O2_OPTIMAL) <= self.TOL_O2
            glc_ok = abs(glc - self.GLC_OPTIMAL) <= self.TOL_GLC
            lac_ok = abs(lac - self.LAC_OPTIMAL) <= self.TOL_LAC

            if not (o2_ok and glc_ok and lac_ok):
                self.logger.debug(f"🔎 Célula {cell.id}: Ambiente no óptimo (O2={o2:.2f}, GLC={glc:.2f}, LAC={lac:.2f})")

            return o2_ok and glc_ok and lac_ok

        except Exception as e:
            self.logger.error(f"⚠️ Error en is_optimal para célula {getattr(cell, 'id', 'None')}: {e}")
            return False

    def is_stressed(self, cell):
        """Retorna True si el ambiente es muy hostil (hipoxia severa + hipoglucemia severa)."""
        try:
            o2 = self.fields.get(cell, 'o2')
            glc = self.fields.get(cell, 'glc')
            lac = self.fields.get(cell, 'lac')

            o2_stress = o2 < o2_THRESHOLD_HIPO
            glc_stress = glc < glc_THRESHOLD_HIPO
            lac_high = lac > lac_THRESHOLD_ACIDIC  # Estrés ácido moderado

            if o2_stress and glc_stress:
                self.logger.debug(f"⚠️ Célula {cell.id}: Bajo hipoxia severa y baja glucosa (O2={o2:.2f}, GLC={glc:.2f})")

            return o2_stress and glc_stress

        except Exception as e:
            self.logger.error(f"⚠️ Error en is_stressed para célula {getattr(cell, 'id', 'None')}: {e}")
            return False



class ConstraintInitializerSteppable(SteppableBasePy):
    def __init__(self, frequency=1):
        super().__init__(frequency)
        self.logger = LoggerConfig.get_logger('constraint_initializer')
        self.initialized = False

    def start(self):
        """Inicializa volumen y lambda de volumen para todas las células."""
        if self.initialized:
            self.logger.info("🛑 ConstraintInitializerSteppable ya inicializado previamente.")
            return

        try:
            for cell in self.cell_list:
                if cell is None:
                    continue
                
                if cell.type in [CELL_TYPE_PROL, CELL_TYPE_RESE, CELL_TYPE_INVA]:
                    cell.targetVolume = INITIAL_TARGET_VOLUME
                    cell.lambdaVolume = INITIAL_LAMBDA_VOLUME
                else:
                    cell.targetVolume = 20  # Necróticas
                    cell.lambdaVolume = 50

                self.logger.debug(f"📦 Célula {cell.id} (Tipo {cell.type}): TargetVolume={cell.targetVolume}, LambdaVolume={cell.lambdaVolume}")

            self.initialized = True
            self.logger.info("✅ ConstraintInitializerSteppable completado.")
            gc.collect()

        except Exception as e:
            self.logger.error(f"❌ Error en ConstraintInitializerSteppable.start: {e}")
            self.initialized = False

class GrowthSteppable(SteppableBasePy):
    def __init__(self, frequency=1):
        super().__init__(frequency)
        self.logger = LoggerConfig.get_logger('growth')
        self.field_accessor = None
        self.env = None
        self.growth_log = []  # Para guardar todos los registros
        self.initialized = False

    def start(self):
        """Inicializa el acceso a campos químicos y evaluador de ambiente."""
        if self.initialized:
            self.logger.info("🛑 GrowthSteppable ya inicializado.")
            return

        try:
            if not hasattr(self.field, 'o2') or self.field.o2 is None:
                self.logger.error("⚠️ Campo 'o2' no disponible en GrowthSteppable.")
                return

            self.field_accessor = FieldAccessor(self.field)
            self.env = EnvironmentEvaluator(self.field_accessor)
            self.initialized = True
            self.logger.info("✅ GrowthSteppable inicializado correctamente.")
        
        except Exception as e:
            self.logger.error(f"❌ Error en GrowthSteppable.start: {e}")
            self.initialized = False

    def get_metabolic_values(self, cell):
        """Accede a las concentraciones locales de O2, glucosa, H3O+ y lactato."""
        if not self.field_accessor or cell is None:
            return (0.0, 0.0, 0.0, 0.0)

        o2 = self.field_accessor.get(cell, 'o2')
        glc = self.field_accessor.get(cell, 'glc')
        h3o = self.field_accessor.get(cell, 'h3o')
        lac = self.field_accessor.get(cell, 'lac')

        return (o2, glc, h3o, lac)

    def step(self, mcs):
        """Actualiza el crecimiento de células en cada MCS."""
        if not self.initialized or not self.field_accessor or not self.env:
            return

        try:
            for cell in self.cell_list:
                if cell is None or cell.type == CELL_TYPE_NECR:
                    continue

                try:
                    o2_conc, glc_conc, h3o_conc, lac_conc = self.get_metabolic_values(cell)
                    self.calculate_growth(cell, o2_conc, glc_conc, h3o_conc, lac_conc)
                
                except Exception as e:
                    self.logger.error(f"⚠️ Error procesando célula {getattr(cell, 'id', 'None')}: {e}")
                    continue

            if mcs % 100 == 0:
                gc.collect()

        except Exception as e:
            self.logger.error(f"❌ Error en GrowthSteppable.step: {e}")

    def calculate_growth(self, cell, o2, glc, h3o, lac):
        """Calcula y aplica el incremento de volumen celular basado en el microambiente."""
        if not self.env.is_optimal(cell):
            return

        base_growth_rates = {
            CELL_TYPE_PROL: 0.26,
            CELL_TYPE_RESE: 0.13,
            CELL_TYPE_INVA: 0.20
        }

        growth_base = base_growth_rates.get(cell.type, 0.05)

        # Correcciones metabólicas
        effective_glc = max(glc, 0.001)
        effective_o2 = max(o2, 0.001)
        effective_lac = max(lac, 0.001)

        # Factores Michaelis-Menten
        glucose_factor = effective_glc / (0.05 + effective_glc)
        oxygen_factor = effective_o2 / (20.0 + effective_o2)

        # Inhibición por lactato (acidosis)
        lactate_inhibition = 1.0 / (1.0 + (effective_lac / 10.0))

        # Combinación de factores
        total_factor = glucose_factor * oxygen_factor * lactate_inhibition

        delta_volume = growth_base * total_factor

        # Límite máximo de crecimiento
        max_growth = 0.5  # voxels por MCS
        delta_volume = min(delta_volume, max_growth)

        cell.targetVolume += delta_volume

        # Guardar en log
        self.growth_log.append({
            'MCS': self.simulator.getStep(),
            'CellID': cell.id,
            'Type': cell.type,
            'DeltaVolume': round(delta_volume, 4),
            'NewTargetVolume': round(cell.targetVolume, 2),
            'LocalGLC': round(glc, 2),
            'LocalO2': round(o2, 2),
            'LocalLAC': round(lac, 2)
        })

        if self.simulator.getStep() % 100 == 0:
            self.logger.info(f"🌱 MCS {self.simulator.getStep()}: Célula {cell.id} creció {delta_volume:.4f} voxels.")

    def finish(self):
        """Guarda resultados de crecimiento al finalizar la simulación."""
        try:
            logger = LoggerConfig.get_logger('growth')

            # Guardar volumen final
            volumen_path = os.path.join(LoggerConfig.get_output_dir(), "volumen_final_celulas.csv")
            logger.info(f"💾 Guardando {volumen_path}")

            with open(volumen_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Cell ID", "Type", "Current Volume", "Target Volume"])
                for cell in self.cell_list:
                    if cell is None:
                        continue
                    tipo_nombre = {
                        CELL_TYPE_PROL: "PROL",
                        CELL_TYPE_RESE: "RESE",
                        CELL_TYPE_INVA: "INVA",
                        CELL_TYPE_NECR: "NECR"
                    }.get(cell.type, f"Type {cell.type}")
                    writer.writerow([
                        cell.id,
                        tipo_nombre,
                        round(cell.volume, 2),
                        round(cell.targetVolume, 2)
                    ])

            # Guardar log de crecimiento
            growth_log_path = os.path.join(LoggerConfig.get_output_dir(), "growth_log.csv")
            logger.info(f"💾 Guardando {growth_log_path}")

            with open(growth_log_path, "w", newline="") as logfile:
                fieldnames = ['MCS', 'CellID', 'Type', 'DeltaVolume', 'NewTargetVolume', 'LocalGLC', 'LocalO2', 'LocalLAC']
                writer = csv.DictWriter(logfile, fieldnames=fieldnames)
                writer.writeheader()
                for entry in self.growth_log:
                    writer.writerow(entry)

            logger.info("✅ Archivos de crecimiento guardados exitosamente.")

        except Exception as e:
            logger.error(f"❌ Error en GrowthSteppable.finish: {e}")


class MitosisSteppable(MitosisSteppableBase):
    def __init__(self, frequency=1):
        super().__init__(frequency)
        self.logger = LoggerConfig.get_logger('mitosis')
        self.initialized = False

    def start(self):
        try:
            self.initialized = True
            self.logger.info("✅ MitosisSteppable inicializado correctamente")
        except Exception as e:
            self.logger.error(f"❌ Error inicializando MitosisSteppable: {e}")
            self.initialized = False

    def step(self, mcs):
        if not self.initialized:
            return

        if mcs < MCS_INIT_EVO:
            return

        try:
            cells_to_divide = []

            for cell in self.cell_list:
                if cell is None or cell.type == CELL_TYPE_NECR:
                    continue  # ❌ Ignorar células muertas
                if cell.volume > MITOSIS_VOLUME_THRESHOLD:
                    cells_to_divide.append(cell)

            for cell in cells_to_divide:
                self.divide_cell_random_orientation(cell)
                self.logger.info(f"🧬 División: célula {cell.id} dividida en MCS {mcs}")

            if mcs % 100 == 0:
                gc.collect()

        except Exception as e:
            self.logger.error(f"❌ Error en MitosisSteppable.step: {e}")

    def update_attributes(self):
        try:
            parent_cell = self.parent_cell
            parent_cell.targetVolume /= 2.0  # Dividir volumen de la madre en 2
            self.clone_parent_2_child()
        except Exception as e:
            self.logger.error(f"❌ Error en update_attributes de MitosisSteppable: {e}")

    def finish(self):
        """Opcional: mensaje final de cierre"""
        try:
            self.logger.info("🧬 Finalizó MitosisSteppable correctamente")
        except Exception as e:
            print(f"⚠️ Error cerrando MitosisSteppable: {e}")
        
class DeathSteppable(SteppableBasePy):
    def __init__(self, frequency=1):
        super().__init__(frequency)
        self.critical_condition_counter = {}
        self.field_accessor = None
        self.env = None
        self.death_count = 0
        self.logger = LoggerConfig.get_logger('death')
        self.initialized = False

    def start(self):
        try:
            if self.initialized:
                return

            if not hasattr(self, 'field') or self.field is None:
                self.logger.error("⚠️ Campo 'field' no disponible en DeathSteppable")
                return

            if not hasattr(self.field, 'o2') or self.field.o2 is None:
                self.logger.error("⚠️ Campo 'o2' no disponible en DeathSteppable")
                return

            self.field_accessor = FieldAccessor(self.field)
            self.env = EnvironmentEvaluator(self.field_accessor)

            self.initialized = True
            self.logger.info("✅ DeathSteppable inicializado correctamente")
        except Exception as e:
            self.logger.error(f"❌ Error inicializando DeathSteppable: {e}")
            self.initialized = False

    def step(self, mcs):
        if not self.initialized or not self.field_accessor or not self.env:
            return

        if mcs < DEATH_DELAY:
            return

        try:
            # Limpiar IDs de células eliminadas
            cell_ids_actuales = {cell.id for cell in self.cell_list if cell is not None}
            ids_a_eliminar = set(self.critical_condition_counter.keys()) - cell_ids_actuales
            for dead_id in ids_a_eliminar:
                del self.critical_condition_counter[dead_id]

            for cell in self.cell_list:
                if cell is None or cell.type == CELL_TYPE_NECR:
                    continue

                try:
                    o2_conc = self.field_accessor.get(cell, 'o2')
                    glc_conc = self.field_accessor.get(cell, 'glc')
                    lac_conc = self.field_accessor.get(cell, 'lac')

                    if cell.id not in self.critical_condition_counter:
                        self.critical_condition_counter[cell.id] = 0

                    # Estresadas: sumar tiempo de daño
                    if self.env.is_stressed(cell):
                        if cell.type == CELL_TYPE_INVA and lac_conc > lac_THRESHOLD_TOXIC:
                            self.critical_condition_counter[cell.id] = max(0, self.critical_condition_counter[cell.id] - 1)
                        else:
                            self.critical_condition_counter[cell.id] += 1

                    # Recuperación: reducir contador de daño
                    elif o2_conc >= o2_THRESHOLD_HIPO and glc_conc >= glc_THRESHOLD_HIPO:
                        self.critical_condition_counter[cell.id] = max(0, self.critical_condition_counter[cell.id] - 2)

                    # Muerte si excede umbral
                    if self.critical_condition_counter[cell.id] >= DEATH_MCS_THRESHOLD:
                        cell.type = CELL_TYPE_NECR
                        cell.targetVolume = 25
                        cell.lambdaVolume = 50.0
                        self.death_count += 1
                        self.logger.info(f"☠️ Célula {cell.id} murió en MCS {mcs}")

                except Exception as e:
                    self.logger.error(f"❌ Error procesando célula {getattr(cell, 'id', 'Unknown')}: {e}")

            if mcs % 100 == 0:
                gc.collect()

        except Exception as e:
            self.logger.error(f"❌ Error en DeathSteppable.step: {e}")

    def finish(self):
        """Guarda las estadísticas finales de muerte celular."""
        try:
            logger.info(f"📁 Guardando estadísticas de muerte celular...")

            death_stats_path = os.path.join(LoggerConfig.get_output_dir(), "death_stats.csv")
            with open(death_stats_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Total Deaths", "MCS"])
                writer.writerow([self.death_count, self.simulator.getStep()])

            logger.info(f"📁 Archivo 'death_stats.csv' guardado exitosamente")

        except Exception as e:
            logger.error(f"⚠️ Error guardando death_stats.csv: {str(e)}")
            print(f"⚠️ Error guardando death_stats.csv: {str(e)}")

        finally:
            try:
                self.logger.info("🔄 Finalizando DeathSteppable correctamente")
            except Exception as e:
                print(f"⚠️ Error finalizando DeathSteppable: {str(e)}")

                
class MutationSteppable(SteppableBasePy):

    def __init__(self, frequency=1):
        super().__init__(frequency)
        self.mutation_count = 0
        self.mutation_interval = 500
        self.cell_conditions = {}
        self.mutation_percentage = MUTATION_PERC
        self.initial_mutation_delay = MUTATION_DELAY
        self.transition_counts = {
            "PROL→RESE": 0,
            "RESE→INVA": 0,
            "RESE→PROL": 0,
            "INVA→RESE": 0
        }
        self.field_accessor = None
        self.logger = LoggerConfig.get_logger('mutation')
        self.initialized = False

        if not tracemalloc.is_tracing():
            tracemalloc.start()

    def start(self):
        try:
            if self.initialized:
                return

            if not hasattr(self, 'field') or self.field is None:
                self.logger.error("⚠️ Campo 'field' no disponible en MutationSteppable")
                return

            if not hasattr(self.field, 'o2') or self.field.o2 is None:
                self.logger.error("⚠️ Campo 'o2' no disponible en MutationSteppable")
                return

            self.field_accessor = FieldAccessor(self.field)
            self.env = EnvironmentEvaluator(self.field_accessor)

            self.initialized = True
            self.logger.info("✅ MutationSteppable inicializado correctamente")

        except Exception as e:
            self.logger.error(f"❌ Error inicializando MutationSteppable: {e}")
            self.initialized = False


    def step(self, mcs):
        if not self.initialized or not self.field_accessor or mcs < self.initial_mutation_delay:
            return

        if mcs % 10 == 0:
            gc.collect()  # Forzar recolección de basura

            num_cells = sum(1 for cell in self.cell_list if cell.type != CELL_TYPE_NECR)
            snapshot = tracemalloc.take_snapshot()
            memoria_mb = sum(stat.size for stat in snapshot.statistics('lineno')) / (1024 * 1024)

            self.logger.info(f"🔄 MCS {mcs}: {num_cells} células activas, {self.mutation_count} mutaciones, memoria ≈ {memoria_mb:.2f} MB")

        for cell in self.cell_list:
            if cell is None or cell.type == CELL_TYPE_NECR:
                continue

            try:
                o2_conc = self.field_accessor.get(cell, 'o2')
                glc_conc = self.field_accessor.get(cell, 'glc')
                lac_conc = self.field_accessor.get(cell, 'lac')

                self.check_and_mutate(cell, o2_conc, glc_conc, lac_conc, mcs)
                self.update_condition_counters(cell, o2_conc, glc_conc, lac_conc)
                self.apply_phenotype_changes(cell, mcs)

            except Exception as e:
                self.logger.error(f"❌ Error procesando célula {getattr(cell, 'id', 'Unknown')}: {e}")

        self.perform_random_mutations(mcs)
    
    def check_and_mutate(self, cell, o2_conc, glc_conc, lac_conc, mcs):
        """Verifica si una célula puede mutar según las condiciones del microambiente."""
        if cell.type in [CELL_TYPE_PROL, CELL_TYPE_RESE, CELL_TYPE_INVA]:
            if o2_conc < o2_THRESHOLD and glc_conc < glc_THRESHOLD:
                new_type = self.get_new_cell_type(cell.type)
                cell.type = new_type
                self.mutation_count += 1
                self.logger.info(f"🔄 Célula {cell.id} mutó a tipo {new_type} debido a hipoxia en MCS {mcs}.")    
                            
    def update_condition_counters(self, cell, o2_conc, glc_conc, lac_conc):
        """
        Actualiza contadores para transición de fenotipos basada en el entorno metabólico.
        Se consideran los 4 posibles cambios:
        - PROL → RESE
        - RESE → INVA
        - RESE → PROL
        - INVA → RESE
        """
    
        if cell.id not in self.cell_conditions:
            self.cell_conditions[cell.id] = {
                'low_o2_low_glu_prol_to_rese': 0,
                'low_o2_low_glu_rese_to_inva': 0,
                'high_o2_high_glu_rese_to_prol': 0,
                'high_o2_high_glu_inva_to_rese': 0,
            }
    
        conditions = self.cell_conditions[cell.id]
    
        # --------------------------------------
        # → PROLIFERATIVA → RESERVA (estrés leve)
        # --------------------------------------
        if cell.type == CELL_TYPE_PROL and (o2_THRESHOLD_HIPO <= o2_conc <= o2_THRESHOLD and glc_THRESHOLD_HIPO <= glc_conc <= glc_THRESHOLD):
            conditions['low_o2_low_glu_prol_to_rese'] += 1
            self.logger.info(f"🔄 Célula {cell.id} (PROL) puede volverse RESE en {MCS_PROL_TO_RESE - conditions['low_o2_low_glu_prol_to_rese']} MCS")
        else:
            conditions['low_o2_low_glu_prol_to_rese'] = max(0, conditions['low_o2_low_glu_prol_to_rese'] - 2)
    
        # --------------------------------------
        # → RESERVA → INVASIVA (estrés severo)
        # --------------------------------------
        if cell.type == CELL_TYPE_RESE and self.env.is_stressed(cell):
            conditions['low_o2_low_glu_rese_to_inva'] += 1
            self.logger.info(f"🔄 Célula {cell.id} (RESE) en estrés → puede volverse INVA en {MCS_RESE_TO_INVA - conditions['low_o2_low_glu_rese_to_inva']} MCS")
        else:
            conditions['low_o2_low_glu_rese_to_inva'] = max(0, conditions['low_o2_low_glu_rese_to_inva'] - 2)
    
        # --------------------------------------
        # → RESERVA → PROLIFERATIVA (recuperación)
        # --------------------------------------
        if cell.type == CELL_TYPE_RESE:
            if self.env.is_optimal(cell):
                conditions['high_o2_high_glu_rese_to_prol'] += 1
                self.logger.info(f"🔄 Célula {cell.id} (RESE) en ambiente óptimo: revertirá a PROL en {MCS_RESE_TO_PROL - conditions['high_o2_high_glu_rese_to_prol']} MCS")
            elif o2_conc > o2_THRESHOLD_HIPO and glc_conc > glc_THRESHOLD_HIPO:
                conditions['high_o2_high_glu_rese_to_prol'] += 1
                self.logger.info(f"🔄 Célula {cell.id} (RESE) en buenas condiciones: revertirá a PROL en {MCS_RESE_TO_PROL - conditions['high_o2_high_glu_rese_to_prol']} MCS")
            else:
                conditions['high_o2_high_glu_rese_to_prol'] = max(0, conditions['high_o2_high_glu_rese_to_prol'] - 2)
    
        # --------------------------------------
        # → INVASIVA → RESERVA (reversión)
        # --------------------------------------
        if cell.type == CELL_TYPE_INVA:
            if self.env.is_optimal(cell):
                conditions['high_o2_high_glu_inva_to_rese'] += 1
                self.logger.info(f"🔄 Célula {cell.id} (INVA) en ambiente óptimo: revertirá a RESE en {MCS_INVA_TO_RESE - conditions['high_o2_high_glu_inva_to_rese']} MCS")
            elif o2_conc >= o2_THRESHOLD_HIPO and glc_conc >= glc_THRESHOLD_HIPO:
                conditions['high_o2_high_glu_inva_to_rese'] += 1
                self.logger.info(f"🔄 Célula {cell.id} (INVA) en buenas condiciones: revertirá a RESE en {MCS_INVA_TO_RESE - conditions['high_o2_high_glu_inva_to_rese']} MCS")
            else:
                conditions['high_o2_high_glu_inva_to_rese'] = max(0, conditions['high_o2_high_glu_inva_to_rese'] - 2)

    def apply_phenotype_changes(self, cell, mcs):
        """
        Aplica los cambios de fenotipo en la célula según los contadores de condición.
        Cada transición tiene su propio umbral temporal definido en MCS.
        """
    
        if mcs < self.initial_mutation_delay:
            return
    
        conditions = self.cell_conditions[cell.id]
    
        # PROL → RESE
        if conditions['low_o2_low_glu_prol_to_rese'] >= MCS_PROL_TO_RESE:
            cell.type = CELL_TYPE_RESE
            self.transition_counts["PROL→RESE"] += 1
            self.logger.info(f"🔄 PROL → RESE in cell {cell.id} at MCS {mcs}")
    
        # RESE → INVA
        elif conditions['low_o2_low_glu_rese_to_inva'] >= MCS_RESE_TO_INVA:
            cell.type = CELL_TYPE_INVA
            self.transition_counts["RESE→INVA"] += 1
            self.logger.info(f"🔄 RESE → INVA in cell {cell.id} at MCS {mcs}")
    
        # RESE → PROL
        elif conditions['high_o2_high_glu_rese_to_prol'] >= MCS_RESE_TO_PROL:
            cell.type = CELL_TYPE_PROL
            self.transition_counts["RESE→PROL"] += 1
            self.logger.info(f"🔄 RESE → PROL in cell {cell.id} at MCS {mcs}")
    
        # INVA → RESE
        elif conditions['high_o2_high_glu_inva_to_rese'] >= MCS_INVA_TO_RESE:
            cell.type = CELL_TYPE_RESE
            self.transition_counts["INVA→RESE"] += 1
            self.logger.info(f"🔄 INVA → RESE in cell {cell.id} at MCS {mcs}")
    
    def get_new_cell_type(self, current_type):
        """Devuelve un nuevo tipo de célula basado en el tipo actual."""
        if current_type == CELL_TYPE_PROL:
            return random.choice([CELL_TYPE_RESE, CELL_TYPE_INVA])
        elif current_type == CELL_TYPE_RESE:
            return random.choice([CELL_TYPE_PROL, CELL_TYPE_INVA])
        else:
            return random.choice([CELL_TYPE_PROL, CELL_TYPE_RESE])
                
    # def perform_random_mutations(self, mcs):
        # """Realiza mutaciones aleatorias en células cada `mutation_interval` pasos."""
        # if mcs < self.initial_mutation_delay or mcs % self.mutation_interval != 0:
    def perform_random_mutations(self, mcs):
        if mcs % self.mutation_interval != 0:
            return

        eligible_cells = [cell for cell in self.cell_list if cell.type in [CELL_TYPE_PROL, CELL_TYPE_RESE, CELL_TYPE_INVA]]
        if not eligible_cells:
            return

        num_mutations = max(1, int(len(eligible_cells) * self.mutation_percentage))
        cells_to_mutate = random.sample(eligible_cells, min(num_mutations, len(eligible_cells)))

        for cell in cells_to_mutate:
            new_type = self.get_new_cell_type(cell.type)
            cell.type = new_type
            self.mutation_count += 1
            self.logger.info(f"🧬 Mutación aleatoria: Célula {cell.id} ahora es tipo {new_type}")
    

    def finish(self):
        """Guarda los resultados de mutación."""
        try:
            transition_file = os.path.join(LoggerConfig.get_output_dir(), "transition_counts.csv")
            with open(transition_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Transition", "Count"])
                for transition, count in self.transition_counts.items():
                    writer.writerow([transition, count])

            mutation_file = os.path.join(LoggerConfig.get_output_dir(), "mutation_stats.csv")
            with open(mutation_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Total Mutations", "MCS"])
                writer.writerow([self.mutation_count, self.simulator.getStep()])

            self.logger.info(f"📁 Resultados de MutationSteppable guardados correctamente")
        except Exception as e:
            logger.error(f"⚠️ Error guardando resultados de MutationSteppable: {e}")
              
