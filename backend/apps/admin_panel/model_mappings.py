from typing import Dict, Optional

from apps.core.base import BaseModelMapping
from apps.core.models import CurrencyType, GameLevel
from apps.core.serializers import CurrencyCreateSerializer, GameLevelSerializer
from apps.courts.models import Court
from apps.courts.serializers import CourtCreateSerializer
from apps.event.models import Game, Tourney
from apps.event.serializers import GameCreateSerializer
from apps.locations.models import City, Country
from apps.locations.serializers import (
    CityCreateSerializer,
    CountryCreateSerializer,
)
from apps.players.models import Player


class MappingRegistry:
    """
    Registry for managing model mappings and access control.

    Centralizes the storage of public and private mappings, providing
    access based on the application's debug state.

    Attributes:
        _public_mappings (Dict[str, BaseModelMapping]): Mappings available
            in all environments.
        _private_mappings (Dict[str, BaseModelMapping]): Mappings accessible
            only when debug mode is enabled.
        _is_debug (bool): Flag indicating if extended access is allowed.
    """

    def __init__(self, extended_model_access: bool = False):
        """
        Initialize the registry with predefined mappings.

        Args:
            is_debug (bool): If True, grants access to private models.
                Defaults to False.
        """
        self._public_mappings: Dict[str, 'BaseModelMapping'] = {
            'countries': CountryModelMapping(),
            'cities': CityModelMapping(),
            'courts': CourtModelMapping(),
            'currencies': CurrencyTypeModelMapping(),
            'levels': LevelsModelMapping(),
        }
        self._private_mappings: Dict[str, 'BaseModelMapping'] = {
            'players': PlayerModelMapping(),
            'games': GameModelMapping(),
            'tourneys': TourneyModelMapping(),
        }
        self._extended_model_access = extended_model_access

    def get_all(self) -> Dict[str, 'BaseModelMapping']:
        """
        Retrieve all accessible mappings.

        Returns:
            Dict[str, BaseModelMapping]: A dictionary containing public and
                (if debug is enabled) private model mappings.
        """
        if self._extended_model_access:
            return {**self._public_mappings, **self._private_mappings}
        return self._public_mappings.copy()

    def get_mapping(self, name: str) -> Optional['BaseModelMapping']:
        """
        Get a specific mapping by its identifier.

        Args:
            name (str): The name/key of the model mapping.

        Returns:
            Optional[BaseModelMapping]: The mapping instance if found
                and accessible, otherwise None.
        """
        return self.get_all().get(name)

    def is_private(self, name: str) -> bool:
        """
        Check if a model name belongs to the private registry.

        Args:
            name (str): The name/key to check.

        Returns:
            bool: True if the model is considered private, False otherwise.
        """
        return name in self._private_mappings


class CountryModelMapping(BaseModelMapping):
    """Model mapping for Country."""

    def __init__(self):
        self._name = 'countries'
        self._model = Country
        self._serializer = CountryCreateSerializer
        self._expected_xlsx_fields = self.get_serializer_fields()


class CityModelMapping(BaseModelMapping):
    """Model mapping for City."""

    def __init__(self):
        self._name = 'cities'
        self._model = City
        self._serializer = CityCreateSerializer
        self._expected_xlsx_fields = self.get_serializer_fields()


class CourtModelMapping(BaseModelMapping):
    """Model mapping for Court."""

    def __init__(self):
        self._name = 'courts'
        self._model = Court
        self._serializer = CourtCreateSerializer
        self._expected_xlsx_fields = (
            'longitude',
            'latitude',
            'country',
            'city',
            'court_name',
            'description',
            'working_hours',
            'price_description',
            'contact_type',
            'contact',
            'tags',
        )

    def agregate_model_fields(self, obj_data: list[dict]) -> dict:
        """Aggregate location fields into a nested location dict."""
        location_keys = [
            'longitude',
            'latitude',
            'court_name',
            'country',
            'city',
        ]
        location_data = {
            k: obj_data.pop(k) for k in location_keys if k in obj_data
        }
        obj_data['location'] = location_data
        return obj_data


class PlayerModelMapping(BaseModelMapping):
    """Model mapping for Player."""

    def __init__(self):
        self._name = 'players'
        self._model = Player
        self._serializer = None
        self._expected_xlsx_fields = None


class GameModelMapping(BaseModelMapping):
    """Model mapping for Game."""

    def __init__(self):
        self._name = 'games'
        self._model = Game
        self._serializer = GameCreateSerializer
        self._expected_xlsx_fields = self.get_serializer_fields()

    def agregate_model_fields(self, obj_data: list[dict]) -> dict:
        """Aggregate levels field into a list."""
        obj_data['levels'] = [
            v.strip() for v in obj_data['levels'].split(',') if v.strip()
        ]
        return obj_data


class TourneyModelMapping(BaseModelMapping):
    """Model mapping for Tourney."""

    def __init__(self):
        self._name = 'tourneys'
        self._model = Tourney
        self._serializer = None
        self._expected_xlsx_fields = None


class CurrencyTypeModelMapping(BaseModelMapping):
    """Model mapping for CurrencyType."""

    def __init__(self):
        self._name = 'currencies'
        self._model = CurrencyType
        self._serializer = CurrencyCreateSerializer
        self._expected_xlsx_fields = self.get_serializer_fields()


class LevelsModelMapping(BaseModelMapping):
    """Model mapping for Levels."""

    def __init__(self):
        self._name = 'levels'
        self._model = GameLevel
        self._serializer = GameLevelSerializer
        self._expected_xlsx_fields = self.get_serializer_fields()
