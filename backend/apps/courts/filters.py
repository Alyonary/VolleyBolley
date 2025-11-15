from django_filters import rest_framework as filters

from .models import Court


class CourtFilter(filters.FilterSet):
    """Filter for the Court model.

    Filtering is performed by partial match of the court_name field
    in the related CourtLocation model.
    """

    search = filters.CharFilter(
        field_name='location__court_name', lookup_expr='icontains'
    )

    class Meta:
        model = Court
        fields = ('search',)
