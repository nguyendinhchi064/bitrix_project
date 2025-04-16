from django.db import models
from django.utils.timezone import now

class BitrixToken(models.Model):
    domain = models.CharField(max_length=255, unique=True)
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    expires_in = models.BigIntegerField()
    expires_at = models.DateTimeField()
    client_id = models.CharField(max_length=255, blank=True, null=True)
    client_secret = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Token for {self.domain}"

    def is_expired(self):
        return now() >= self.expires_at

    class Meta:
        verbose_name = "Bitrix24 Token"
        verbose_name_plural = "Bitrix24 Tokens" #This name will appear in admin

