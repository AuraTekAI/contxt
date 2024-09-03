
from sms_app.models import SMS
from sms_app.serializers import SmsSerializer
from sms_app.utils import log_incoming_request, validate_webhook_token, get_webhook_schema
from sms_app.constants import OPERATIONAL_DESCRIPTION
from contxt.utils.constants import SMS_DIRECTION_CHOICES, SMS_STATUS_CHOICES

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger('sms_webhook')

SMS_STATUS_CHOICES_DICT = dict(SMS_STATUS_CHOICES)
SMS_DIRECTION_CHOICES_DICT = dict(SMS_DIRECTION_CHOICES)


@swagger_auto_schema(
    method='post',
    operation_description=OPERATIONAL_DESCRIPTION,
    request_body=get_webhook_schema(),
    responses={
        200: openapi.Response('Successful response', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='The email address associated with the SMS'),
                'contact': openapi.Schema(type=openapi.TYPE_STRING, description='The name of the contact associated with the SMS')
            }
        )),
        400: openapi.Response('Bad request', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Returns False in case of error'),
                'contact': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Returns False in case of error')
            }
        )),
        403: openapi.Response('Forbidden', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
            }
        )),
    }
)
@api_view(['POST'])
def textbelt_webhook(request):
    log_incoming_request(request=request, logger=logger)

    incoming_data = request.data

    if settings.TEST_MODE == False:
        token = incoming_data.get('data', None)
        if token:
            valid_token = validate_webhook_token(token)
            if not valid_token:
                logger.error("Invalid or expired token in webhook request.")
                return Response({'error': 'Invalid or expired token'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_403_FORBIDDEN)

    email = None
    contact = None
    error_occured = False
    status_code = status.HTTP_200_OK

    if incoming_data:
        try:
            outbound_sms_obj = SMS.objects.filter(text_id=incoming_data.get('textId', None), direction=SMS_DIRECTION_CHOICES_DICT['Outbound']).order_by('-created_at').first()
            if not outbound_sms_obj:
                raise ValueError(f"No outbound sms found for textid {incoming_data.get('textId', None)}")

            logger.debug(f'Outbound sms object = {outbound_sms_obj}')

            email = outbound_sms_obj.email
            contact = outbound_sms_obj.contact
            if email and contact:
                inbound_sms_obj = SMS.objects.create(
                    bot = outbound_sms_obj.bot,
                    email = email,
                    contact = contact,
                    message = incoming_data.get('text', None),
                    text_id = incoming_data.get('textId', None),
                    phone_number = incoming_data.get('fromNumber', None),
                    direction = SMS_DIRECTION_CHOICES_DICT['Inbound'],
                    status = SMS_STATUS_CHOICES_DICT['Delivered']
                )
                logger.debug(f"SMS inbound object created. Data = {inbound_sms_obj}")

        except Exception as e:
            error_occured = True
            logger.error(f"Error occured while getting or updating sms from database with text_id {incoming_data.get('text_id')}. Complete Error information = {e}")

    if error_occured:
        status_code = status.HTTP_400_BAD_REQUEST

    return Response({'email' : email.message_id if email else False, 'contact' : contact.contact_name if contact else False},status=status_code)


@swagger_auto_schema(
    method='get',
    operation_description="Checks if the API is working.",
    responses={
        200: openapi.Response('Successful response', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, description='Status message')
            }
        ))
    }
)
@api_view(['GET'])
def sms_api_test(request):
    return Response({'message' : "API is working."})
