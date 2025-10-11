from django.db import models


class FAQ(models.Model):
    content = models.TextField()  # Содержимое FAQ
    is_active = models.BooleanField(default=False)  # Активная версия
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания
    updated_at = models.DateTimeField(auto_now=True)  # Дата обновления

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return f"FAQ (ID: {self.id}, Active: {self.is_active})"