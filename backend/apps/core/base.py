from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file) -> dict[str, list[dict]]:
        """Should return a standardized dict: {'model_name': [data_list]}"""
        pass


class BaseModelMapping(ABC):
    """
    Base class for defining model-to-file mappings.

    Provides core properties and utility methods for extracting fields
    from serializers and aggregating model data.
    """

    @abstractmethod
    def __init__(self) -> None:
        """Initialize base mapping attributes."""
        pass

    @property
    def model(self) -> Any:
        """Return the Django model class."""
        return self._model

    @property
    def serializer(self) -> Any:
        """Return the DRF serializer class."""
        return self._serializer

    @property
    def name(self) -> str:
        """Return the mapping identifier name."""
        return self._name

    @property
    def expected_fields(self) -> Tuple[str, ...]:
        """Return the expected fields for Excel parsing."""
        return self._expected_xlsx_fields

    def get_serializer_fields(self) -> Tuple[str, ...]:
        """
        Extract non-read-only fields from the assigned serializer.

        Returns:
            Tuple[str, ...]: A tuple of field names available for writing.
        """
        if not self.serializer:
            return ()
        return tuple(
            name
            for name, field in self.serializer().get_fields().items()
            if not field.read_only
        )

    def agregate_model_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform data transformation or aggregation for specific models.

        Args:
            data (Dict[str, Any]): Raw data row from file.

        Returns:
            Dict[str, Any]: Processed data ready for serialization.
        """
        return data
