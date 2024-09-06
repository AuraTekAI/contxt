
from sms_app.models import SMS
from sms_app.utils import log_incoming_request, validate_webhook_token, get_webhook_schema
from sms_app.constants import OPERATIONAL_DESCRIPTION
from contxt.utils.constants import SMS_DIRECTION_CHOICES, SMS_STATUS_CHOICES, CURRENT_TASKS_RUN_BY_BOTS

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging


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
    # Get the command name from the currently running bot tasks
    command_name = CURRENT_TASKS_RUN_BY_BOTS['receive_sms']

    # Extract incoming data from the request
    incoming_data = request.data

    # Initialize variables to hold email, contact, error state, and response status code
    email = None
    contact = None
    error_occured = False
    status_code = status.HTTP_200_OK

    # Check if there is any incoming data
    if incoming_data:
        try:
            # Try to find the outbound SMS object using the text ID from incoming data
            outbound_sms_obj = SMS.objects.filter(
                text_id=incoming_data.get('textId', None),
                direction=SMS_DIRECTION_CHOICES_DICT['Outbound']
            ).order_by('-created_at').first()

            # If no outbound SMS object is found, log the error and raise a ValueError
            if not outbound_sms_obj:
                logger = logging.getLogger('sms_webhook')
                logger.error(f"No outbound SMS found for text_id = {incoming_data.get('textId', None)}")
                raise ValueError(f"No outbound SMS found for textid {incoming_data.get('textId', None)}")

            # Set up the logger depending on whether the SMS is associated with a bot
            if outbound_sms_obj.bot:
                logger = logging.getLogger(f'bot_{outbound_sms_obj.bot.id}_{command_name}')
            else:
                logger = logging.getLogger('sms_webhook')

            # Log the incoming request for debugging or audit purposes
            log_incoming_request(request=request, logger=logger)

            # If not in test mode, validate the webhook token
            if settings.TEST_MODE == False:
                token = incoming_data.get('data', None)
                if token:
                    valid_token = validate_webhook_token(token)
                    # If the token is invalid or expired, log an error and return a 403 response
                    if not valid_token:
                        logger.error(f"Invalid or expired token in webhook request. Incoming data was = {incoming_data}")
                        return Response({'error': 'Invalid or expired token'}, status=status.HTTP_403_FORBIDDEN)
                else:
                    # If no token is present in the incoming data, return a 403 response
                    return Response({'error': 'Invalid or expired token'}, status=status.HTTP_403_FORBIDDEN)

            # Log the outbound SMS object for debugging purposes
            logger.debug(f'Outbound SMS object = {outbound_sms_obj}')

            # Extract the email and contact information from the outbound SMS object
            email = outbound_sms_obj.email
            contact = outbound_sms_obj.contact

            # If both email and contact are present, create a new inbound SMS object
            if email and contact:
                inbound_sms_obj = SMS.objects.create(
                    bot=outbound_sms_obj.bot,
                    email=email,
                    contact=contact,
                    message=incoming_data.get('text', None),
                    text_id=incoming_data.get('textId', None),
                    phone_number=incoming_data.get('fromNumber', None),
                    direction=SMS_DIRECTION_CHOICES_DICT['Inbound'],
                    status=SMS_STATUS_CHOICES_DICT['Delivered']
                )
                # Log the creation of the new inbound SMS object
                logger.debug(f"SMS inbound object created. Data = {inbound_sms_obj}")

        except Exception as e:
            # If any exception occurs, set error_occured to True and log the error
            error_occured = True
            logger.error(f"Error occurred while getting or updating SMS from database with text_id {incoming_data.get('textId')}. Complete Error information = {e}")

    # If an error occurred, set the response status code to 400
    if error_occured:
        status_code = status.HTTP_400_BAD_REQUEST

    # Return a response containing the email message ID and contact name, if available
    return Response({'email': email.message_id if email else False, 'contact': contact.contact_name if contact else False}, status=status_code)



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
