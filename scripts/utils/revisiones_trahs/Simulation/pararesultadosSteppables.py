from cc3d.core.PySteppables import *
import numpy as np
import random
import logging
import gc
import weakref

# Configurar el logger
logging.basicConfig(filename='cambios_simulacion.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Definición de constantes para los tipos de células
CELL_TYPE_PROL = 1  # Proliferativa
CELL_TYPE_RESE = 2  # Reserva
CELL_TYPE_INVA = 3  # Invasiva
CELL_TYPE_NECR = 4  # Necrótica

# Definición de constantes para umbrales y parámetros
MCS_INIT_EVO = 20
O2_THRESHOLD = 10
O2_THRESHOLD_HIPO = 5
GLC_THRESHOLD = 10
GLC_THRESHOLD_HIPO = 5
DEATH_MCS_THRESHOLD = 15
MITOSIS_VOLUME_THRESHOLD = 50
MUTATION_PROBABILITY = 0.01
INITIAL_TARGET_VOLUME = 25
INITIAL_LAMBDA_VOLUME = 2.0
OPTIMAL_H3O = 7.2
GROWTH_RATE_MIN = 0.01
MUTATION_PERC = 0.05
MUTATION_DELAY = 20
MCS_4_CHANGE_H3O = 5

class ConstraintInitializerSteppable(SteppableBasePy):
    def __init__(self, frequency=1):
        super().__init__(frequency)
        self.initialized = False
        self._cell_list = weakref.WeakSet()

    def start(self):
        try:
            if self.initialized:
                return

            for cell in self.cell_list:
                if cell is None:
                    continue
                self._cell_list.add(cell)
                if cell.type in [CELL_TYPE_PROL, CELL_TYPE_RESE, CELL_TYPE_INVA]:
                    cell.targetVolume = INITIAL_TARGET_VOLUME
                    cell.lambdaVolume = INITIAL_LAMBDA_VOLUME
                else:
                    cell.targetVolume = 20
                    cell.lambdaVolume = 50

            self.initialized = True
            gc.collect()
        except Exception as e:
            logging.error(f"Error en ConstraintInitializerSteppable.start: {str(e)}")
            self.initialized = False

class GrowthSteppable(SteppableBasePy):
    def __init__(self, frequency=1):
        super().__init__(frequency)
        self.field_initialized = False
        self.field_cache = {}
        self.required_fields = ['O2', 'GLC', 'H3O', 'LAC']
        self._cell_list = weakref.WeakSet()
        self._dim_cache = None

    def start(self):
        try:
            if self.field_initialized:
                return

            for field_name in self.required_fields:
                if not hasattr(self.field, field_name):
                    logging.error(f"Campo {field_name} no encontrado")
                    return
                
                field = getattr(self.field, field_name)
                if field is None:
                    logging.error(f"Campo {field_name} es None")
                    return
                
                self.field_cache[field_name] = field

            if hasattr(self.field, 'O2'):
                self._dim_cache = self.field.O2.dim
            else:
                logging.error("No se pudo inicializar las dimensiones del campo")
                return

            for cell in self.cell_list:
                if cell is not None:
                    self._cell_list.add(cell)

            self.field_initialized = True
            gc.collect()
        except Exception as e:
            logging.error(f"Error en GrowthSteppable.start: {str(e)}")
            self.field_initialized = False

    def get_metabolic_values(self, cell):
        try:
            if not self.field_initialized or cell is None or self._dim_cache is None:
                return (0.0, 0.0, 0.0, 0.0)

            x, y, z = int(cell.xCOM), int(cell.yCOM), int(cell.zCOM)
            
            if not (0 <= x < self._dim_cache.x and 0 <= y < self._dim_cache.y and 0 <= z < self._dim_cache.z):
                return (0.0, 0.0, 0.0, 0.0)

            for field_name in self.required_fields:
                if self.field_cache[field_name] is None:
                    logging.error(f"Campo {field_name} en caché es None")
                    return (0.0, 0.0, 0.0, 0.0)

            return (
                self.field_cache['O2'][x, y, z],
                self.field_cache['GLC'][x, y, z],
                self.field_cache['H3O'][x, y, z],
                self.field_cache['LAC'][x, y, z],
            )
        except Exception as e:
            logging.error(f"Error en get_metabolic_values para célula {cell.id if cell else 'None'}: {str(e)}")
            return (0.0, 0.0, 0.0, 0.0)

    def step(self, mcs):
        try:
            if not self.field_initialized or self._dim_cache is None:
                return

            cells_to_process = [cell for cell in self._cell_list 
                              if cell is not None and cell.type != CELL_TYPE_NECR]
            
            for cell in cells_to_process:
                try:
                    O2_conc, GLC_conc, H3O_conc, LAC_conc = self.get_metabolic_values(cell)
                    self.calculate_growth(cell, O2_conc, GLC_conc, H3O_conc, LAC_conc)
                except Exception as e:
                    logging.error(f"Error procesando célula {cell.id if cell else 'None'}: {str(e)}")
                    continue

            if mcs % 100 == 0:
                gc.collect()
        except Exception as e:
            logging.error(f"Error en GrowthSteppable.step: {str(e)}")

class MitosisSteppable(MitosisSteppableBase):
    def __init__(self, frequency=1):
        super().__init__(frequency)
        self.division_count = 0
        self.max_divisions_per_step = 10

    def step(self, mcs):
        try:
            if mcs < MCS_INIT_EVO:
                return

            cells_to_divide = []
            
            for cell in self.cell_list:
                if cell is None or cell.type == CELL_TYPE_NECR:
                    continue
                
                if cell.volume > MITOSIS_VOLUME_THRESHOLD:
                    cells_to_divide.append(cell)

            # Limitar el número de divisiones por paso
            cells_to_divide = cells_to_divide[:self.max_divisions_per_step]
            self.division_count = 0

            for cell in cells_to_divide:
                if cell is not None and self.division_count < self.max_divisions_per_step:
                    self.divide_cell_random_orientation(cell)
                    self.division_count += 1

            # Limpiar memoria después de las divisiones
            gc.collect()
        except Exception as e:
            logging.error(f"Error en MitosisSteppable.step: {str(e)}")

    def update_attributes(self):
        try:
            if self.parent_cell is None:
                return

            # Copiar atributos y dividir volumen
            self.parent_cell.targetVolume /= 2.0
            self.clone_parent_2_child()
        except Exception as e:
            logging.error(f"Error en update_attributes: {str(e)}")

class DeathSteppable(SteppableBasePy):
    def __init__(self, frequency=1):
        super().__init__(frequency)
        self.critical_condition_counter = {}
        self.field_initialized = False
        self.field_cache = {}

    def start(self):
        try:
            # Verificar que los campos existan
            required_fields = ['O2', 'GLC', 'LAC']
            for field_name in required_fields:
                if not hasattr(self.field, field_name):
                    logging.error(f"Campo {field_name} no encontrado")
                    return
                self.field_cache[field_name] = getattr(self.field, field_name)
            self.field_initialized = True
            gc.collect()  # Limpiar memoria no utilizada
        except Exception as e:
            logging.error(f"Error en DeathSteppable.start: {str(e)}")
            self.field_initialized = False

    def step(self, mcs):
        try:
            if not self.field_initialized or mcs < DEATH_DELAY:
                return

            # Limpiar IDs de células eliminadas
            cell_ids_actuales = {cell.id for cell in self.cell_list if cell is not None}
            ids_a_eliminar = set(self.critical_condition_counter.keys()) - cell_ids_actuales
            for dead_cell_id in ids_a_eliminar:
                del self.critical_condition_counter[dead_cell_id]

            # Limitar el número de células procesadas por paso
            cells_to_process = [cell for cell in self.cell_list 
                              if cell is not None and cell.type != CELL_TYPE_NECR]

            for cell in cells_to_process:
                try:
                    x, y, z = int(cell.xCOM), int(cell.yCOM), int(cell.zCOM)
                    if not (0 <= x < self.dim.x and 0 <= y < self.dim.y and 0 <= z < self.dim.z):
                        continue

                    # Usar caché de campos
                    O2_conc = self.field_cache['O2'][x, y, z]
                    GLC_conc = self.field_cache['GLC'][x, y, z]
                    LAC_conc = self.field_cache['LAC'][x, y, z]

                    if cell.id not in self.critical_condition_counter:
                        self.critical_condition_counter[cell.id] = 0

                    if O2_conc < O2_THRESHOLD_HIPO and GLC_conc < GLC_THRESHOLD_HIPO:
                        if cell.type == CELL_TYPE_INVA and LAC_conc > 0.1:
                            self.critical_condition_counter[cell.id] = max(0, self.critical_condition_counter[cell.id] - 1)
                        else:
                            increment = 0.5 if cell.type == CELL_TYPE_INVA else 1.0
                            self.critical_condition_counter[cell.id] += increment
                    else:
                        decrement = 1.0 if cell.type == CELL_TYPE_INVA else 2.0
                        self.critical_condition_counter[cell.id] = max(0, self.critical_condition_counter[cell.id] - decrement)

                    if self.critical_condition_counter[cell.id] >= DEATH_MCS_THRESHOLD:
                        cell.type = CELL_TYPE_NECR
                        cell.targetVolume = 25
                        cell.lambdaVolume = 50.0
                        del self.critical_condition_counter[cell.id]

                except Exception as e:
                    logging.error(f"Error procesando célula {cell.id if cell else 'None'}: {str(e)}")
                    continue

            # Limpiar memoria periódicamente
            if mcs % 100 == 0:
                gc.collect()
        except Exception as e:
            logging.error(f"Error en DeathSteppable.step: {str(e)}")

class MutationSteppable(SteppableBasePy):
    def __init__(self, frequency=1):
        super().__init__(frequency)
        self.mutation_count = 0
        self.mutation_interval = 100
        self.cell_conditions = {}
        self.mutation_percentage = MUTATION_PERC
        self.initial_mutation_delay = MUTATION_DELAY
        self.field_initialized = False
        self.field_cache = {}
        self.max_mutations_per_step = 5

    def start(self):
        try:
            # Verificar que los campos existan
            required_fields = ['O2', 'GLC', 'LAC']
            for field_name in required_fields:
                if not hasattr(self.field, field_name):
                    logging.error(f"Campo {field_name} no encontrado")
                    return
                self.field_cache[field_name] = getattr(self.field, field_name)
            self.field_initialized = True
            gc.collect()  # Limpiar memoria no utilizada
        except Exception as e:
            logging.error(f"Error en MutationSteppable.start: {str(e)}")
            self.field_initialized = False

    def step(self, mcs):
        try:
            if not self.field_initialized or mcs < self.initial_mutation_delay:
                return

            # Limitar el número de células procesadas por paso
            cells_to_process = [cell for cell in self.cell_list 
                              if cell is not None and cell.type != CELL_TYPE_NECR]

            for cell in cells_to_process:
                try:
                    x, y, z = int(cell.xCOM), int(cell.yCOM), int(cell.zCOM)
                    if not (0 <= x < self.dim.x and 0 <= y < self.dim.y and 0 <= z < self.dim.z):
                        continue

                    # Usar caché de campos
                    O2_conc = self.field_cache['O2'][x, y, z]
                    GLC_conc = self.field_cache['GLC'][x, y, z]
                    LAC_conc = self.field_cache['LAC'][x, y, z]

                    self.check_and_mutate(cell, O2_conc, GLC_conc, LAC_conc, mcs)
                    self.update_condition_counters(cell, O2_conc, GLC_conc, LAC_conc)
                    self.apply_phenotype_changes(cell, mcs)

                except Exception as e:
                    logging.error(f"Error procesando célula {cell.id if cell else 'None'}: {str(e)}")
                    continue

            self.perform_random_mutations(mcs)

            # Limpiar memoria periódicamente
            if mcs % 100 == 0:
                gc.collect()
        except Exception as e:
            logging.error(f"Error en MutationSteppable.step: {str(e)}")
    
    def check_and_mutate(self, cell, O2_conc, GLC_conc, LAC_conc, mcs):
        """Verifica si una célula puede mutar según las condiciones del microambiente."""
        try:
            if cell is None or cell.type not in [CELL_TYPE_PROL, CELL_TYPE_RESE, CELL_TYPE_INVA]:
                return

            if O2_conc < O2_THRESHOLD_HIPO and GLC_conc < GLC_THRESHOLD_HIPO:
                new_type = self.get_new_cell_type(cell.type)
                cell.type = new_type
                self.mutation_count += 1
                logging.info(f"🔬 Célula {cell.id} mutó a tipo {new_type} debido a hipoxia en MCS {mcs}.")
        except Exception as e:
            logging.error(f"Error en check_and_mutate: {str(e)}")
                            
    def update_condition_counters(self, cell, O2_conc, GLC_conc, LAC_conc):
        """Actualiza contadores basados en el entorno metabólico."""
        try:
            if cell is None or cell.id is None:
                return

            if cell.id not in self.cell_conditions:
                self.cell_conditions[cell.id] = {
                    'low_O2_low_glu': 0,
                    'low_O2_low_glu_prol_to_rese': 0,
                    'high_O2_high_glu_rese_to_prol': 0,
                    'low_O2_low_glu_rese_to_inva': 0,
                    'high_O2_high_glu_inva_to_rese': 0,
                }

            conditions = self.cell_conditions[cell.id]
        
            if cell.type == CELL_TYPE_PROL and (O2_THRESHOLD >= O2_conc and GLC_THRESHOLD >= GLC_conc):
                conditions['low_O2_low_glu_prol_to_rese'] += 1
                logging.info(f"⚠️ Célula {cell.id} (PROL) puede volverse RESE en {MCS_4_CHANGE_H3O - conditions['low_O2_low_glu_prol_to_rese']} MCS")
            else:
                conditions['low_O2_low_glu_prol_to_rese'] = 0
        
            if cell.type == CELL_TYPE_RESE and (O2_THRESHOLD < O2_conc and GLC_conc > GLC_THRESHOLD):
                conditions['high_O2_high_glu_rese_to_prol'] += 1
                logging.info(f"🟢 Célula {cell.id} (RESE) puede volverse PROL en {MCS_4_CHANGE_H3O - conditions['high_O2_high_glu_rese_to_prol']} MCS")
            else:
                conditions['high_O2_high_glu_rese_to_prol'] = 0
        
            if cell.type == CELL_TYPE_RESE and (O2_THRESHOLD_HIPO >= O2_conc and GLC_THRESHOLD_HIPO >= GLC_conc):
                conditions['low_O2_low_glu_rese_to_inva'] += 1
                logging.info(f"⚠️ Célula {cell.id} (RESE) puede volverse INVA en {MCS_4_CHANGE_H3O - conditions['low_O2_low_glu_rese_to_inva']} MCS")
            else:
                conditions['low_O2_low_glu_rese_to_inva'] = 0
        
            if cell.type == CELL_TYPE_INVA and (O2_THRESHOLD_HIPO < O2_conc and GLC_THRESHOLD_HIPO < GLC_conc):
                conditions['high_O2_high_glu_inva_to_rese'] += 1
                logging.info(f"🟢 Célula {cell.id} (INVA) puede volverse RESE en {MCS_4_CHANGE_H3O - conditions['high_O2_high_glu_inva_to_rese']} MCS")
            else:
                conditions['high_O2_high_glu_inva_to_rese'] = 0
        except Exception as e:
            logging.error(f"Error en update_condition_counters: {str(e)}")

    def apply_phenotype_changes(self, cell, mcs):
        """Aplica cambios fenotípicos si se cumplen las condiciones metabólicas."""
        try:
            if cell is None or cell.id is None or mcs < self.initial_mutation_delay:
                return

            if cell.id not in self.cell_conditions:
                return

            conditions = self.cell_conditions[cell.id]

            if conditions['low_O2_low_glu_prol_to_rese'] >= MCS_4_CHANGE_H3O:
                cell.type = CELL_TYPE_RESE
                logging.info(f"🔄 Cambio: PROL a RESE en célula {cell.id} (MCS {mcs})")
            elif conditions['high_O2_high_glu_rese_to_prol'] >= MCS_4_CHANGE_H3O:
                cell.type = CELL_TYPE_PROL
                logging.info(f"🔄 Cambio: RESE a PROL en célula {cell.id} (MCS {mcs})")
            elif conditions['low_O2_low_glu_rese_to_inva'] >= MCS_4_CHANGE_H3O:
                cell.type = CELL_TYPE_INVA
                logging.info(f"🔄 Cambio: RESE a INVA en célula {cell.id} (MCS {mcs})")
            elif conditions['high_O2_high_glu_inva_to_rese'] >= MCS_4_CHANGE_H3O:
                cell.type = CELL_TYPE_RESE
                logging.info(f"🔄 Cambio: INVA a RESE en célula {cell.id} (MCS {mcs})")
        except Exception as e:
            logging.error(f"Error en apply_phenotype_changes: {str(e)}")

    def get_new_cell_type(self, current_type):
        """Devuelve un nuevo tipo de célula basado en el tipo actual."""
        try:
            if current_type == CELL_TYPE_PROL:
                return random.choice([CELL_TYPE_RESE, CELL_TYPE_INVA])
            elif current_type == CELL_TYPE_RESE:
                return random.choice([CELL_TYPE_PROL, CELL_TYPE_INVA])
            else:
                return random.choice([CELL_TYPE_PROL, CELL_TYPE_RESE])
        except Exception as e:
            logging.error(f"Error en get_new_cell_type: {str(e)}")
            return current_type
                
    def perform_random_mutations(self, mcs):
        """Realiza mutaciones aleatorias en células cada `mutation_interval` pasos."""
        try:
            if mcs < self.initial_mutation_delay or mcs % self.mutation_interval != 0:
                return

            eligible_cells = [cell for cell in self.cell_list 
                            if cell is not None and cell.type in [CELL_TYPE_PROL, CELL_TYPE_RESE, CELL_TYPE_INVA]]
            
            if not eligible_cells:
                return

            # Limitar el número de mutaciones por paso
            num_mutations = min(self.max_mutations_per_step, 
                              max(1, int(len(eligible_cells) * self.mutation_percentage)))
            cells_to_mutate = random.sample(eligible_cells, min(num_mutations, len(eligible_cells)))

            for cell in cells_to_mutate:
                if cell is None:
                    continue
                new_type = self.get_new_cell_type(cell.type)
                cell.type = new_type
                self.mutation_count += 1
                logging.info(f"🔀 Mutación aleatoria: Célula {cell.id} ahora es tipo {new_type} en MCS {mcs}.")

            # Limpiar memoria después de las mutaciones
            gc.collect()
        except Exception as e:
            logging.error(f"Error en perform_random_mutations: {str(e)}")

