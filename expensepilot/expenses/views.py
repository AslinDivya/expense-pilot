from django.shortcuts import render, redirect, get_object_or_404
from .models import Expense, Income
from .forms import ExpenseForm, IncomeForm, RegisterForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncYear
import json


def home(request):
    return render(request,'home.html')


def register_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 == password2:

            from django.contrib.auth.models import User

            User.objects.create_user(username=username, password=password1)

            return redirect("login")

    return render(request,"register.html")
def user_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:

            login(request,user)

            return redirect("dashboard")

    return render(request,"login.html")

@login_required
def dashboard(request):

    expenses = Expense.objects.filter(user=request.user)

    total = expenses.aggregate(Sum("amount"))["amount__sum"] or 0

    return render(request, "dashboard.html", {"total": total})


@login_required
def expense_list(request):

    if request.user.is_superuser:
        expenses = Expense.objects.all()
    else:
        expenses = Expense.objects.filter(user=request.user)

    return render(request, "expense_list.html", {"expenses": expenses})


@login_required
def expense_create(request):

    if request.method == "POST":

        form = ExpenseForm(request.POST)

        if form.is_valid():

            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()

            return redirect("expense_list")

    else:
        form = ExpenseForm()

    return render(request, "expense_form.html", {"form": form})


@login_required
def expense_update(request, pk):

    expense = get_object_or_404(Expense, pk=pk)

    form = ExpenseForm(request.POST or None, instance=expense)

    if form.is_valid():
        form.save()
        return redirect("expense_list")

    return render(request, "expense_form.html", {"form": form})


@login_required
def expense_delete(request, pk):

    expense = get_object_or_404(Expense, pk=pk)

    expense.delete()

    return redirect("expense_list")


@login_required
def add_income(request):

    if request.method == "POST":

        form = IncomeForm(request.POST)

        if form.is_valid():

            income = form.save(commit=False)
            income.user = request.user
            income.save()

            return redirect("dashboard")

    else:
        form = IncomeForm()

    return render(request, "add_income.html", {"form": form})


def admin_dashboard(request):

    total_users = User.objects.count()
    total_expenses = Expense.objects.count()

    context = {
        "total_users": total_users,
        "total_expenses": total_expenses,
    }

    return render(request, "admin_dashboard.html", context)


def admin_user_list(request):

    users = User.objects.all()

    return render(request, "admin_user_list.html", {"users": users})


def admin_user_detail(request, user_id):

    user = User.objects.get(id=user_id)

    expenses = Expense.objects.filter(user=user)

    return render(request, "admin_user_detail.html", {"user": user, "expenses": expenses})

from django.db.models.functions import TruncMonth
from django.db.models import Sum
import json


def monthly_chart(request):

    data = (
        Expense.objects
        .filter(user=request.user)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    labels = []
    totals = []

    for item in data:
        labels.append(item['month'].strftime("%b %Y"))
        totals.append(float(item['total']))

    context = {
        "labels": json.dumps(labels),
        "totals": json.dumps(totals)
    }

    return render(request,"monthly_chart.html",context)

from django.db.models.functions import ExtractYear


def yearly_chart(request):

    data = (
        Expense.objects
        .filter(user=request.user)
        .annotate(year=ExtractYear('date'))
        .values('year')
        .annotate(total=Sum('amount'))
        .order_by('year')
    )

    years=[]
    totals=[]

    for item in data:
        years.append(item['year'])
        totals.append(float(item['total']))

    context={
        "years":json.dumps(years),
        "totals":json.dumps(totals)
    }

    return render(request,"yearly_chart.html",context)


def admin_dashboard(request):

    total_users = User.objects.count()

    total_expense = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        "total_users": total_users,
        "total_expense": total_expense
    }

    return render(request,"admin_dashboard.html",context)

def admin_user_list(request):

    if not request.user.is_superuser:
        return redirect('dashboard')

    users = User.objects.all()

    return render(request,"admin_user_list.html",{"users":users})

def admin_user_detail(request,user_id):

    if not request.user.is_superuser:
        return redirect('dashboard')

    user = User.objects.get(id=user_id)

    expenses = Expense.objects.filter(user=user)

    return render(request,"admin_user_detail.html",{
        "user":user,
        "expenses":expenses
    })


def admin_dashboard(request):

    if not request.user.is_superuser:
        return redirect('dashboard')

    total_users = User.objects.count()

    total_expense = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        "total_users": total_users,
        "total_expense": total_expense
    }

    return render(request,"admin_dashboard.html",context)