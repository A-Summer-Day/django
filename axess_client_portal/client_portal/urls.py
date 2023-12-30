from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('transactions/', views.transactions, name='transactions'),
    #path('transactions/<int:page_number>', views.transactions, name='transactions'),
    path('transactions/<str:transaction_id>', views.transaction_details, name='transaction-details'),
    path('tasks/', views.tasks, name='tasks'),
    path('tasks/<str:opportunity_id>', views.task_details, name='task-details'),
    path('send-email/', views.send_email, name='send-email'),
    path('send-message-to-clerk/', views.send_message_to_clerk, name='send-message-to-clerk'),
    path('profile/', views.profile, name='profile'),
    path('document-upload/', views.document_upload, name = 'document-upload'),
    path('modal-document-upload/', views.modal_document_upload, name = 'modal-document-upload'),
    path('file/', views.file, name = 'file'),
    path('sync/', views.sync, name = 'sync')
]
 