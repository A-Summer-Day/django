from calendar import month
import requests, pytz
import logging
from client_portal.views import transactions
from simple_salesforce import Salesforce, format_soql, SalesforceLogin, SFType, SalesforceExpiredSession, SalesforceMalformedRequest
from os import getenv
from dotenv import load_dotenv
from django.contrib import auth
from io import BytesIO
import base64 
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import boto3
import awswrangler as wr
import json
import urllib.request

load_dotenv()
logger = logging.getLogger('watchtower')

transaction_json_data = open('./data/transactions.json')  
transaction_data = json.load(transaction_json_data)

clerk_json_data = open('./data/clerks.json')  
clerk_data = json.load(clerk_json_data)

bdm_json_data = open('./data/bdm.json')  
bdm_data = json.load(bdm_json_data)


def init_salesforce_session():
    username = username=getenv('SALESFORCE_USERNAME')
    password = getenv('SALESFORCE_PASSWORD')
    security_token = getenv('SALESFORCE_TOKEN')

    session_id, instance = SalesforceLogin(
        username=username,
        password=password,  
        security_token=security_token
    )

    print('Salesforce init')
    sf = Salesforce(instance=instance, session_id=session_id)
    return sf
    
    
def check_salesforce_session(salesforce_instance):
    try:
        salesforce_instance.query('')
    except SalesforceExpiredSession as expired_session_error:
        salesforce_instance = init_salesforce_session()
        print('Salesforce session expired!')
        logger.error(f'Salesforce session expired!') 
    except SalesforceMalformedRequest as malformed_request_error:
        pass
    finally:
        return salesforce_instance


sf = init_salesforce_session()


def get_transaction_details(request, transaction_id):
    check_sf = check_salesforce_session(sf)
    result = check_sf.query_all(format_soql("SELECT Opportunity.Id, Opportunity.Name, Opportunity.StageName, Opportunity.CloseDate, Opportunity.Lead_Transaction_Type__c, Opportunity.Primary_Contact_Flow__c, Opportunity.Mortgage_Agent_Contact__c, Opportunity.Real_Estate_Agent_Contact__c, Opportunity.Lawyer_on_file__c, Opportunity.Assigned_Lawyer__c, Opportunity.Assigned_Lawyer_Full_Name__c, Opportunity.Assigned_Lawyer_Email_Address__c, Opportunity.Clerk_Assigned__c, Opportunity.Clerk_Assigned_Email_Address__c, Opportunity.Clerk_Assigned_Full_Name__c, Opportunity.BDM__c, Opportunity.Client_on_File__c, Opportunity.Purchase_Price__c, Opportunity.Sale_Price__c, Opportunity.RecordTypeId, Opportunity.Milestone__c, Opportunity.Milestone_Completion__c, Opportunity.RecordType.Name, Opportunity.APS_Received__c, Opportunity.Assignment_APS_Received__c, Opportunity.Intake_Form_Received__c, Opportunity.Power_of_Attorney__c, Opportunity.Separation_Agreement__c, Opportunity.X2_Pieces_of_ID_Scanned_Attached__c, Opportunity.Void_Cheque__c, Opportunity.Status_Certificate_Received__c, Opportunity.Power_of_Attorney2__c, Opportunity.Separation_Agreement2__c, Opportunity.Property_Tax_Bill__c,  Opportunity.LastModifiedDate, IsPrimary, Email_Address__c, Contact.Full_Name__c FROM OpportunityContactRole WHERE OpportunityId = {transaction_id} AND Opportunity.StageName != 'Closed Lost'", transaction_id=transaction_id))
 
    if(len(result['records'])):
        user_contact_id = request.user.contact_id
        primary_contact = []
        for role in result['records']:
            if role['IsPrimary']:
                primary_contact = role
        transaction = result['records'][0]
        tdata = get_transaction_data(transaction['Opportunity']['RecordTypeId'])
        tasks = tdata['tasks'] if tdata else []
        get_contacts =  check_sf.query_all(format_soql("SELECT ContactId FROM OpportunityContactRole WHERE OpportunityId = {transaction_id} AND Opportunity.StageName != 'Closed Lost'", transaction_id=transaction_id))
        if(len(get_contacts['records'])):
            contact_list = [record['ContactId'] for record in get_contacts['records']]
            if(user_contact_id in contact_list):
                task_list = [{task['label']: transaction['Opportunity'][task['api']]} for task in tasks] if tasks else []
                task_list2 = [
                    {'api': task['api'], 
                    'label': task['label'],
                    'value': transaction['Opportunity'][task['api']]
                    } for task in tasks
                ] if tasks else []

                completed_tasks = [key for task in task_list for key in task if (task[key] == True or task[key] == 'Yes')] if task_list else []
                open_tasks = [task for task in task_list2 if (task['value'] == False or task['value'] == 'No')] if task_list2 else []
                number_of_completed_tasks = len(completed_tasks)
                number_of_open_tasks = len(open_tasks)

                returned_data = {
                    'transaction': transaction,
                    'tasks': tasks,
                    'has_result': True,
                    'number_of_completed_tasks': number_of_completed_tasks,
                    'number_of_open_tasks': number_of_open_tasks,
                    'open_tasks': open_tasks,
                    'completed_tasks': completed_tasks,
                    'portal_transaction_type': tdata['label'] if 'label' in tdata else 'N/A',
                    'primary_contact': primary_contact

                }
            else:
                returned_data = {
                    'has_result': False
                }   
        else:
            returned_data = {
                'has_result': False
            }    
    else:
        returned_data = {
            'has_result': False
        }    

    return returned_data


