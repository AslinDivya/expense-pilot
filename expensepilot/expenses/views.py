
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

    total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'expenses/dashboard.html', {
        'expenses': expenses,
        'total': total,
        'is_admin': is_admin
    })



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
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'expenses/expense_form.html', {'form': form})

@login_required
def expense_update(request, pk):

    if request.user.is_superuser:
        expense = get_object_or_404(Expense, pk=pk)
    else:
        expense = get_object_or_404(Expense, pk=pk, user=request.user)

    form = ExpenseForm(request.POST or None, instance=expense)

    if form.is_valid():
        form.save()
        return redirect('expense_list')

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

    # -----------------------
    # MONTHLY TOTAL
    # -----------------------
    monthly = (
        Expense.objects
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    # User-wise monthly
    user_month_raw = (
        Expense.objects
        .annotate(month=TruncMonth('date'))
        .values('month', 'user__username')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    user_month_data = defaultdict(list)

    for item in user_month_raw:
        month_str = item['month'].strftime("%b %Y")
        user_month_data[month_str].append({
            "username": item['user__username'],
            "amount": float(item['total'])
        })

    # -----------------------
    # YEARLY TOTAL
    # -----------------------
    yearly = (
        Expense.objects
        .annotate(year=TruncYear('date'))
        .values('year')
        .annotate(total=Sum('amount'))
        .order_by('year')
    )

    # User-wise yearly
    yearly_user_raw = (
        Expense.objects
        .annotate(year=TruncYear('date'))
        .values('year', 'user__username')
        .annotate(total=Sum('amount'))
        .order_by('year')
    )

    user_year_data = defaultdict(list)

    for item in yearly_user_raw:
        year_str = item['year'].strftime("%Y")
        user_year_data[year_str].append({
            "username": item['user__username'],
            "amount": float(item['total'])
        })

    # -----------------------
    # FINAL CONTEXT (ONLY ONCE)
    # -----------------------
    context = {
        'total_users': total_users,
        'total_expenses': total_expenses,
        'monthly': monthly,
        'yearly': yearly,
        'user_month_data': json.dumps(user_month_data),
        'user_year_data': json.dumps(user_year_data),
    }

    return render(request, 'expenses/admin_dashboard.html', context)
