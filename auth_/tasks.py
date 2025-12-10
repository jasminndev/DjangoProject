from celery import shared_task
from django.conf.global_settings import EMAIL_HOST_USER
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


@shared_task
def send_code_email(user_email: dict, code):
    subject = 'Email Verification'
    from_email = EMAIL_HOST_USER
    to_email = [user_email.get('email')]
    print('Sending email to {}'.format(to_email))

    context = {
        'code': code,
        'verify_url': f"https://localhost:8000/verify/{code}"
    }
    print(context)
    html_content = render_to_string('verification_email.html', context=context)
    text_content = f"Your verification code is {code}"

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