def get_recent_transactions(request, limit=5):
    check_sf = check_salesforce_session(sf)
    user_contact_id = request.user.contact_id
    limit = limit

    result = check_sf.query_all(format_soql("SELECT Opportunity.Id, Opportunity.Name, Opportunity.CloseDate, Opportunity.Lead_Transaction_Type__c, Opportunity.StageName, Opportunity.Lawyer_on_file__c, Opportunity.Assigned_Lawyer__c, Opportunity.Assigned_Lawyer_Full_Name__c, Opportunity.Assigned_Lawyer_Email_Address__c, Opportunity.Clerk_Assigned__c, Opportunity.Clerk_Assigned_Email_Address__c, Opportunity.Clerk_Assigned_Full_Name__c, Opportunity.Client_on_File__c, Opportunity.Purchase_Price__c, Opportunity.Sale_Price__c, Opportunity.RecordTypeId, Opportunity.Milestone__c, Opportunity.Milestone_Completion__c, Opportunity.RecordType.Name, Opportunity.LastModifiedDate FROM OpportunityContactRole WHERE ContactId = {contact_id} AND Opportunity.StageName != 'Closed Lost' ORDER BY Opportunity.CloseDate DESC LIMIT {limit}", contact_id=user_contact_id, limit=limit))

    if(len(result['records'])):
        transactions = result['records']
        get_transactions_with_tasks_outstanding =  check_sf.query_all(format_soql("SELECT Opportunity.Id FROM OpportunityContactRole WHERE ContactId = {contact_id} AND Opportunity.All_documents_uploaded__c = False AND Opportunity.StageName != 'Closed Lost' AND Opportunity.StageName != 'Closed Won'", contact_id=user_contact_id))

        transactions_with_tasks_outstanding = len(get_transactions_with_tasks_outstanding['records'])

        returned_data = {
            'transactions': transactions,
            'has_result': True,
            'transactions_with_tasks_outstanding': transactions_with_tasks_outstanding
        }  
    else:
        returned_data = {
            'has_result': False
        }    

    return returned_data


