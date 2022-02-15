from django.core.management.base import BaseCommand, CommandError
from crunch.django.app.models import Dataset

class Command(BaseCommand):
    help = 'Lists the files in storage associated with a dataset.'

    def add_arguments(self, parser):
        parser.add_argument('project', type=str)
        parser.add_argument('dataset', type=str)

    def handle(self, *args, **options):
        dataset = Dataset.objects.get(slug=options['dataset'], project__slug=options['project'])
        print(dataset)
        print(list(dataset.files()))
        