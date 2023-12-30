import requests, logging
from requests.api import get
from simple_salesforce.api import Salesforce
from users.decorators import admin_required
from django.shortcuts import render, redirect
from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.views import View
from django.contrib import messages, auth 
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.loader import render_to_string
from django_filters import FilterSet
from simple_salesforce import Salesforce, format_soql
from modules import salesforce
from users.models import User
from dotenv import load_dotenv
from os import getenv
from .forms import UploadFileForm

load_dotenv()

logger = logging.getLogger('watchtower')



# Create your views here.

@login_required(redirect_field_name=None)
def dashboard(request):
    recent_transactions = salesforce.get_recent_transactions(request, 1)
    if(recent_transactions['has_result']):
        most_recent_transaction_details = salesforce.get_transaction_details(request, recent_transactions['transactions'][0]['Opportunity']['Id'])
        if(most_recent_transaction_details['has_result']):
            transaction_info = salesforce.get_transaction_data(most_recent_transaction_details['transaction']['Opportunity']['RecordTypeId'])
            total_transactions = salesforce.get_all_transactions(request)
            transactions = recent_transactions['transactions']
            for transaction in transactions:
                tdata = salesforce.get_transaction_data(transaction['Opportunity']['RecordTypeId'])
                transaction['portal_transaction_type'] = tdata['label']
        
            context = {
                'transactions': transactions,
                'total_transactions': total_transactions['total'],
                'total_open_transactions': total_transactions['total_open'],
                'total_completed_transactions': total_transactions['total_completed'],
                'transactions_with_tasks_outstanding': recent_transactions['transactions_with_tasks_outstanding'],
                'most_recent_transaction': most_recent_transaction_details['transaction'],
                'most_recent_transaction_portal_type': most_recent_transaction_details['portal_transaction_type'],
                'number_of_completed_tasks': most_recent_transaction_details['number_of_completed_tasks'],
                'number_of_open_tasks': most_recent_transaction_details['number_of_open_tasks'],
                'completed_tasks': most_recent_transaction_details['completed_tasks'],
                'open_tasks': most_recent_transaction_details['open_tasks'],
                'milestones': transaction_info['milestones'] if transaction_info else [],
                'current_milestone_index': (transaction_info['milestones'].index(most_recent_transaction_details['transaction']['Opportunity']['Milestone__c'])) + 1 if transaction_info and most_recent_transaction_details['transaction']['Opportunity']['Milestone__c'] else 1
            }

        else:
            context = {
                'no_recent_transactions': True,
                'error': "You don't have any recent transactions to view.",
                'transactions_with_tasks_outstanding': 0
            }
    else:
        print('No result found')
        context = {
            'no_recent_transactions': True,
            'error': "You don't have any recent transactions to view.",
            'transactions_with_tasks_outstanding': 0
        }

    return render(request, 'client_portal/index.html', context)


@login_required(redirect_field_name=None)
def transactions(request, page_number=1):
    page_size = 5
    
    all_transactions = salesforce.get_all_transactions(request)

    current_page = request.GET.get('page')
    if(current_page):
        page_number = current_page
    
    if(all_transactions['has_result']):
        total_transactions = all_transactions['total']
        total_open_transactions = all_transactions['total_open']
        total_completed_transactions = all_transactions['total_completed']
        transactions = all_transactions['transactions']
        brokers = all_transactions['brokers']
        for transaction in transactions:
            tdata = salesforce.get_transaction_data(transaction['Opportunity']['RecordTypeId'])
            transaction['portal_transaction_type'] = tdata.get('label')
            
        all_transactions = tuple(transactions)

        paginator = Paginator(all_transactions, page_size)
        
        try: 
            transactions = paginator.page(page_number)
        except PageNotAnInteger:
            transactions = paginator.page(1)
        except EmptyPage:
            transactions = paginator.page(paginator.num_pages)    

        context = {
            'transactions': transactions,
            'total_transactions': total_transactions,
            'total_open_transactions': total_open_transactions,
            'total_completed_transactions': total_completed_transactions,
            'brokers': brokers
        }
    else:
        print('No transactions at all')
        context = {
            'error': "You don't have any transactions to view."
        }

    return render(request, 'client_portal/transactions.html', context)
    

