from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.category_list_create, name='category-list-create'),
    path('categories/<int:pk>/', views.category_detail, name='category-detail'),
    path('categoriesList/<int:pk>/', views.category_list_by_user, name='category-list-by_user'),
    path('monthly-budgets/', views.monthly_budget_list_create, name='monthly-budget-list-create'),
    path('monthly-budgets/<int:pk>/', views.monthly_budget_detail, name='monthly-budget-detail'),
    path('transactions/', views.transaction_list_create, name='transaction-list-create'),
    path('transactions/<int:pk>/', views.transaction_detail, name='transaction-detail'),
    path('financial-data/', views.get_financial_data, name='get_financial_data'),
]