def get_all_transactions(request):
    check_sf = check_salesforce_session(sf)
    user_contact_id = request.user.contact_id
    
    broker_name = request.GET.get('broker')
    status = request.GET.get('status')
    transaction_type = request.GET.get('type')
    additional_queries = ''

    print('====BROKER', broker_name)
    print('====STATUS', status)
    print('====TYPE', transaction_type)
    #print('===PAGE NUMBER', page_number)

    purchase_types = "('Real Estate - Purchase New Build', 'Real Estate - Resale Purchase (NEW)')"
    finance_types = "('Real Estate - Refinance New', 'Real Estate - Survivorship and Refinance', 'Real Estate - Title Transfer and Refi', 'Real Estate - Borrower Representation')"
    ila_types = "('Real Estate - ILA')"

    queries = " WHERE ContactId = '" + user_contact_id + "'"

    if(broker_name):
        queries += " AND (Opportunity.Real_Estate_Agent_Contact__c = '" + broker_name + "' OR Opportunity.Mortgage_Agent_Contact__c = '" + broker_name + "')"

    if(status):
        queries += " AND Opportunity.StageName LIKE '%" + status + "%'"

    if(transaction_type):
        list_to_check = ""
        if(transaction_type.lower() == 'purchase'):
            list_to_check = purchase_types
        elif(transaction_type.lower() == 'refi'):
            list_to_check = finance_types
        elif(transaction_type.lower() == 'ila'):
            list_to_check = ila_types

        queries += " AND Opportunity.Lead_Transaction_Type__c IN " + list_to_check + ""
        #queries += " AND Opportunity.Lead_Transaction_Type__c IN ('Real Estate - ILA')" 
    
    queries = "SELECT Opportunity.Id, Opportunity.Name, Opportunity.CloseDate, Opportunity.Lead_Transaction_Type__c, Opportunity.StageName, Opportunity.Lawyer_on_file__c, Opportunity.Assigned_Lawyer__c, Opportunity.Assigned_Lawyer_Full_Name__c, Opportunity.Assigned_Lawyer_Email_Address__c, Opportunity.Clerk_Assigned__c, Opportunity.Clerk_Assigned_Email_Address__c, Opportunity.Clerk_Assigned_Full_Name__c, Opportunity.Client_on_File__c, Opportunity.Purchase_Price__c, Opportunity.Sale_Price__c, Opportunity.RecordTypeId, Opportunity.Milestone__c, Opportunity.Milestone_Completion__c, Opportunity.RecordType.Name, Opportunity.Real_Estate_Agent_Contact__c, Opportunity.Mortgage_Agent_Contact__c FROM OpportunityContactRole" + queries + " AND Opportunity.StageName != 'Closed Lost' ORDER BY Opportunity.CloseDate DESC"
    print('=====QUERIES=====')
    print(queries)

    #result = check_sf.query_all(format_soql("SELECT Opportunity.Id, Opportunity.Name, Opportunity.CloseDate, Opportunity.Lead_Transaction_Type__c, Opportunity.StageName, Opportunity.Lawyer_on_file__c, Opportunity.Assigned_Lawyer__c, Opportunity.Assigned_Lawyer_Full_Name__c, Opportunity.Assigned_Lawyer_Email_Address__c, Opportunity.Clerk_Assigned__c, Opportunity.Clerk_Assigned_Email_Address__c, Opportunity.Clerk_Assigned_Full_Name__c, Opportunity.Client_on_File__c, Opportunity.Purchase_Price__c, Opportunity.Sale_Price__c, Opportunity.RecordTypeId, Opportunity.Milestone__c, Opportunity.Milestone_Completion__c, Opportunity.RecordType.Name, Opportunity.Real_Estate_Agent_Contact__c, Opportunity.Mortgage_Agent_Contact__c FROM OpportunityContactRole WHERE ContactId = {contact_id} AND Opportunity.StageName != 'Closed Lost' {additional_queries} ORDER BY Opportunity.CloseDate DESC", contact_id=user_contact_id, additional_queries = additional_queries))
    #result = check_sf.query_all("SELECT Opportunity.Id, Opportunity.Name, Opportunity.CloseDate, Opportunity.Lead_Transaction_Type__c, Opportunity.StageName, Opportunity.Lawyer_on_file__c, Opportunity.Assigned_Lawyer__c, Opportunity.Assigned_Lawyer_Full_Name__c, Opportunity.Assigned_Lawyer_Email_Address__c, Opportunity.Clerk_Assigned__c, Opportunity.Clerk_Assigned_Email_Address__c, Opportunity.Clerk_Assigned_Full_Name__c, Opportunity.Client_on_File__c, Opportunity.Purchase_Price__c, Opportunity.Sale_Price__c, Opportunity.RecordTypeId, Opportunity.Milestone__c, Opportunity.Milestone_Completion__c, Opportunity.RecordType.Name, Opportunity.Real_Estate_Agent_Contact__c, Opportunity.Mortgage_Agent_Contact__c FROM OpportunityContactRole" + queries + " AND Opportunity.StageName != 'Closed Lost' ORDER BY Opportunity.CloseDate DESC")
    result = check_sf.query_all(format_soql(queries))
 
    if(len(result['records'])):
        transactions = result['records']
        completed_transactions = [transactions for transaction in transactions if ('Closed' in transaction['Opportunity']['StageName'])] if transactions else []
        open_transactions = [transactions for transaction in transactions if ('Closed' not in transaction['Opportunity']['StageName'])] if transactions else []
        number_of_completed_transactions = len(completed_transactions)
        number_of_open_transactions = len(open_transactions)
        real_estate_brokers = [transaction['Opportunity']['Real_Estate_Agent_Contact__c'] for transaction in transactions if transaction['Opportunity']['Real_Estate_Agent_Contact__c']]
        mortgage_brokers = [transaction['Opportunity']['Mortgage_Agent_Contact__c'] for transaction in transactions if transaction['Opportunity']['Mortgage_Agent_Contact__c']]
        broker_ids = list(set(real_estate_brokers + mortgage_brokers))
        get_all_brokers = get_brokers(broker_ids)
        returned_data = {
            'total': len(transactions),
            'total_open': number_of_open_transactions,
            'total_completed': number_of_completed_transactions,
            'transactions': transactions,
            'brokers': get_all_brokers['brokers'] if get_all_brokers['has_result'] else [],
            'has_result': True
        }  
    else:
        returned_data = {
            'has_result': False
        }    

    return returned_data    


