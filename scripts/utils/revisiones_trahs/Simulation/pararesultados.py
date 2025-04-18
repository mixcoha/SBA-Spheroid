
from cc3d import CompuCellSetup
        


from pararesultadosSteppables import ConstraintInitializerSteppable

CompuCellSetup.register_steppable(steppable=ConstraintInitializerSteppable(frequency=1))




from pararesultadosSteppables import GrowthSteppable

CompuCellSetup.register_steppable(steppable=GrowthSteppable(frequency=1))




from pararesultadosSteppables import MitosisSteppable

CompuCellSetup.register_steppable(steppable=MitosisSteppable(frequency=1))




from pararesultadosSteppables import DeathSteppable

CompuCellSetup.register_steppable(steppable=DeathSteppable(frequency=1))



from pararesultadosSteppables import MutationSteppable

CompuCellSetup.register_steppable(steppable=MutationSteppable(frequency=1))

CompuCellSetup.run()
