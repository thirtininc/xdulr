from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from practitioners.models import EmailLog, TelnyxLog

class Command(BaseCommand):
    help = 'Deletes email and Telnyx logs older than 60 days.'

    def handle(self, *args, **options):
        """
        The main logic of the management command.
        """
        # Calculate the cutoff date, which is 60 days before the current time
        cutoff_date = timezone.now() - timedelta(days=60)
        self.stdout.write(f"Pruning logs older than {cutoff_date.strftime('%Y-%m-%d')}...")

        # Find all EmailLog objects created before the cutoff date
        email_logs_to_delete = EmailLog.objects.filter(received_at__lt=cutoff_date)
        email_count = email_logs_to_delete.count()
        
        if email_count > 0:
            # Delete the old logs in a single database operation
            email_logs_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {email_count} old email logs.'))
        else:
            self.stdout.write('No old email logs to delete.')

        # Find all TelnyxLog objects created before the cutoff date
        telnyx_logs_to_delete = TelnyxLog.objects.filter(received_at__lt=cutoff_date)
        telnyx_count = telnyx_logs_to_delete.count()

        if telnyx_count > 0:
            # Delete the old logs
            telnyx_logs_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {telnyx_count} old Telnyx logs.'))
        else:
            self.stdout.write('No old Telnyx logs to delete.')

        self.stdout.write(self.style.SUCCESS('Log pruning complete.'))
