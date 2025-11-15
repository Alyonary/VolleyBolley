import pytest

from apps.core.models import CurrencyType, GameLevel


@pytest.fixture()
def game_levels_light():
    return GameLevel.objects.create(name=GameLevel.GameLevelChoices.LIGHT)


@pytest.fixture()
def game_levels_medium():
    return GameLevel.objects.create(name=GameLevel.GameLevelChoices.MEDIUM)


@pytest.fixture
def game_levels_pro():
    from apps.core.models import GameLevel

    return GameLevel.objects.create(name='PRO')


@pytest.fixture()
def currency_type_thailand(country_thailand):
    return CurrencyType.objects.create(
        currency_name=CurrencyType.CurrencyNameChoices.THB,
        currency_type=CurrencyType.CurrencyTypeChoices.THB,
        country=country_thailand,
    )


@pytest.fixture()
def currency_type_cyprus(country_cyprus):
    return CurrencyType.objects.create(
        currency_name=CurrencyType.CurrencyNameChoices.EUR,
        currency_type=CurrencyType.CurrencyTypeChoices.EUR,
        country=country_cyprus,
    )