@login_required(redirect_field_name=None)
def tasks(request, page_number=1):
    page_size = 5
    all_transactions = salesforce.get_all_transactions_with_tasks_outstanding(request)
    if(all_transactions['has_result']):
        transactions = all_transactions['transactions']
        for transaction in transactions:
            tdata = salesforce.get_transaction_data(transaction['Opportunity']['RecordTypeId'])
            transaction['portal_transaction_type'] = tdata['label']
            
        all_transactions = tuple(transactions)
        paginator = Paginator(all_transactions, page_size)
        
        try: 
            transactions = paginator.page(page_number)
        except PageNotAnInteger:
            transactions = paginator.page(1)
        except EmptyPage:
            transactions = paginator.page(paginator.num_pages)    

        context = {
            'transactions': transactions
        }
    else:
        print('No Transactions with Tasks Outstanding')
        context = {
            'error': "You don't have any Transactions with Tasks Outstanding."
        }

    return render(request, 'client_portal/tasks.html', context)


@login_required(redirect_field_name=None)
def transaction_details(request, transaction_id):
    if(transaction_id.startswith('006') and len(transaction_id) == 18):
        get_transaction_details = salesforce.get_transaction_details(request, transaction_id)
        form = UploadFileForm()
        if(get_transaction_details['has_result']):
            sf_transaction_type = get_transaction_details['transaction']['Opportunity']['Lead_Transaction_Type__c']
            transaction_info = salesforce.get_transaction_data(get_transaction_details['transaction']['Opportunity']['RecordTypeId'])
            clerk_info = salesforce.get_clerk_data(get_transaction_details['transaction']['Opportunity']['Clerk_Assigned_Email_Address__c'])
            bdm_info = salesforce.get_bdm_data(get_transaction_details['transaction']['Opportunity']['BDM__c'])
            context = {
                'transaction_id': transaction_id,
                'transaction': get_transaction_details['transaction'],
                'tasks': get_transaction_details['tasks'],
                'number_of_completed_tasks': get_transaction_details['number_of_completed_tasks'],
                'number_of_open_tasks': get_transaction_details['number_of_open_tasks'],
                'completed_tasks': get_transaction_details['completed_tasks'],
                'open_tasks': get_transaction_details['open_tasks'],
                'form': form,
                'portal_transaction_type': get_transaction_details['portal_transaction_type'],
                'clerk_phone_number': clerk_info['phone'] if clerk_info else '',
                'bdm_email': bdm_info['email'] if bdm_info else '',
                'milestones': transaction_info['milestones'] if transaction_info else [],
                'current_milestone_index': (transaction_info['milestones'].index(get_transaction_details['transaction']['Opportunity']['Milestone__c'])) + 1 if transaction_info and get_transaction_details['transaction']['Opportunity']['Milestone__c'] else 1,
                'primary_contact': get_transaction_details['primary_contact']
            }
        else:
            print('No result found')
            context = {
                'transaction_id': transaction_id,
                'error': "You don't have permissions to view this record or the record does not exist."
            }
    else:
        context = {
            'transaction_id': transaction_id,
            'error': 'Transaction Id is not correct.'
        }
    
    return render(request, 'client_portal/transaction_details.html', context)


@login_required(redirect_field_name=None)
def task_details(request, opportunity_id):
    if(opportunity_id.startswith('006') and len(opportunity_id) == 18):
        get_task_details = salesforce.get_task_details(request, opportunity_id)
        if(get_task_details['has_result']):
            context = {
                'opportunity_id': opportunity_id,
                'tasks': get_task_details['tasks'],
                'transaction': get_task_details['transaction'],
            }
        else:
            print('No result found')
            context = {
                'opportunity_id': opportunity_id,
                'error': "You don't have permissions to view this record or the record does not exist."
            }
    else:
        context = {
            'opportunity_id': opportunity_id,
            'error': 'Opportunity Id is not correct.'
        }
    
    return render(request, 'client_portal/task_details.html', context)


