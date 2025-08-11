from cryptography.fernet import Fernet
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

from apps.notifications.models import Device


class Command(BaseCommand):
    help = 'Rotate encryption keys and re-encrypt all FCM tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--new-key',
            help='New encryption key (base64). If not provided, a new one '
                 'will be generated.'
        )

    def handle(self, *args, **options):
        """
        Rotate encryption keys for FCM tokens.
        If a new key is provided, it will be used; otherwise, a new key will
        be generated. The old key will be added to the list of old keys.
        """
        new_key = options.get('new-key')
        if not new_key:
            new_key = Fernet.generate_key()
            self.stdout.write(
                self.style.SUCCESS(f"Generated new encryption key: "
                                  f"{new_key.decode()}")
            )
        else:
            new_key = new_key.encode() if isinstance(
                new_key, str
            ) else new_key
        try:
            Fernet(new_key)
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Invalid encryption key: {str(e)}")
            )
            return

        old_key = settings.ENCRYPTION_KEY
        old_key_str = old_key.decode() if isinstance(
            old_key, bytes
        ) else old_key

        old_fernet = Fernet(old_key)
        new_fernet = Fernet(new_key)
        self.stdout.write(
            self.style.NOTICE("Starting key rotation process...")
        )

        success_count, error_count = self.replace_tokens_in_db(
            old_fernet, new_fernet
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Re-encryption complete: {success_count} successful, "
                f"{error_count} failed"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "\nIMPORTANT: Update your environment variables:"
            )
        )
        self.stdout.write(f"ENCRYPTION_KEY={new_key.decode()}\n")        
        self.stdout.write(f"OLD_ENCRYPTION_KEYS={old_key_str}")

        self.stdout.write(
            self.style.WARNING(
                "\nMake sure to update your environment variables and restart"
                " your application to apply the new encryption key."
            )
        )

    def replace_tokens_in_db(self, old_fernet, new_fernet):
        """Replaces tokens in the db using the old and new Fernet keys."""
        devices = Device.objects.all()
        count = devices.count()
        self.stdout.write(
            self.style.NOTICE(f"Found {count} devices to re-encrypt")
        )
        success_count = 0
        error_count = 0
        token_field_name = Device._meta.get_field('token').column
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT id, {token_field_name} FROM {Device._meta.db_table}"
            )
            rows = cursor.fetchall()

            for row in rows:
                device_id, encrypted_token = row

                try:
                    try:
                        decrypted_token = old_fernet.decrypt(
                            encrypted_token.encode('utf-8')
                        ).decode('utf-8')
                    except Exception as e:
                        self.stderr.write(
                            self.style.ERROR(
                                f"Could not decrypt token for device "
                                f"{device_id}: {str(e)}"
                            )
                        )
                        error_count += 1
                        continue
                    newly_encrypted_token = new_fernet.encrypt(
                        decrypted_token.encode('utf-8')
                    ).decode('utf-8')
                    cursor.execute(
                        f"UPDATE {Device._meta.db_table} SET "
                        f"{token_field_name} = %s WHERE id = %s",
                        [newly_encrypted_token, device_id]
                    )

                    success_count += 1
                    if success_count % 100 == 0:
                        self.stdout.write(
                            f"Re-encrypted {success_count} tokens..."
                        )

                except Exception as e:
                    self.stderr.write(
                        self.style.ERROR(
                            f"Error processing device {device_id}: {str(e)}"
                        )
                    )
                    error_count += 1
        return success_count, error_count