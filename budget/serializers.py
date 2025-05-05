from rest_framework import serializers
from .models import Category,MonthlyBudget,Transaction

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class MonthlyBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyBudget
        fields = ['id', 'user', 'month', 'total_budget_amount', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_month(self, value):
        """Validate month format (YYYY-MM)"""
        import re
        if not re.match(r'^\d{4}-\d{2}$', value):
            raise serializers.ValidationError("Month must be in format YYYY-MM")
        return value
    
    def create(self, validated_data):
        """Set user to current user if not provided"""
        if 'user' not in validated_data:
            validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'type', 'amount', 'category', 'category_name', 'date', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'category_name']
    
    def get_category_name(self, obj):
        if obj.category:
            return obj.category.name
        return None
    
    def validate_type(self, value):
        """Validate type is either 'Income' or 'Expense'"""
        if value not in [Transaction.INCOME, Transaction.EXPENSE]:
            raise serializers.ValidationError("Type must be either 'Income' or 'Expense'")
        return value
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value
    
    def create(self, validated_data):
        """Set user to current user if not provided"""
        if 'user' not in validated_data:
            validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TransactionDetailSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'type', 'amount', 'category', 'category_detail', 'date', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'category_detail']