def get_brokers(ids):
    check_sf = check_salesforce_session(sf)

    result = check_sf.query_all(format_soql("SELECT Id, Name FROM Contact WHERE Id IN {list} ORDER BY NAME", list=ids))
 
    if(len(result['records'])):
        brokers = result['records']
        returned_data = {
            'brokers': brokers,
            'has_result': True
        }  
    else:
        returned_data = {
            'has_result': False
        }    

    return returned_data


def get_all_transactions_with_tasks_outstanding(request):
    check_sf = check_salesforce_session(sf)
    user_contact_id = request.user.contact_id

    result = check_sf.query_all(format_soql("SELECT Opportunity.Id, Opportunity.Name, Opportunity.CloseDate, Opportunity.Lead_Transaction_Type__c, Opportunity.StageName, Opportunity.Lawyer_on_file__c, Opportunity.Assigned_Lawyer__c, Opportunity.Assigned_Lawyer_Full_Name__c, Opportunity.Assigned_Lawyer_Email_Address__c, Opportunity.Clerk_Assigned__c, Opportunity.Clerk_Assigned_Email_Address__c, Opportunity.Clerk_Assigned_Full_Name__c, Opportunity.Client_on_File__c, Opportunity.Purchase_Price__c, Opportunity.Sale_Price__c, Opportunity.RecordTypeId, Opportunity.Milestone__c, Opportunity.Milestone_Completion__c, Opportunity.RecordType.Name FROM OpportunityContactRole WHERE ContactId = {contact_id} AND Opportunity.All_documents_uploaded__c = False AND Opportunity.StageName != 'Closed Lost' AND Opportunity.StageName != 'Closed Won'", contact_id=user_contact_id))
 
    if(len(result['records'])):
        transactions = result['records']
        returned_data = {
            'transactions': transactions,
            'has_result': True
        }  
    else:
        returned_data = {
            'has_result': False
        }    

    return returned_data


