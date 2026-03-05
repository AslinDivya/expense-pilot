
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
from django.utils import timezone


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
def monthly_chart(request):
    data = (
        Expense.objects
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    labels = [d['month'].strftime("%b %Y") for d in data]
    totals = [float(d['total']) for d in data]

    context = {
        'labels': json.dumps(labels),
        'totals': json.dumps(totals),
    }

    return render(request, 'expenses/monthly_chart.html', context)


def yearly_chart(request):
    data = (
        Expense.objects
        .annotate(year=TruncYear('date'))
        .values('year')
        .annotate(total=Sum('amount'))
        .order_by('year')
    )

    labels = [d['year'].strftime("%Y") for d in data]
    totals = [float(d['total']) for d in data]

    context = {
        'labels': json.dumps(labels),
        'totals': json.dumps(totals),
    }

    return render(request, 'expenses/yearly_chart.html', context)

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
    total_users = User.objects.count()
    total_expense_count = Expense.objects.count()

    this_month_total = Expense.objects.filter(
        date__month=timezone.now().month,
        date__year=timezone.now().year
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    recent_expenses = Expense.objects.select_related('user').order_by('-date')[:5]

    context = {
        'total_users': total_users,
        'total_expense_count': total_expense_count,
        'this_month_total': this_month_total,
        'recent_expenses': recent_expenses,
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


def admin_user_list(request):
    if not request.user.is_superuser:
        return redirect('home')

    users = User.objects.all()

    return render(request, 'expenses/admin_user_list.html', {'users': users})


def admin_user_detail(request, user_id):
    if not request.user.is_superuser:
        return redirect('home')

    user = User.objects.get(id=user_id)

    # Monthly Expense
    monthly_expense = (
        Expense.objects
        .filter(user=user)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total_expense=Sum('amount'))
        .order_by('month')
    )

    # Monthly Income
    monthly_income = (
        MonthlyFinance.objects
        .filter(user=user)
        .values('month')
        .annotate(total_income=Sum('income'))
        .order_by('month')
    )

    # Convert income queryset to dictionary
    income_dict = {
        entry['month'].strftime("%b %Y"): entry['total_income']
        for entry in monthly_income
    }

    monthly_data = []

    for expense in monthly_expense:
        month_label = expense['month'].strftime("%b %Y")
        expense_amount = expense['total_expense']
        income_amount = income_dict.get(month_label, 0)
        balance = income_amount - expense_amount

        monthly_data.append({
            'month': month_label,
            'income': income_amount,
            'expense': expense_amount,
            'balance': balance
        })

    context = {
        'user': user,
        'monthly_data': monthly_data
    }

    return render(request, 'expenses/admin_user_detail.html', context)