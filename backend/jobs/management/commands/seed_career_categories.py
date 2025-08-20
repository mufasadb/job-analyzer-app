"""
Management command to seed initial career categories for the insights system.
These categories help organize user insights by career path type.
"""

from django.core.management.base import BaseCommand
from jobs.models import CareerCategory


class Command(BaseCommand):
    help = 'Seed initial career categories for insights matching'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing career categories...')
            CareerCategory.objects.all().delete()

        categories_data = [
            {
                'name': 'CTO (Chief Technology Officer)',
                'keywords': [
                    'cto', 'chief technology officer', 'head of technology',
                    'technology director', 'vp engineering', 'vp technology',
                    'chief technical officer', 'technology lead'
                ],
                'description': 'Senior technical leadership roles focusing on technology strategy, architecture, and team leadership.'
            },
            {
                'name': 'Head of IT / IT Director',
                'keywords': [
                    'head of it', 'it director', 'it manager', 'infrastructure director',
                    'systems director', 'technology operations director', 'it leadership',
                    'director of information technology'
                ],
                'description': 'Leadership roles managing IT infrastructure, operations, and technology systems.'
            },
            {
                'name': 'Engineering Management',
                'keywords': [
                    'engineering manager', 'senior engineering manager',
                    'director of engineering', 'vp engineering', 'engineering lead',
                    'technical manager', 'development manager'
                ],
                'description': 'Management roles leading engineering teams and software development organizations.'
            },
            {
                'name': 'Product Management',
                'keywords': [
                    'product manager', 'senior product manager', 'principal product manager',
                    'director of product', 'vp product', 'head of product',
                    'product lead', 'product owner'
                ],
                'description': 'Product strategy and management roles focusing on product development and market fit.'
            },
            {
                'name': 'Project Management / Program Management',
                'keywords': [
                    'project manager', 'program manager', 'senior project manager',
                    'project lead', 'program lead', 'delivery manager',
                    'scrum master', 'agile coach'
                ],
                'description': 'Roles focused on project delivery, program coordination, and process management.'
            },
            {
                'name': 'Technical Leadership / Architect',
                'keywords': [
                    'technical lead', 'lead developer', 'senior developer',
                    'principal engineer', 'staff engineer', 'architect',
                    'solution architect', 'technical architect', 'lead engineer'
                ],
                'description': 'Senior individual contributor roles with technical leadership responsibilities.'
            },
            {
                'name': 'Consultant / Advisory',
                'keywords': [
                    'consultant', 'senior consultant', 'principal consultant',
                    'advisor', 'technical advisor', 'freelancer',
                    'independent contractor', 'strategic advisor'
                ],
                'description': 'Consulting and advisory roles providing expertise to organizations.'
            },
            {
                'name': 'Startup / Founder',
                'keywords': [
                    'founder', 'co-founder', 'ceo', 'startup',
                    'entrepreneur', 'technical founder', 'founding engineer'
                ],
                'description': 'Entrepreneurial roles in startups and founding new ventures.'
            },
            {
                'name': 'Data & Analytics Leadership',
                'keywords': [
                    'head of data', 'data director', 'chief data officer',
                    'analytics director', 'data science manager',
                    'business intelligence director'
                ],
                'description': 'Leadership roles in data strategy, analytics, and business intelligence.'
            },
            {
                'name': 'DevOps / Infrastructure Leadership',
                'keywords': [
                    'devops manager', 'infrastructure manager', 'platform manager',
                    'sre manager', 'cloud architect', 'devops lead',
                    'infrastructure director', 'platform engineering manager'
                ],
                'description': 'Leadership roles in DevOps, infrastructure, and platform engineering.'
            }
        ]

        created_count = 0
        updated_count = 0

        for category_data in categories_data:
            category, created = CareerCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'keywords': category_data['keywords'],
                    'description': category_data['description'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                # Update existing category with new data
                category.keywords = category_data['keywords']
                category.description = category_data['description']
                category.is_active = True
                category.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated category: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {created_count + updated_count} career categories '
                f'({created_count} created, {updated_count} updated)'
            )
        )