def get_task_details(request, opportunity_id):
    check_sf = check_salesforce_session(sf)
    result = check_sf.query_all(format_soql("SELECT Id, WhatId, WhoId, OwnerId, Subject, Status FROM Task WHERE WhatId = {opportunity_id} AND OwnerId = '0053j00000AbJYgAAN' AND Tasks_is_assigned_to12__c = 'CUSTOMER'", opportunity_id=opportunity_id))
 
    if(len(result['records'])):
        tasks = result['records']

        get_transaction = check_sf.query_all(format_soql("SELECT Id, Name, StageName, CloseDate FROM Opportunity WHERE Id = {transaction_id}", transaction_id=opportunity_id))
        transaction = get_transaction['records'][0]

        returned_data = {
            'tasks': tasks,
            'transaction': transaction,
            'has_result': True
        }
    else:
        returned_data = {
            'has_result': False
        }    

    return returned_data


def update_task_status(transaction_id, task_api, status):
    check_sf = check_salesforce_session(sf)
    try:
        check_sf.Opportunity.update(transaction_id,{task_api: status})
        return True 
    except:
        return False


def get_user_task_count(user_id):
    check_sf = check_salesforce_session(sf)

    result = check_sf.query_all(format_soql("SELECT Opportunity.Id, Opportunity.Name, Opportunity.CloseDate, Opportunity.Lead_Transaction_Type__c, Opportunity.StageName, Opportunity.Lawyer_on_file__c, Opportunity.Assigned_Lawyer__c, Opportunity.Assigned_Lawyer_Full_Name__c, Opportunity.Assigned_Lawyer_Email_Address__c, Opportunity.Clerk_Assigned__c, Opportunity.Clerk_Assigned_Email_Address__c, Opportunity.Clerk_Assigned_Full_Name__c, Opportunity.Client_on_File__c, Opportunity.Purchase_Price__c, Opportunity.Sale_Price__c, Opportunity.RecordTypeId, Opportunity.Milestone__c, Opportunity.Milestone_Completion__c, Opportunity.RecordType.Name FROM OpportunityContactRole WHERE ContactId = {contact_id} ORDER BY Opportunity.CloseDate DESC", contact_id=user_id))
 
    if(len(result['records'])):
        transactions = result['records']
        returned_data = {
            'transactions': transactions,
            'has_result': True
        }  
    else:
        returned_data = {
            'has_result': False
        }    

    return returned_data    


def user_has_portal_access(contact_id):
    portal_access = False
    check_sf = check_salesforce_session(sf)
    result = check_sf.query_all(format_soql("SELECT Id, LastName, FirstName, Portal_Access__c FROM Contact WHERE Id = {contact_id}", contact_id=contact_id))
    if(len(result['records'])):
        portal_access = result['records'][0]['Portal_Access__c']
        
    return portal_access
    
    
def user_can_register(email):
    check_sf = check_salesforce_session(sf)
    results = check_sf.query_all(format_soql("SELECT Id, LastName, FirstName, RecordTypeId, RecordType.Name FROM Contact WHERE (RecordTypeId = '0123j000001QPgLAAW' OR RecordTypeId = '0122A000000s5kvQAA' OR RecordTypeId = '0123j0000010Ck5AAE') AND Email = {email} LIMIT 1", email=email))
    if(len(results['records'])):
        first_name = results['records'][0]['FirstName']
        last_name = results['records'][0]['LastName']
        contact_id = results['records'][0]['Id']
        record_type_id = results['records'][0]['RecordTypeId']
        record_type = results['records'][0]['RecordType']['Name']
        returned_data = {
            'first_name': first_name,
            'last_name': last_name,
            'contact_id': contact_id,
            'record_type_id': record_type_id,
            'record_type': record_type,
            'can_register': True
        }
    else:
        returned_data = {
            'can_register': False
        }    

    return returned_data


def get_object_fields(obj):
    fields = getattr(sf,obj).describe()['fields']
    field_list = [i['name'] for i in fields]
    return field_list


def upload_document(request, document, transaction_id=None):
    current_user = auth.get_user(request)
    with document.open("rb") as temp:
        encoded_string = base64.b64encode(temp.read())

    check_sf = check_salesforce_session(sf)
    title = 'CU_' + document.name if transaction_id is None else '[Transaction ID: ' +  transaction_id + '] ' + 'CU_' +  document.name
    fields = {'title' : title, 'PathOnClient' : 'somepathdoesntmatterthatmuchtome','VersionData' : encoded_string.decode('utf-8')}


    contentv1 = check_sf.ContentVersion.create(fields)


