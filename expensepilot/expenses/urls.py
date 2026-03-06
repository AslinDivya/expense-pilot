from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_create, name='expense_add'),
    path('expenses/edit/<int:pk>/', views.expense_update, name='expense_edit'),
    path('expenses/delete/<int:pk>/', views.expense_delete, name='expense_delete'),

    path('charts/monthly/', views.monthly_chart, name='monthly_chart'),
    path('charts/yearly/', views.yearly_chart, name='yearly_chart'),
    path('income/add/', views.add_income, name='add_income'),
    path('admin-users/', views.admin_user_list, name='admin_user_list'),
    path('admin-user/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),

    path('user/charts/monthly/', views.user_monthly_chart, name='user_monthly_chart'),
    path('user/charts/yearly/', views.user_yearly_chart, name='user_yearly_chart'),

]
