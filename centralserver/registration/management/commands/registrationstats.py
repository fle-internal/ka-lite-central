"""
Display stats about registrations and usage of the Central Server directly
in the terminal.
"""

from django.core.management.base import BaseCommand
from django.db.models import Sum, Avg

from kalite.main.models import AttemptLog, ExerciseLog
from ...models import RegistrationProfile
from securesync.engine.models import SyncSession
from securesync.devices.models import Device
from kalite.topic_tools.content_models import get_content_item


class Command(BaseCommand):
    help = "Displays basic anonymized stats from registrations and usage"

    def handle(self, *args, **options):
        
        registered_users = RegistrationProfile.objects.filter(
            activation_key=RegistrationProfile.ACTIVATED
        ).count()

        print("------------------------------")
        print(" Registrations")
        print("------------------------------")
                
        print("Registered users: {}".format(registered_users))
        
        sync_sessions = SyncSession.objects.all().count()
        
        print("Sync sessions: {}".format(sync_sessions))
        
        devices = Device.objects.all().count()

        print("Devices: {}".format(devices))

        print("Syncs per device: {}".format(float(sync_sessions) / devices))
        
        print("------------------------------")
        print(" Exercises, attempts")
        print("------------------------------")

        exercise_attempts = AttemptLog.objects.all().count()
        
        exercise_complete = AttemptLog.objects.filter(complete=True).count()
        exercise_correct = AttemptLog.objects.filter(correct=True).count()

        print("Total attempts: {}".format(exercise_attempts))
        print("Completed exercises: {}".format(exercise_complete))
        print("Correct exercises: {}".format(exercise_correct))

        print("------------------------------")
        print(" Exercises, Top 10 completed")
        print("------------------------------")

        exercises = ExerciseLog.objects.filter(complete=True).values("exercise_id").annotate(
            attempts_avg=Avg("attempts_before_completion"),
            attempts=Sum("attempts_before_completion"),
        ).order_by("-attempts")[:10]

        for exercise in exercises:
            title = get_content_item(content_id=exercise["exercise_id"])
            print("{}: {} avg. attempts".format(title, exercise["attempts_avg"]))

        print("------------------------------")
        print(" Exercises, Top 10 hardest")
        print("------------------------------")

        exercises = ExerciseLog.objects.filter(complete=True).values("exercise_id").annotate(
            attempts_avg=Avg("attempts_before_completion"),
            attempts=Sum("attempts"),
        ).order_by("-attempts_avg")[:10]

        for exercise in exercises:
            title = get_content_item(content_id=exercise["exercise_id"])
            print("{}: {} attempts".format(title, exercise["attempts"]))