def file_exists(file_path):
    my_session = boto3.Session(region_name="us-east-2")

    return wr.s3.does_object_exist("s3://axess-client-portal" + file_path, boto3_session=my_session)


def get_transaction_data(record_type_id):
    return next((transaction[record_type_id] for transaction in transaction_data if record_type_id in transaction), {}) 


def get_clerk_data(clerk_email):
    return next((clerk[clerk_email] for clerk in clerk_data if clerk_email in clerk), {}) 


def get_bdm_data(bdm_name):
    return next((bdm[bdm_name] for bdm in bdm_data if bdm_name in bdm), {}) 


def sync_shift_planning():
    utc_tzinfo = pytz.timezone('UTC')
    sp_format = '%Y%m%dT%H%M%SZ'
    sf_format = '%Y-%m-%dT%H:%M:%S.%f%z'
    url = 'https://axess1.humanity.com/ical/_649c0be3a5c894b5f0466765cdf5fb70.ics?1536861728082'
    start_dt = datetime.today()
    end_dt = start_dt + relativedelta(months=+1)
    start_dt = start_dt.astimezone(utc_tzinfo) 
    end_dt = end_dt.astimezone(utc_tzinfo) 
    report = ''
    matched_contacts = []
    matched_contacts_2 = []

    output = requests.get(url).text
    lines = output.split('\r\n')

    sf_events = search_events_for_sync()
    sf_contacts = search_contacts('@axesslaw.com')
    sf_event  = {}
    sf_event_2 = {}
    update_sf_events = []
    insert_sf_events = []
    locations = dict(get_location_code())

    for line in lines:
        if line == 'BEGIN:VEVENT':
            matched_contacts = []
            matched_contacts_2 = []
            sf_event  = {}
            sf_event_2 = {}
        elif line.startswith('DTSTART:'):
            dtstart = line.replace('DTSTART:', '').strip()
            sf_event['StartDateTime'] = parse(dtstart).astimezone(utc_tzinfo).strftime(sp_format)
        elif line.startswith('DTEND:'):
            dtend = line.replace('DTEND:', '').strip()
            sf_event['EndDateTime'] = parse(dtend).astimezone(utc_tzinfo).strftime(sp_format)
        elif line.startswith('UID:'):
            sf_event['ExternalId__c'] = line.replace('UID:', '').strip()
        elif line.startswith('SUMMARY:'):
            summary = line.replace('SUMMARY:', '').split(' ')

            if(len(summary) > 2 and any(summary[0] in location for location in locations)):
                sf_event['Subject'] = summary[1].upper()
                sf_event['OwnerId'] = next((location[summary[0]] for location in locations if summary[0] in location), '') 
                sf_event['Description'] = line.replace('SUMMARY:', '')
        
        elif line.startswith('DESCRIPTION:'):
            parts = line.split('-')
            if(len(parts) > 1):
                name = line.split('-')[1].strip().replace('\\n', '')
                names = name.split(' ')
                first_name = names[0]
                last_name = names[len(names) - 1]
                sf_event['WhoId'] = get_contact(first_name, last_name, sf_contacts, matched_contacts)
            if(len(parts) > 2):
                name = line.split('-')[2].strip().replace('\\n', '')
                names = name.split(' ')
                first_name = names[0]
                last_name = names[len(names) - 1]
                copy_event(sf_event, sf_event_2)
                sf_event_2['WhoId'] = get_contact(first_name, last_name, sf_contacts, matched_contacts_2)
        elif line == 'END:VEVENT':
            sf_event['Booking_created_by__c'] = 'Sync'
            sf_event_2['Booking_created_by__c'] = 'Sync'
            sf_start_dt = datetime.strptime(sf_event['StartDateTime'], sf_format)
            sf_end_dt = datetime.strptime(sf_event['EndDateTime'], sf_format)

            # out of time range
            if(sf_start_dt < start_dt or sf_end_dt > end_dt):
                pass

            if((sf_event['WhoId'] is not None) and (sf_event['OwnerId'] is not None) and (sf_event['Subject'] is not None)):
                    
                action = get_action(sf_events, sf_event, matched_contacts)

                if(action == 1):
                    update_sf_events.append(sf_event)
                    #report += string.Format("\r\nUpdate:{0}{1}", sFEvent.StartDateTime, sFEvent.Description)
                
                elif(action == 0):
                    insert_sf_events.append(sf_event)
                    #report += string.Format("\r\nInsert:{0}{1}", sFEvent.StartDateTime, sFEvent.Description);

            if((sf_event_2['WhoId'] is not None) and (sf_event_2['OwnerId'] is not None) and (sf_event_2['Subject'] is not None)):
            
                action_2 = get_action(sf_events, sf_event_2, matched_contacts_2)

                if(action_2 == 1):
                    update_sf_events.append(sf_event_2)
                    #report += string.Format("\r\nUpdate:{0}{1}", sFEvent2.StartDateTime, sFEvent2.Description);
                
                elif(action_2 == 0):
                    insert_sf_events.append(sf_event_2)
                    #report += string.Format("\r\nInsert:{0}{1}", sFEvent2.StartDateTime, sFEvent2.Description);
                

    create_events(insert_sf_events)
    update_events(update_sf_events)


