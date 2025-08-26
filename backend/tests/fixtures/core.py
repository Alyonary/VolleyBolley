import pytest

from apps.core.models import CurrencyType, GameLevel, Gender, Payment


@pytest.fixture
def payment_account_revolut(active_user):
    return Payment.objects.create(
        owner=active_user,
        payment_type='REVOLUT',
        payment_account='test revolut account'
    )


@pytest.fixture
def gender_men():
    return Gender.objects.create(name=Gender.GenderChoices.MEN)


@pytest.fixture()
def game_levels():
    return GameLevel.objects.create(name=GameLevel.GameLevelChoices.LIGHT)


@pytest.fixture()
def currency_type():
    return CurrencyType.objects.create(
        currency_name=CurrencyType.CurrencyNameChoices.THB,
        currency_type=CurrencyType.CurrencyTypeChoices.THB
    )
