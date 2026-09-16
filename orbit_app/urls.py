from django.urls import path
from . import views
urlpatterns=[
 path('',views.dashboard,name='dashboard'),
 path('experts/',views.expert_list,name='expert_list'),
 path('matching/',views.matching,name='matching'),
 path('experts/nouveau/',views.expert_edit,name='expert_create'),
 path('experts/<int:pk>/',views.expert_detail,name='expert_detail'),
 path('experts/<int:pk>/modifier/',views.expert_edit,name='expert_edit'),
 path('demandes/',views.request_list,name='request_list'),
 path('demandes/nouvelle/',views.request_edit,name='request_create'),
 path('demandes/<int:pk>/',views.request_detail,name='request_detail'),
 path('demandes/<int:pk>/modifier/',views.request_edit,name='request_edit'),
 path('sollicitations/',views.solicitation_list,name='solicitation_list'),
 path('sollicitations/nouvelle/<int:expert_id>/',views.solicitation_create,name='solicitation_create'),
 path('sollicitations/<int:pk>/',views.solicitation_detail,name='solicitation_detail'),
 path('missions/',views.mission_list,name='mission_list'),
 path('missions/<int:pk>/',views.mission_detail,name='mission_detail'),
 path('notifications/',views.notifications,name='notifications'),
 path('notifications/apercu/',views.notification_preview,name='notification_preview'),
 path('notifications/<int:pk>/lu/',views.mark_notification_read,name='mark_notification_read'),
 path('journal/',views.audit_list,name='audit_list'),
 path('rapports/',views.reports,name='reports'),
 path('administration/',views.functional_admin,name='functional_admin'),
]