def create_events(sf_events):
    if(len(sf_events) > 0):
        pass


def update_events(sf_events):
    if(len(sf_events) > 0):
        pass


def search_events_for_sync(start_dt, end_dt):
    events = []
     
    check_sf = check_salesforce_session(sf)
    result = check_sf.query_all(format_soql("SELECT Id, IsAllDayEvent, StartDateTime, EndDateTime, Subject, OwnerId, WhoId, Email_Template__c, ExternalId__c, Description, Booking_created_by__c FROM Event WHERE StartDateTime > {start} AND EndDateTime < {end} AND (Subject LIKE '%LAWYER%' OR Subject LIKE '%CSR%')", start = start_dt, end = end_dt))

    if(len(result['records'])):
        events = result['records']
    
    return events


def search_contacts(email):
    check_sf = check_salesforce_session(sf)
    result = check_sf.query_all(format_soql("SELECT Id, FirstName, LastName, AccountId FROM Contact WHERE EMAIL LIKE {email}", email=email))
    if(len(result['records'])):
        contacts = result['records']
        return contacts

    return None


def get_location_code():
    locations = [
        {'HQ': '005F0000002Pc69IAC'},
        {'EGN': '0232A000008ZkGtQAK'},
        {'STC': '023F00000027QYOIA2'},
        {'THL': '0232A000008ZiTHQA0'},
        {'ETB': '0232A000008ZkGjQAK'},
        {'HRT': '0232A000008ZkGeQAK'},
        {'WCH': '0232A000008ZkGUQA0'},
        {'RCH': '0232A000008ZkGPQA0'},
        {'VGN': '0233j000008AnBQAA0'},
        {'OTT': '0233j000008AsxoAAC'}
    ]

    return locations


def get_contact(first_name, last_name, sf_contacts, matched_contacts):
    contact_id = ''
    
    for contact in sf_contacts:
        if((contact['FirstName'] is None) or (contact['LastName'] is None)):
            pass
        elif((contact['FirstName'].lower() == first_name.lower() and 
            contact['LastName'].lower() == last_name.lower()) or 
            (contact['FirstName'].lower().startswith(first_name.lower()) and 
            contact['LastName'].lower().startswith(last_name.lower()))):
            matched_contacts.append(contact['Id'])
            contact_id = contact['Id']
            break

    return contact_id


def copy_event(sf_event, sf_event_2):
    sf_event_2['StartDateTime'] = sf_event['StartDateTime']
    sf_event_2['EndDateTime'] = sf_event['EndDateTime']
    sf_event_2['Subject'] = sf_event['Subject']
    sf_event_2['OwnerId'] = sf_event['OwnerId']
    sf_event_2['Description'] = sf_event['Description'] + '(2)'
    sf_event_2['ExternalId__c'] = sf_event['ExternalId__c'] + '2'


def get_action(sf_events, sf_event, matched_contacts):
    action = 0


    return action