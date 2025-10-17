from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.constants import GenderChoices
from apps.core.models import CurrencyType, GameLevel
from apps.courts.models import Court, CourtLocation
from apps.event.models import Tourney
from apps.locations.models import City, Country
from apps.players.constants import Genders, Payments, PlayerStrEnums
from apps.players.models import Payment, Player

User = get_user_model()


class Command(BaseCommand):
    help = (
        'Создаёт тестовые данные '
        'для API (страны, города, корты, игрока, платежи, турниры).'
    )

    def handle(self, *args, **kwargs):
        # Страны и города
        cyprus, _ = Country.objects.get_or_create(name='Cyprus')
        thailand, _ = Country.objects.get_or_create(name='Thailand')

        paphos, _ = City.objects.get_or_create(name='Paphos', country=cyprus)
        pattaya, _ = City.objects.get_or_create(
            name='Pattaya', country=thailand)

        # Валюты
        eur, _ = CurrencyType.objects.get_or_create(
            currency_type='EUR', currency_name='€', country=cyprus
        )
        thb, _ = CurrencyType.objects.get_or_create(
            currency_type='THB', currency_name='฿', country=thailand
        )

        # Уровни
        for level in ['LIGHT', 'MEDIUM', 'HARD', 'PRO']:
            GameLevel.objects.get_or_create(name=level)

        # Корт
        location, _ = CourtLocation.objects.get_or_create(
            longitude=33.0,
            latitude=34.7,
            court_name='Test Court',
            country=cyprus,
            city=paphos,
        )
        court, _ = Court.objects.get_or_create(
            location=location, description='Main test court'
        )

        # Пользователь + игрок
        user, _ = User.objects.get_or_create(
            username='testuser',
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@test.com'
            },
        )
        if not hasattr(user, "player"):
            player = Player.objects.create(
                user=user,
                gender=Genders.MALE,
                level='PRO',
                date_of_birth=PlayerStrEnums.DEFAULT_BIRTHDAY.value,
                country=cyprus,
                city=paphos,
                is_registered=True,
            )
        else:
            player = user.player

        # Платёжные данные
        Payment.objects.get_or_create(
            player=player,
            payment_type=Payments.REVOLUT,
            payment_account='123-456',
            is_preferred=True,
        )

        # --- Турниры ---
        now = timezone.now()

        # Будущий турнир (upcoming)
        Tourney.objects.get_or_create(
            message='Future Beach Tournament',
            start_time=now + timedelta(days=5),
            end_time=now + timedelta(days=6),
            is_individual=True,
            gender=GenderChoices.MIX,
            max_players=8,
            maximum_teams=4,
            price_per_person='10.00',
            currency_type=eur,
            payment_type=Payments.REVOLUT,
            payment_account='123-456',
            court=court,
            host=player,
        )

        # Прошедший турнир (archive)
        Tourney.objects.get_or_create(
            message='Past City Cup',
            start_time=now - timedelta(days=10),
            end_time=now - timedelta(days=9),
            is_individual=True,
            gender=GenderChoices.MEN,
            max_players=12,
            maximum_teams=6,
            price_per_person='15.00',
            currency_type=eur,
            payment_type=Payments.REVOLUT,
            payment_account='123-456',
            court=court,
            host=player,
        )

        self.stdout.write(self.style.SUCCESS(
            '✅ Тестовые данные успешно созданы (включая турниры)!'
        ))
