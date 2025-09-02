import pytest

from apps.core.models import CurrencyType, GameLevel


@pytest.fixture()
def game_levels():
    return GameLevel.objects.create(name=GameLevel.GameLevelChoices.LIGHT)


@pytest.fixture()
def currency_type():
    return CurrencyType.objects.create(
        currency_name=CurrencyType.CurrencyNameChoices.THB,
        currency_type=CurrencyType.CurrencyTypeChoices.THB
    )
