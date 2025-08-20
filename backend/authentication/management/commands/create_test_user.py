from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create a test user for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete and recreate the test user if it exists',
        )

    def handle(self, *args, **options):
        username = 'testuser'
        email = 'test@example.com'
        password = 'testpass123'
        
        if User.objects.filter(username=username).exists():
            if options['reset']:
                User.objects.filter(username=username).delete()
                self.stdout.write(
                    self.style.WARNING(f'Deleted existing test user "{username}"')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Test user "{username}" already exists!\n'
                                      f'Username: {username}\n'
                                      f'Password: {password}\n'
                                      f'Email: {email}\n'
                                      f'Use --reset to recreate')
                )
                return
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Test user created successfully!\n'
                              f'Username: {username}\n'
                              f'Password: {password}\n'
                              f'Email: {email}')
        )