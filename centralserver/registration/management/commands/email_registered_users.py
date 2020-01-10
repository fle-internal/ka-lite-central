"""
A command that mass-mails people.
"""
from datetime import datetime
from optparse import make_option
from django.core import mail
from django.core.management.base import BaseCommand, CommandError

from django.db.models import Count, Max, Min

from ...models import RegistrationProfile

from centralserver.central.models import Organization
from django import template
from django.template.base import TemplateDoesNotExist
from django.template.context import Context


class Command(BaseCommand):
    help = """
    Send an email to registered users.
    """

    args = "<template_name>"

    option_list = BaseCommand.option_list + (
        make_option('-y', '--yes',
            action='store',
            dest='store_true',
            help='Sends emails, otherwise just prints a test email and a count.',
        ),
        make_option('-l', '--last-login-gte',
            action='store',
            dest='last_login_gte',
            default=None,
            help='Lower bound on last_login date "greater than or equal to" (midnight, so includes that date)',
        ),
        make_option('-t', '--test-email',
            action='store',
            dest='test_email',
            default=None,
            help='Send one email here and exit',
        ),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Need to supply a template name")
        
        template_name = args[0]
        min_date = options.get("min_date", None)
        test_email = options.get("test_email", None)
        
        email_log = open(
            "email_log_{}_{}.log".format(template_name, datetime.now().strftime("%Y%m%d_%H%M%s")),
            "w"
        )
        
        try:
            t_body = template.loader.get_template("registration/emails/{}.txt".format(template_name))
            t_subject = template.loader.get_template("registration/emails/{}_subject".format(template_name))
        except TemplateDoesNotExist:
            raise CommandError("Use the file name of something in registration/emails/")
        
        registrations = RegistrationProfile.objects.filter(
            activation_key=RegistrationProfile.ACTIVATED
        ).exclude(
            user__email=None
        ).order_by(
            "-id"
        )
        
        if min_date:
            registrations = registrations.exclude(
                user__last_login__gte=min_date
            ) 

        print(
            "Number of emails to send: {}".format(registrations.count())
        )


        connection = mail.get_connection()
        
        connection.open()

        for reg in registrations:
            receiver_list = [
                reg.user.email if not test_email else test_email
            ]
            context = Context({
                'name': reg.user.get_full_name(),
                'email': reg.user.email
            })
            body = t_body.render(context)
            subject = t_subject.render(context)
            email1 = mail.EmailMessage(
                subject,
                body,
                'info@learningequality.org',
                receiver_list,
                connection=connection,
            )
            try:
                email1.send(fail_silently=False)
                email_log.write("{}\n".format(reg.user.email))
            except:
                print("Failed sending to: {}".format(receiver_list[0]))
                raise
                
            if test_email:
                print("Exiting test, check that {} received an email".format(test_email))
                break