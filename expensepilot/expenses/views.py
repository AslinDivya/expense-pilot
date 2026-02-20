
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncYear
from django.contrib.auth import authenticate, login
from .models import Expense
from .forms import ExpenseForm, RegisterForm
from django.shortcuts import redirect
from collections import defaultdict
from django.contrib.auth.models import User
import calendar
from .models import Income
from .forms import IncomeForm
from datetime import datetime
from .models import MonthlyFinance

def home(request):
    return render(request, 'home.html')



def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})
@login_required

def dashboard(request):

    if request.user.is_superuser:
        expenses = Expense.objects.all()
        is_admin = True
    else:
        expenses = Expense.objects.filter(user=request.user)
        is_admin = False

    # Unique user-month from expenses
    expense_months = expenses.annotate(
        month=TruncMonth('date')
    ).values('user', 'month').distinct()

    finance_data = []

    for item in expense_months:
        user_id = item['user']
        month = item['month']

        # Get user object safely
        user_obj = User.objects.get(id=user_id)

        # Total expense for that month
        total_expense = Expense.objects.filter(
            user=user_obj,
            date__year=month.year,
            date__month=month.month
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Check income
        monthly_finance = MonthlyFinance.objects.filter(
            user=user_obj,
            month=month
        ).first()

        income = monthly_finance.income if monthly_finance else 0

        balance = income - total_expense

        finance_data.append({
            'user': user_obj.username,
            'month': month.strftime("%B %Y"),
            'income': income,
            'expense': total_expense,
            'balance': balance
        })

    context = {
        'finance_data': finance_data,
        'is_admin': is_admin
    }

    return render(request, 'expenses/dashboard.html', context)




@login_required
def expense_list(request):
    if request.user.is_superuser:
        expenses = Expense.objects.all()   # Admin → all users data
    else:
        expenses = Expense.objects.filter(user=request.user)  # Normal user → own data

    return render(request, 'expenses/expense_list.html', {'expenses': expenses})


@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()

            expense_month = expense.date.replace(day=1)

            monthly_finance, created = MonthlyFinance.objects.get_or_create(
                user=request.user,
                month=expense_month
            )

            income_input = form.cleaned_data.get('income_for_month')

            # NEW LOGIC
            if income_input:
                monthly_finance.income = income_input
                monthly_finance.save()

            return redirect('expense_list')
    else:
        form = ExpenseForm()

    return render(request, 'expenses/expense_form.html', {'form': form})

@login_required
def expense_update(request, pk):
    expense = get_object_or_404(Expense, pk=pk)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.save()

            # Get month
            expense_month = expense.date.replace(day=1)

            monthly_finance, created = MonthlyFinance.objects.get_or_create(
                user=request.user,
                month=expense_month
            )

            income_input = form.cleaned_data.get('income_for_month')

            if income_input:
                monthly_finance.income = income_input
                monthly_finance.save()

            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)

    return render(request, 'expenses/expense_form.html', {'form': form})

@login_required
def expense_delete(request, pk):

    if request.user.is_superuser:
        expense = get_object_or_404(Expense, pk=pk)
    else:
        expense = get_object_or_404(Expense, pk=pk, user=request.user)

    expense.delete()
    return redirect('expense_list')


@login_required


def monthly_chart(request):

    monthly = (
        Expense.objects
        .filter(user=request.user)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    labels = []
    amounts = []

    for item in monthly:
        labels.append(item['month'].strftime("%b %Y"))
        amounts.append(float(item['total']))

    context = {
        "labels": json.dumps(labels),
        "amounts": json.dumps(amounts),
    }

    return render(request, 'expenses/monthly_chart.html', context)



@login_required
def yearly_chart(request):
    data = Expense.objects.filter(user=request.user)\
        .annotate(year=TruncYear('date'))\
        .values('year')\
        .annotate(total=Sum('amount'))\
        .order_by('year')
    return render(request, 'expenses/yearly_chart.html', {'data': data})


def manage_expense(request):
    if request.user.is_superuser:
        expenses = Expense.objects.all()  # show all users data
    else:
        expenses = Expense.objects.filter(user=request.user)  # show only own data

    return render(request, 'manage_expense.html', {'expenses': expenses})


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('dashboard')

    return render(request, 'login.html')

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncYear
from collections import defaultdict
import json

def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('home')

    total_users = User.objects.count()

    total_expenses = Expense.objects.aggregate(
        Sum('amount')
    )['amount__sum'] or 0

    total_income = MonthlyFinance.objects.aggregate(
        Sum('income')
    )['income__sum'] or 0

    total_balance = total_income - total_expenses

    # -----------------------
    # MONTHLY TOTAL (EXPENSE)
    # -----------------------
    monthly = (
        Expense.objects
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    # -----------------------
    # YEARLY TOTAL (EXPENSE)
    # -----------------------
    yearly = (
        Expense.objects
        .annotate(year=TruncYear('date'))
        .values('year')
        .annotate(total=Sum('amount'))
        .order_by('year')
    )

    # -----------------------
    # USER MONTH DATA
    # -----------------------
    user_month_data = defaultdict(list)
    expenses = Expense.objects.select_related('user')

    for expense in expenses:
        month_label = expense.date.strftime("%b %Y")
        user_month_data[month_label].append({
            "username": expense.user.username,
            "amount": float(expense.amount)
        })

    # -----------------------
    # USER YEAR DATA
    # -----------------------
    user_year_data = defaultdict(list)

    for expense in expenses:
        year_label = expense.date.strftime("%Y")
        user_year_data[year_label].append({
            "username": expense.user.username,
            "amount": float(expense.amount)
        })

    context = {
        'total_users': total_users,
        'total_expenses': total_expenses,
        'total_income': total_income,
        'total_balance': total_balance,
        'monthly': monthly,
        'yearly': yearly,
        'user_month_data': json.dumps(user_month_data),
        'user_year_data': json.dumps(user_year_data),
    }

    return render(request, 'expenses/admin_dashboard.html', context)


def add_income(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            return redirect('dashboard')  # change if needed
    else:
        form = IncomeForm()

    return render(request, 'expenses/add_income.html', {'form': form})