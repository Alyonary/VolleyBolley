import django_filters
from django.contrib.auth import get_user_model

User = get_user_model()


class PlayerLevelCountryFilter(django_filters.FilterSet):
    """Кастомный фильтр для поиска игроков по уровню и локации."""

    level = django_filters.ChoiceFilter(
        field_name='game_skill_level',
        choices=User.GameSkillLevel.choices,
        lookup_expr='iexact',
    )
    country = django_filters.CharFilter(
        field_name='location__country',
        lookup_expr='iexact',
    )

    class Meta:
        model = User
        fields = ('level', 'country')
