from rest_framework import serializers
from .models import CustomUser, Expense, ExpenseSplit, BalanceSheet
from django.contrib.auth import get_user_model
from decimal import Decimal
import re

class CustomUserSerializer(serializers.ModelSerializer):
    
    """
    Serializer for CustomUser model.
    
    """
    
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'mobile', 'password')
        extra_kwargs = {
            'password': {'write_only': True}
        }
        
    def validate_email(self, value):
        """
        Validate email format.
        """
        if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            raise serializers.ValidationError("Invalid email format")
        return value

    def validate_mobile(self, value):
        """
        Validate mobile number format.
        """
        if not re.match(r"^\+?1?\d{9,15}$", value):
            raise serializers.ValidationError("Invalid mobile number format")
        return value
    
    def create(self, validated_data):
        """
        Create a new CustomUser instance.
        """
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            mobile=validated_data['mobile'],
            password=validated_data['password']
        )
        return user
    
    
    
class CustomUserDetailSerializer(serializers.ModelSerializer):
    
    """
    Serializer for detailed representation of CustomUser.
    """
    
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'mobile')
        
        
class CustomUserListSerializer(serializers.ModelSerializer):
    
    """
    Serializer for list representation of CustomUser.
    """
    
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'mobile')
        
        
        
class ExpenseSplitSerializer(serializers.ModelSerializer):
    
    """
    Serializer for ExpenseSplit model.
    """
    
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    percentage = serializers.FloatField(required=False) 
    split_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)  # For exact split method

    class Meta:
        model = ExpenseSplit
        fields = ('user', 'split_amount', 'percentage')  # Include percentage field
        extra_kwargs = {
            'split_amount': {'required': False},  # Make split_amount optional
            'percentage': {'required': False}  # Make percentage optional
        }


class ExpenseCreateSerializer(serializers.ModelSerializer):
    
    """
    Serializer for creating Expense model instance.
    """
    
    splits = ExpenseSplitSerializer(many=True, read_only=True)
    exact_splits = ExpenseSplitSerializer(many=True, write_only=True, required=False)
    percentage_splits = ExpenseSplitSerializer(many=True, write_only=True, required=False)  # For percentage splits

    class Meta:
        model = Expense
        fields = ('amount', 'title', 'description', 'split_method', 'splits', 'exact_splits', 'percentage_splits')
        
    def validate(self, data):
        
        """
        Validate expense creation data based on split_method.
        """
        
        split_method = data.get('split_method')
        exact_splits = data.get('exact_splits', [])
        percentage_splits = data.get('percentage_splits', [])

        if split_method == 'exact':
            if not exact_splits:
                raise serializers.ValidationError("Exact splits are required for 'exact' split method.")
            
            total_split_amount = sum(Decimal(split['split_amount']) for split in exact_splits)
            if total_split_amount != Decimal(data['amount']):
                raise serializers.ValidationError("The total of all exact split amounts must equal the expense amount.")

            user_ids = [split['user'].id for split in exact_splits]
            if len(user_ids) != len(set(user_ids)):
                raise serializers.ValidationError("Duplicate user IDs found in exact splits.")
            
            users_exist = CustomUser.objects.filter(id__in=user_ids).count()
            if users_exist != len(user_ids):
                raise serializers.ValidationError("One or more user IDs are invalid.")

        elif split_method == 'percentage':
            if not percentage_splits:
                raise serializers.ValidationError("Percentage splits are required for 'percentage' split method.")
            
            total_percentage = sum(Decimal(split['percentage']) for split in percentage_splits)
            if total_percentage != Decimal('100.0'):
                raise serializers.ValidationError("The sum of all percentages must equal 100%.")
            
            user_ids = [split['user'].id for split in percentage_splits]
            if len(user_ids) != len(set(user_ids)):
                raise serializers.ValidationError("Duplicate user IDs found in percentage splits.")
            
            users_exist = CustomUser.objects.filter(id__in=user_ids).count()
            if users_exist != len(user_ids):
                raise serializers.ValidationError("One or more user IDs are invalid.")
        
        elif split_method == 'equal' and (exact_splits or percentage_splits):
            raise serializers.ValidationError("Exact or percentage splits should not be provided for 'equal' split method.")
        
        return data

    def create(self, validated_data):
        
        """
        Create an Expense instance and related ExpenseSplit and BalanceSheet entries based on split_method.
        """
        
        owner = self.context['request'].user
        amount = Decimal(validated_data['amount'])
        split_method = validated_data['split_method']
        
        exact_splits_data = validated_data.pop('exact_splits', [])
        percentage_splits_data = validated_data.pop('percentage_splits', [])
        
        # Create the expense with the owner set
        expense = Expense.objects.create(owner=owner, **validated_data)
        
        if split_method == 'equal':
            num_users = CustomUser.objects.count()
            split_amount = amount / Decimal(num_users)
            for user in CustomUser.objects.all():
                # Create ExpenseSplit without specifying owner again
                ExpenseSplit.objects.create(expense=expense, user=user, split_amount=split_amount)
                BalanceSheet.objects.create(
                    user=user,
                    expense=expense,
                    split_amount=split_amount,
                    owner=owner,
                    amount=amount,
                    title=expense.title,
                    description=expense.description
                )
                
        
        elif split_method == 'exact':
            for split_data in exact_splits_data:
                user = split_data['user']
                split_amount = Decimal(split_data['split_amount'])
                
                if not CustomUser.objects.filter(id=user.id).exists():
                    raise serializers.ValidationError(f"User with ID {user.id} does not exist.")
                
                # Create ExpenseSplit without specifying owner again
                ExpenseSplit.objects.create(expense=expense, user=user, split_amount=split_amount)
                BalanceSheet.objects.create(
                    user=user,
                    expense=expense,
                    split_amount=split_amount,
                    owner=owner,
                    amount=amount,
                    title=expense.title,
                    description=expense.description
                )
        
        elif split_method == 'percentage':
            for split_data in percentage_splits_data:
                user = split_data['user']
                percentage = Decimal(split_data['percentage'])
                split_amount = (percentage / Decimal('100.0')) * amount
                
                if not CustomUser.objects.filter(id=user.id).exists():
                    raise serializers.ValidationError(f"User with ID {user.id} does not exist.")
                
                # Create ExpenseSplit without specifying owner again
                ExpenseSplit.objects.create(expense=expense, user=user, split_amount=split_amount)
                BalanceSheet.objects.create(
                    user=user,
                    expense=expense,
                    split_amount=split_amount,
                    owner=owner,
                    amount=amount,
                    title=expense.title,
                    description=expense.description
                )

        return expense
    
class BalanceSheetSerializer(serializers.ModelSerializer):
    
    """
    Serializer for BalanceSheet model.
    """
    
    class Meta:
        model = BalanceSheet
        fields = ('id', 'user', 'expense', 'split_amount', 'owner', 'amount', 'title', 'description')