"""
A command that mass-mails people.
"""
import socket
import time

from datetime import datetime
from optparse import make_option
from django.core import mail
from django.core.management.base import BaseCommand, CommandError


from ...models import RegistrationProfile

from django import template
from django.template.base import TemplateDoesNotExist
from django.template.context import Context
from django.contrib.auth.models import User
from postmark.backends import PostmarkMailUnprocessableEntityException


class Command(BaseCommand):
    help = """
    Send an email to registered users.
    """

    args = "<template_name>"

    option_list = BaseCommand.option_list + (
        make_option('-y', '--yes',
            action='store_true',
            dest='confirm',
            help='Sends emails, otherwise just prints a test email and a count.',
        ),
        make_option('-l', '--last-login-lte',
            action='store',
            dest='last_login_lte',
            default=None,
            help='Upper bound on last_login date "smaller than or equal to" (midnight, so includes that date)',
        ),
        make_option('-t', '--test-email',
            action='store',
            dest='test_email',
            default=None,
            help='Send one email here and exit',
        ),
        make_option('-s', '--skip',
            action='store',
            dest='skip_log',
            default=None,
            help='A file full of emails to skip',
        ),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Need to supply a template name")
        
        template_name = args[0]
        max_date = options.get("last_login_lte", None)
        test_email = options.get("test_email", None)
        confirm = options.get("confirm", False)
        skip_log = options.get("skip_log", None)
        
        assert test_email or confirm
        
        if skip_log:
            skip_log = open(skip_log, "r").read().strip().split("\n")
            print("Skipping {} emails".format(len(skip_log)))
        else:
            skip_log = []

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
            activation_key=RegistrationProfile.ACTIVATED,
            unsubscribe_decomissioning_emails=False,
        ).exclude(
            user__email=None
        ).order_by(
            "-id"
        ).select_related("user")
        
        if max_date:
            registrations = registrations.exclude(
                user__last_login__gte=max_date
            ) 

        emails = set([reg.user.email for reg in registrations])
        
        print(
            "Number of emails to send: {}".format(len(emails))
        )

        connection = mail.get_connection()
        
        connection.open()

        for email in emails:
            user = User.objects.filter(email__iexact=email)[0]
            receiver_list = [
                email if not test_email else test_email
            ]
            if receiver_list[0] in skip_log:
                print("Skipping {}".format(receiver_list[0]))
                continue

            context = Context({
                'name': user.get_full_name(),
                'email': email
            })
            body = t_body.render(context)
            subject = t_subject.render(context)
            email1 = mail.EmailMessage(
                subject.strip(),
                body,
                'kalite@learningequality.org',
                receiver_list,
                connection=connection,
            )
            
            for __ in range(5):
                try:
                    email1.send(fail_silently=False)
                    email_log.write("{}\n".format(email))
                    break
                except socket.timeout:
                    print("Timed out sending to {}, sleeping 1 second".format(email))
                    time.sleep(1)
                    continue
                except PostmarkMailUnprocessableEntityException:
                    RegistrationProfile.objects.filter(
                        user__email__iexact=email
                    ).update(
                        unsubscribe_decomissioning_emails=True
                    )
                    print("Email previously unsubscribed/bounced: {}".format(email))
                    break
                except:
                    print("Failed sending to: {}".format(receiver_list[0]))
                    raise
                
            if test_email:
                print("Exiting test, check that {} received an email".format(test_email))
                break
