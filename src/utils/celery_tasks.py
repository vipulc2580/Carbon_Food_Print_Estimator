from celery import Celery
from .mail_service import mail,create_email_message
from typing import List 
from asgiref.sync import async_to_sync

celery_app=Celery()

celery_app.config_from_object('src.constants.config')

# celery task are not going to asynchronous
@celery_app.task()
def send_email(
    recipients:List[str],
    subject:str,
    body:str 
    ):
    message=create_email_message(
            recipients=recipients,
            subject=subject,
            body=body
        )
    # here mail.send_message is a co-routine async function
    # we convert async to sync 
    async_to_sync(mail.send_message)(message)