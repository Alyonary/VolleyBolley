import pytest

from apps.core.models import CurrencyType, GameLevel
from apps.locations.models import Country


@pytest.fixture()
def game_levels():
    return GameLevel.objects.create(name=GameLevel.GameLevelChoices.LIGHT)


@pytest.fixture()
def currency_type():
    country, _ = Country.objects.get_or_create(name='Thailand')
    return CurrencyType.objects.create(
        currency_name=CurrencyType.CurrencyNameChoices.THB,
        currency_type=CurrencyType.CurrencyTypeChoices.THB,
        country=country
    )
