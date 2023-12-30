from django import template
from datetime import datetime
from urllib.parse import urlencode
import boto3
import awswrangler as wr

register = template.Library()

@register.filter()
def string_to_datetime(value):
    return datetime.strptime(value, '%Y-%m-%d').date()


@register.filter()
def sfdc_datetime_to_datetime(value):
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f%z').date()    


@register.filter()
def percentage_of(numerator, denominator):
    if denominator is None or denominator == 0:
        return False
    return round(numerator*100/denominator)
    

@register.filter()
def file_exists(file_path):
    my_session = boto3.Session(region_name="us-east-2")

    return wr.s3.does_object_exist("s3://axess-client-portal" + file_path, boto3_session=my_session)


@register.simple_tag()
def url_replace(request, field, value):
    # query = context['request'].GET.copy()
    # query.update(kwargs)
    # return query.urlencode() 

    dict_ = request.GET.copy()

    dict_[field] = value

    return dict_.urlencode()
