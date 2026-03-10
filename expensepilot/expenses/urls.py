from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register_view, name='register'),
    
    path('dashboard/', views.dashboard, name='dashboard'),

    # Expense URLs
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_create, name='expense_add'),
    path('expenses/edit/<int:pk>/', views.expense_update, name='expense_edit'),
    path('expenses/delete/<int:pk>/', views.expense_delete, name='expense_delete'),

    # Income
    path('income/add/', views.add_income, name='add_income'),

    # Charts
    path('charts/monthly/', views.monthly_chart, name='monthly_chart'),
    path('charts/yearly/', views.yearly_chart, name='yearly_chart'),

    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-users/', views.admin_user_list, name='admin_user_list'),
    path('admin-user/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
]