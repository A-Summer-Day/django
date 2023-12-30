from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('file-submission', views.file_submission, name='file-submission'),
    path('document-upload', views.document_upload, name='document-upload'),
    path('referral', views.referral, name='referral'),
    path('api-token-auth/', obtain_auth_token, name='api-token-auth')
]


