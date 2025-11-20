import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.locations.models import City, Country
from apps.locations.serializers import (
    CityCreateSerializer,
    CountryCreateSerializer,
)


class Command(BaseCommand):
    """Load countries and cities from JSON file."""

    help = 'Load locations from JSON file'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--file',
            type=str,
            default='data/locations.json',
            help='Path to JSON file with locations data',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before loading',
        )

    def handle(self, *args, **options):
        """Main command logic."""
        file_path = options['file']

        if options['clear']:
            self.clear_data()
            return

        if not os.path.exists(file_path):
            raise CommandError(f'File "{file_path}" does not exist.')

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            self.load_data(data)

        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON format: {e}') from e
        except Exception as e:
            raise CommandError(f'Error loading data: {e}') from e

        self.stdout.write(
            self.style.SUCCESS('Successfully loaded locations from JSON')
        )

    def clear_data(self):
        """Clear existing location data."""
        self.stdout.write('Clearing existing data...')
        City.objects.all().delete()
        Country.objects.all().delete()
        self.stdout.write(self.style.WARNING('Existing data cleared'))

    @transaction.atomic
    def load_data(self, data):
        """Load countries and cities from JSON data."""
        countries_created = 0
        for country_data in data.get('countries', []):
            serializer = CountryCreateSerializer(data=country_data)
            if serializer.is_valid():
                country, created = Country.objects.get_or_create(
                    name=serializer.validated_data['name']
                )
                if created:
                    countries_created += 1
                    self.stdout.write(
                        f'Created country: {country.name}',
                        style_func=self.style.SUCCESS,
                    )
                else:
                    self.stdout.write(
                        f'Country exists: {country.name}',
                        style_func=self.style.NOTICE,
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Country not created: {country_data} — '
                        f'{serializer.errors}'
                    )
                )

        self.stdout.write(f'Countries processed: {countries_created} created')

        cities_created = 0
        cities_skipped = 0

        for city_data in data.get('cities', []):
            serializer = CityCreateSerializer(data=city_data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                city, created = City.objects.get_or_create(
                    name=validated_data['name'],
                    country=validated_data['country'],
                )
                if created:
                    cities_created += 1
                    self.stdout.write(
                        f'Created city: {city.name}, {city.country.name}',
                        style_func=self.style.SUCCESS,
                    )
                else:
                    self.stdout.write(
                        f'City exists: {city.name}, {city.country.name}',
                        style_func=self.style.NOTICE,
                    )
            else:
                cities_skipped += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'City not created: {city_data} — {serializer.errors}'
                    )
                )

        self.stdout.write(
            f'Cities processed: {cities_created} created, '
            f'{cities_skipped} skipped'
        )
