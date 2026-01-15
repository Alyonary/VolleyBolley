from apps.core.models import CurrencyType, GameLevel
from apps.core.serializers import CurrencyCreateSerializer, GameLevelSerializer
from apps.courts.models import Court
from apps.courts.serializers import CourtCreateSerializer
from apps.event.models import Game, Tourney
from apps.locations.models import City, Country
from apps.locations.serializers import CityCreateSerializer, CountryCreateSerializer
from apps.players.models import Player
from backend.apps.event.serializers import GameCreateSerializer


class BaseModelMapping:
    """
    Base class for model mapping.
    Subclasses must set self.model, self.serializer, self.can_update.
    """

    def __init__(self):
        self._model = None
        self._serializer = None
        self._name = ''
        self._expected_xlsx_fields = ()

    @property
    def model(self):
        return self._model

    @property
    def serializer(self):
        return self._serializer

    @property
    def name(self):
        return self._name

    @property
    def expected_fields(self):
        return self._expected_xlsx_fields

    def get_serializer_fields(self) -> list[str]:
        """Get non-read-only fields from the serializer."""

        if not self.serializer:
            return []
        return tuple(
            name
            for name, field in self._serializer().get_fields().items()
            if not field.read_only
        )

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
        )


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