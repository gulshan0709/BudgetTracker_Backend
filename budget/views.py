from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Category,MonthlyBudget,Transaction
from .serializers import CategorySerializer,MonthlyBudgetSerializer,TransactionSerializer,TransactionDetailSerializer
from django.db.models import Q, Sum, Case, When, Value, DecimalField
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from datetime import datetime


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size'  
    max_page_size = 100


def get_monthly_summary(user_id, year,month_num):
    current_year = year
    current_month = month_num
    
    end_month = current_month if year == current_year else 12
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_data = []
    
    for month_num in range(1, end_month + 1):
        income_sum = Transaction.objects.filter(
            user_id=user_id,
            type='Income',
            date__year=year,
            date__month=month_num
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        expense_sum = Transaction.objects.filter(
            user_id=user_id,
            type='Expense',
            date__year=year,
            date__month=month_num
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        monthly_entry = {
            'month': month_names[month_num - 1],
            'income': float(income_sum),
            'expenses': float(expense_sum)
        }
        
        monthly_data.append(monthly_entry)
    
    return monthly_data


@api_view(['GET'])
def category_list_by_user(request, pk):
    categories = Category.objects.filter(user__id=pk)
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def category_list_create(request):
    if request.method == 'GET':
        user_id = request.query_params.get('user')
        search_query = request.query_params.get('search', "")
        
        if user_id:
            categories = Category.objects.filter(user__id=user_id)
        else:
            categories = Category.objects.filter(
                Q(user=request.user) | Q(user__isnull=True)
            )
        
        if search_query:
            categories = categories.filter(
                Q(name__icontains=search_query) | 
                Q(type__icontains=search_query)  
            )
        
        paginator = StandardResultsSetPagination()
        paginated_categories = paginator.paginate_queryset(categories, request)
        serializer = CategorySerializer(paginated_categories, many=True)
        
        return paginator.get_paginated_response(serializer.data)



    elif request.method == 'POST':
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','PUT', 'DELETE'])
def category_detail(request, pk):
    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        category.delete()
        return Response({'message': 'Category deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def monthly_budget_list_create(request):
    if request.method == 'GET':
        month = request.query_params.get('month')
        search = request.query_params.get('search')
        user_id = request.query_params.get('user')
        
        budgets = MonthlyBudget.objects.filter(user=user_id)
        
        if month:
            budgets = budgets.filter(month=month)
            
        if search:
            budgets = budgets.filter(month__icontains=search)
        
        paginator = StandardResultsSetPagination()
        paginated_budgets = paginator.paginate_queryset(budgets, request)
        
        serializer = MonthlyBudgetSerializer(paginated_budgets, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        serializer = MonthlyBudgetSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def monthly_budget_detail(request, pk):
   
    budget = get_object_or_404(MonthlyBudget, pk=pk, user=request.user)
    
    if request.method == 'GET':
        serializer = MonthlyBudgetSerializer(budget)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = MonthlyBudgetSerializer(
            budget, 
            data=request.data,
            context={'request': request},
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        budget.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def transaction_list_create(request):
    if request.method == 'GET':
        search_term = request.query_params.get('search_term')
        transaction_type = request.query_params.get('type')
        category_id = request.query_params.get('category_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        user = request.query_params.get('user') 
        
        transactions = Transaction.objects.filter(user=user).order_by('-date')
        
        if search_term:
            transactions = transactions.filter(
                    Q(description__icontains=search_term) | Q(amount__icontains=search_term)| Q(id__icontains=search_term)
                )
            
        if transaction_type:
            transactions = transactions.filter(type=transaction_type)
            
        if category_id:
            transactions = transactions.filter(category_id=category_id)
            
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
                transactions = transactions.filter(date__gte=start_datetime)
            except ValueError:
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    transactions = transactions.filter(date__gte=start_date)
                except ValueError:
                    return Response(
                        {"error": "Invalid start_date format. Use YYYY-MM-DDThh:mm or YYYY-MM-DD."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
                transactions = transactions.filter(date__lte=end_datetime)
            except ValueError:
                try:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    transactions = transactions.filter(date__lte=end_date)
                except ValueError:
                    return Response(
                        {"error": "Invalid end_date format. Use YYYY-MM-DDThh:mm or YYYY-MM-DD."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        paginator = StandardResultsSetPagination()
        paginated_transactions = paginator.paginate_queryset(transactions, request)
        
        serializer = TransactionSerializer(paginated_transactions, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        serializer = TransactionSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            transaction = serializer.save(user=request.user)
            detail_serializer = TransactionDetailSerializer(transaction)
            return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def transaction_detail(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    if request.method == 'GET':
        serializer = TransactionDetailSerializer(transaction)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = TransactionSerializer(
            transaction,
            data=request.data,
            context={'request': request},
            partial=True
        )
        
        if serializer.is_valid():
            updated_transaction = serializer.save()
            detail_serializer = TransactionDetailSerializer(updated_transaction)
            return Response(detail_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        transaction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


@api_view(['GET'])
def get_financial_data(request):
    user_id = request.query_params.get('user_id')
    month = request.query_params.get('month')
    
    if not month or not month.strip():
        return Response({"error": "Month parameter is required in YYYY-MM format"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        datetime.strptime(month, '%Y-%m')
    except ValueError:
        return Response({"error": "Month must be in YYYY-MM format"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    
    if user_id:
        target_user_id = user_id
    else:
        target_user_id = request.user.id
    
    budget_data = {}
    
    year, month_num = month.split('-')
    month_int = int(month_num)
    year_int = int(year)
    
    months_to_fetch = [month]
    
    prev_month_int = month_int - 1
    prev_year_int = year_int
    if prev_month_int < 1:
        prev_month_int = 12
        prev_year_int -= 1
    prev_month = f"{prev_year_int}-{prev_month_int:02d}"
    months_to_fetch.append(prev_month)
    
    prev2_month_int = prev_month_int - 1
    prev2_year_int = prev_year_int
    if prev2_month_int < 1:
        prev2_month_int = 12
        prev2_year_int -= 1
    prev2_month = f"{prev2_year_int}-{prev2_month_int:02d}"
    months_to_fetch.append(prev2_month)
    
    budgets = MonthlyBudget.objects.filter(
        user_id=target_user_id, 
        month__in=months_to_fetch
    )
    
    budget_data = {budget.month: float(budget.total_budget_amount) for budget in budgets}
    
    transactions = Transaction.objects.filter(
        user_id=target_user_id,
        date__year=int(year),
        date__month=int(month_num)
    ).select_related('category')
    
    formatted_transactions = []
    for transaction in transactions:
        formatted_transaction = {
            'id': transaction.id,
            'type': transaction.type,
            'amount': float(transaction.amount),
            'category_id': transaction.category_id,
            'date': transaction.date.strftime('%Y-%m-%d'),
            'time': transaction.date.strftime('%I:%M %p'),
            'description': transaction.description or ''
        }
        formatted_transactions.append(formatted_transaction)
    
    categories = Category.objects.filter(
        Q(user_id=target_user_id) | Q(user__isnull=True)
    )
    
    formatted_categories = []
    for category in categories:
        formatted_category = {
            'id': category.id,
            'name': category.name,
            'type': category.type,
            'icon': category.icon,
            'color': category.color or '#CCCCCC'
        }
        formatted_categories.append(formatted_category)

    monthly_summary = get_monthly_summary(target_user_id, int(year),int(month_num))
    
    response_data = {
        'budgets': budget_data,
        'transactions': formatted_transactions,
        'categories': formatted_categories,
        'monthlyData': monthly_summary
    }
    
    return Response(response_data)
