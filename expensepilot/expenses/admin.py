
from django.contrib import admin
from .models import Expense

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'amount', 'date')
    list_filter = ('date', 'user')
    search_fields = ('title', 'description', 'user__username')
