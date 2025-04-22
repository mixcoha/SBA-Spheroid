import sys
from cc3d import CompuCellSetup
from steady_state_simulationSteppables import *

CompuCellSetup.register_steppable(ConstraintInitializerSteppable(frequency=1))
CompuCellSetup.register_steppable(GrowthSteppable(frequency=1))
CompuCellSetup.register_steppable(MitosisSteppable(frequency=1))
CompuCellSetup.register_steppable(DeathSteppable(frequency=1))
CompuCellSetup.register_steppable(MutationSteppable(frequency=1))

CompuCellSetup.run() 