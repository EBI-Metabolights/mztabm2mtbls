from abc import ABC, abstractmethod

from metabolights_utils.models.metabolights.model import MetabolightsStudyModel

from mztabm2mtbls.mztab2 import MzTab


class BaseMapper(ABC):
    @abstractmethod
    def update(self, mztab_model: MzTab, mtbls_model: MetabolightsStudyModel):
        pass
