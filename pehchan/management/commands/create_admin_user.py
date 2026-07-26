import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create or update admin superuser for Pehchan'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default=os.environ.get('ADMIN_USERNAME', 'admin'),
            help='Admin username (default: admin or ADMIN_USERNAME env var)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default=os.environ.get('ADMIN_EMAIL', 'admin@pehchanyui.in'),
            help='Admin email (default: admin@pehchanyui.in or ADMIN_EMAIL env var)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default=os.environ.get('ADMIN_PASSWORD', 'admin'),
            help='Admin password (default: admin or ADMIN_PASSWORD env var)'
        )

    def handle(self, *args, **options):
        username = options['username'] or 'admin'
        email = options['email'] or 'admin@pehchanyui.in'
        password = options['password'] or 'admin'

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Pehchan Admin User Setup'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # Security warning for production
        if password == 'admin' and os.environ.get('DEBUG', 'False') == 'False':
            self.stdout.write(self.style.WARNING(
                'WARNING: Using default admin password in production!'
            ))
            self.stdout.write(self.style.WARNING(
                'Please set ADMIN_PASSWORD environment variable to a secure password.'
            ))

        # Check if user exists
        if User.objects.filter(username=username).exists():
            # User exists - update password
            user = User.objects.get(username=username)
            user.set_password(password)
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f'[*] Updated existing superuser "{username}"'
            ))
            self.stdout.write(self.style.SUCCESS(f'  Email: {email}'))
            self.stdout.write(self.style.SUCCESS(f'  Login at: /admin/'))
        else:
            # Create new superuser
            try:
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                self.stdout.write(self.style.SUCCESS(
                    f'[*] Created new superuser "{username}"'
                ))
                self.stdout.write(self.style.SUCCESS(f'  Email: {email}'))
                self.stdout.write(self.style.SUCCESS(f'  Login at: /admin/'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'[ERROR] Failed to create superuser: {e}'
                ))
                return

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('[*] Admin setup completed successfully!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