@login_required(redirect_field_name=None)
def send_email(request):
    contact_id = request.POST['contact_id']
    comment = request.POST['comment']
    from_email = request.POST['email']
    to_email = [request.POST['bdm_email']]
    print('To emails:', to_email)
    user_message = comment
    #to_email = ['sle@axesslaw.com', 'jon@sidepart.com']

    #print('To emails:', to_email)

    context = {
        'contact_id': contact_id,
        'user_message': user_message,
        'from_email': from_email
    }

    html_body = render_to_string('client_portal/email_templates/contact_us.html', context) 

    message =  EmailMultiAlternatives(
        subject = 'Client Portal Feedbacks',
        body = "Email testing",
        from_email ='autoemail@axesslaw.com',
        to = to_email
    )

    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)

    messages.success(
        request, f'Your feedbacks have been submitted! We will get back to you asap!')

    return redirect('client_portal:dashboard')


@login_required(redirect_field_name=None)
def send_message_to_clerk(request):
    contact_id = request.POST['contact_id']
    comment = request.POST['comment']
    from_email = request.POST['email']
    transaction_id = request.POST['transaction_id']
    to_email = request.POST['clerk_email']
    user_message = comment

    #to_email = ['sle@axesslaw.com']
    to_email = [to_email]

    print('To emails: ' , to_email)
    
    context = {
        'contact_id': contact_id,
        'transaction_id': transaction_id,
        'user_message': user_message,
        'from_email': from_email
    }

    html_body = render_to_string('client_portal/email_templates/message_to_clerk.html', context)

    message =  EmailMultiAlternatives(
        subject = 'Message To Clerk From Client Portal Client',
        body = "Email testing",
        from_email ='autoemail@axesslaw.com',
        to = to_email
    )

    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)

    messages.success(
        request, f'Your message has been sent to our clerk! We will get back to you asap!')

    return redirect('client_portal:transaction-details', transaction_id = request.POST['transaction_id'])


@login_required(redirect_field_name=None)
def profile(request):
    context = {
        
    }

    return render(request, 'client_portal/profile.html', context)
    

@login_required(redirect_field_name=None)
def document_upload(request):
    form = UploadFileForm()
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)  # Do not forget to add: request.FILES
        if form.is_valid():
            print(request.FILES)
            print(request.FILES['file'].name)
            salesforce.upload_document(request, request.FILES['file'])
            messages.success(request, f'File uploaded succesfully!')
            return redirect('client_portal:document-upload')


    return render(request, 'client_portal/document_upload.html', {
        'form': form
    })


@login_required(redirect_field_name=None)
def file(request):
    current_user = auth.get_user(request)
    if not current_user.is_superuser:
        return redirect('client_portal:dashboard')
    else:
        context = {
            
        }

        return render(request, 'client_portal/file.html', context)


@login_required(redirect_field_name=None)
def modal_document_upload(request):
    if request.method == 'POST':
        print('Length: ', len(request.FILES))
        print('transaction_id: ', request.POST['transaction_id'])
        print(request.FILES['file'].name)
        if len(request.FILES) != 0 and 'transaction_id' in request.POST:
            print(request.FILES)
            print(request.FILES['file'].name)
            files = request.FILES.getlist('file')
            for f in files:
                try:
                    salesforce.upload_document(request, f, request.POST['transaction_id'])
                except:
                    messages.error(request, f'Error uploading files! Please try again!')
                    return redirect('client_portal:transaction-details', transaction_id = request.POST['transaction_id'])

            new_task_status = 'Yes' if request.POST['task_value'] == 'No' else True
            print(request.POST['task_value'])
            print('new task status: ', new_task_status)
            update_task_status = salesforce.update_task_status(request.POST['transaction_id'], request.POST['task_api'], new_task_status)
            print('update_task_status: ' ,update_task_status)
            if(update_task_status):
                messages.success(request, f'File(s) uploaded succesfully!')
                return redirect('client_portal:transaction-details', transaction_id = request.POST['transaction_id'])
            else:
                messages.error(request, f'Error uploading files! Please try again!')
                return redirect('client_portal:transaction-details', transaction_id = request.POST['transaction_id'])
        
        return redirect('client_portal:dashboard')


    return redirect('client_portal:dashboard')


@login_required(redirect_field_name=None)
def sync(request):
    if request.method == 'POST':
        #salesforce.sync_shift_planning()
        context = {
            
        }

        messages.success(request, f'Synced succesfully!')
        return redirect('client_portal:sync')

    else:
        context = {
            
        }

        return render(request, 'client_portal/sync.html', context)
