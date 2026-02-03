from abc import ABC, abstractmethod


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file) -> dict[str, list[dict]]:
        """Should return a standardized dict: {'model_name': [data_list]}"""
        pass
