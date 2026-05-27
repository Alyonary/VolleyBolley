from typing import Any, Type

from django.db.models import QuerySet
from django.db.models.base import Model


def get_model_objects(model_class: Type[Model], **kwargs: Any) -> QuerySet:
    if kwargs:
        return model_class.objects.filter(**kwargs)
    return model_class.objects.all()
