"""
"""
import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from centralserver.central.models import ExportJob
from django.utils import timezone


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs pending and non-started export jobs."

    option_list = BaseCommand.option_list + (
        make_option('-d', '--dry-run',
            action='store_true',
            dest='dryrun',
            help='do not store whether a job was started',
        ),
        make_option('-a', '--reset-all',
            action='store_true',
            dest='resetall',
            help='Resets all jobs (reruns everything!)',
        ),
    )

    def handle(self, *args, **options):
        logger.info("Processing pending, non-started export jobs at {}".format(timezone.now()))
        
        # This maintains state when using --dry-run
        last_id = 0
        
        if options['resetall']:
            ExportJob.objects.all().update(started=None, completed=None)
        
        while True:
            next_job = ExportJob.objects.filter(
                completed=None,
                started=None,
                id__gt=last_id,
            ).order_by('id')
    
            if next_job.count() == 0:
                logger.info("No more jobs in queue")
                break

            job = next_job[0]
            last_id = job.id
            logger.info("Processing Job ID {}".format(job.id))

            if not options.get('dryrun', False):
                job.started = timezone.now()
                job.save()
            
            job.run()
            
            if not options.get('dryrun', False):
                job.completed = timezone.now()
                job.save()
