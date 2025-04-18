
from cc3d import CompuCellSetup
        


from steady_state_simulationSteppables import ConstraintInitializerSteppable

CompuCellSetup.register_steppable(steppable=ConstraintInitializerSteppable(frequency=1))




from steady_state_simulationSteppables import GrowthSteppable

CompuCellSetup.register_steppable(steppable=GrowthSteppable(frequency=1))




from steady_state_simulationSteppables import MitosisSteppable

CompuCellSetup.register_steppable(steppable=MitosisSteppable(frequency=1))




from steady_state_simulationSteppables import DeathSteppable

CompuCellSetup.register_steppable(steppable=DeathSteppable(frequency=1))




from steady_state_simulationSteppables import MutationSteppable

CompuCellSetup.register_steppable(steppable=MutationSteppable(frequency=1))



CompuCellSetup.run() 