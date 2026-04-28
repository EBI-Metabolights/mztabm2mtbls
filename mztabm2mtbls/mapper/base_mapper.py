from abc import ABC, abstractmethod

from metabolights_utils.models.metabolights.model import MetabolightsStudyModel
from mztab_m_io.model.mztabm import MzTabM


class BaseMapper(ABC):
    @abstractmethod
    def update(self, mztab_model: MzTabM, mtbls_model: MetabolightsStudyModel):
        pass
