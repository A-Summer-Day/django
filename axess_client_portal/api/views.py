from smtplib import SMTPException
from django.shortcuts import render
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMultiAlternatives
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey
import json, uuid

# Create your views here.

def dashboard(request):
    data = {
        'name': 'Dashboard',
        'location': 'Finland',
        'is_active': True,
        'count': 28
    }
    return JsonResponse(data)


def file_submission(request):
    data = {
        'name': 'File Submission',
        'location': 'Finland',
        'is_active': True,
        'count': 28
    }
    return JsonResponse(data)


def document_upload(request):
    data = {
        'name': 'Document Upload',
        'location': 'Finland',
        'is_active': True,
        'count': 28
    }
    return JsonResponse(data)


@csrf_exempt
@api_view(['POST'])
# @permission_classes([IsAuthenticated])
@permission_classes([HasAPIKey])
def referral(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        firm_code =  data.get('firm_code', '')
        if(firm_code):
            referral_type = data.get('referral_type', '')
            name = data.get('name', '')
            email = data.get('email', '')
            phone = data.get('phone', '')
            file_type = data.get('file_type', '')
            street_address_1 = data.get('street_address_1', '')
            street_address_2 = data.get('street_address_2', '')
            city = data.get('city', '')
            province = data.get('province', '')
            postal_code = data.get('postal_code', '')
            
            to_email = ['sle@axesslaw.com', 'jon@sidepart.com', 'jcastellano@axesslaw.com']
            submission_id = str(uuid.uuid4())

            context = {
                'referral_type': referral_type,
                'name': name,
                'email': email,
                'phone': phone,
                'file_type': file_type,
                'submission_id' : submission_id,
                'street_address_1': street_address_1,
                'street_address_2': street_address_2,
                'city': city,
                'province': province,
                'postal_code': postal_code,
                'firm_code': firm_code
            }

            html_body = render_to_string('api/email_templates/referral.html', context) 

            message =  EmailMultiAlternatives(
                subject = 'Client Portal API Referral',
                body = "Email testing",
                from_email ='autoemail@axesslaw.com',
                to = to_email
            )

            message.attach_alternative(html_body, "text/html")
            try:
                message.send(fail_silently=False)

                response = {
                    'success': True,
                    'request_type': 'POST',
                    'submission_id': submission_id
                }
            except SMTPException as e:
                response = {
                'success': False,
                'request_type': 'POST',
                'message': 'Unable to send email. Please try again later.'
            }
        else:
            response = {
                'success': False,
                'request_type': 'POST',
                'message': 'Request is missing firm_code'
            }

        return JsonResponse(response)
    else:
        response = {
            'success': False,
            'request_type': 'GET',
            'message': 'Only POST method is allowed.'
        }

        return JsonResponse(response)


