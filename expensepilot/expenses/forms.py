from django import forms
from .models import Expense
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Income

class ExpenseForm(forms.ModelForm):

    income_for_month = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label="Income for this Month (if not set)"
    )

    class Meta:
        model = Expense
        fields = ['title', 'amount', 'description', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }

class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['source', 'amount', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }