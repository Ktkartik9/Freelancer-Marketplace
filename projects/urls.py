from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('create/', views.create_project, name='create_project'),
    path('<int:project_id>/', views.project_detail, name='project_detail'),
    path('bid/<int:project_id>/', views.place_bid, name='place_bid'),
    path('bids/<int:project_id>/', views.view_bids, name='view_bids'),
    path('select/<int:bid_id>/', views.select_freelancer, name='select_freelancer'),
    path('my/', views.my_projects, name='my_projects'),
    path('chat/<int:project_id>/<int:user_id>/', views.chat_view, name='chat'),
    path('projects/accept-bid/<int:bid_id>/', views.select_freelancer, name='accept_bid'),
    path('my-bids/', views.my_bids, name='my_bids'),
    path('messages/', views.messages_list, name='messages_list'),
    path('reject-bid/<int:bid_id>/', views.reject_bid, name='reject_bid'),
]
