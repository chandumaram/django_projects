from django.http import HttpResponse
from django.shortcuts import render
from .tasks import test_func
from send_mail_app.tasks import send_mail_func
from django_celery_beat.models import PeriodicTask, CrontabSchedule

# Create your views here.
def test(request):
    test_func.delay()
    return HttpResponse("Done")

def send_mail_to_all(request):
    send_mail_func.delay()
    return HttpResponse("Sent")

def schedule_mail(request):
    schedule, created = CrontabSchedule.objects.get_or_create(hour=16, minute=10)
    task = PeriodicTask.objects.create(crontab=schedule, name="schedule_mail_task_1")
    return HttpResponse("Mail Sent")