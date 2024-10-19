from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import CustomUser, Expense, ExpenseSplit, BalanceSheet
from .serializers import CustomUserSerializer, ExpenseCreateSerializer

class CustomUserTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')  # Assuming this is the name of your register endpoint
        self.user_data = {
            'email': 'test@example.com',
            'name': 'Test User',
            'mobile': '+1234567890',
            'password': 'testpassword'
        }

    def test_create_user(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(CustomUser.objects.get().name, 'Test User')

    def test_create_user_invalid_data(self):
        invalid_data = self.user_data.copy()
        invalid_data['email'] = 'invalid_email'  # Invalid email format
        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CustomUser.objects.count(), 0)


class ExpenseCreateTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.create_expense_url = reverse('expense-create')  # Assuming this is the name of your create expense endpoint
        # Set up necessary data for testing

    def test_create_expense_equal_split(self):
        # Test creating an expense with equal split method
        user = CustomUser.objects.create_user(email='test@example.com', name='Test User', mobile='+1234567890', password='testpassword')
        self.client.force_authenticate(user=user)

        expense_data = {
            'amount': '100.00',
            'title': 'Test Expense',
            'description': 'Test Description',
            'split_method': 'equal'
        }
        response = self.client.post(self.create_expense_url, expense_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 1)
        self.assertEqual(BalanceSheet.objects.count(), CustomUser.objects.count())

    def test_create_expense_exact_split_invalid_data(self):
        # Test creating an expense with exact split method and invalid data
        user = CustomUser.objects.create_user(email='test@example.com', name='Test User', mobile='+1234567890', password='testpassword')
        self.client.force_authenticate(user=user)

        expense_data = {
            'amount': '100.00',
            'title': 'Test Expense',
            'description': 'Test Description',
            'split_method': 'exact',
            'exact_splits': [{'user': user.id, 'split_amount': '50.00'}, {'user': user.id, 'split_amount': '60.00'}]
        }
        response = self.client.post(self.create_expense_url, expense_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_create_expense_percentage_split(self):
        # Test creating an expense with percentage split method
        user1 = CustomUser.objects.create_user(email='user1@example.com', name='User One', mobile='+1234567890', password='testpassword')
        user2 = CustomUser.objects.create_user(email='user2@example.com', name='User Two', mobile='+9876543210', password='testpassword')
        self.client.force_authenticate(user=user1)

        expense_data = {
            'amount': '200.00',
            'title': 'Test Expense',
            'description': 'Test Description',
            'split_method': 'percentage',
            'percentage_splits': [{'user': user1.id, 'percentage': '40.0'}, {'user': user2.id, 'percentage': '60.0'}]
        }
        response = self.client.post(self.create_expense_url, expense_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 1)
        self.assertEqual(BalanceSheet.objects.count(), 2)  # Two users involved

    def test_create_expense_percentage_split_invalid_percentage(self):
        # Test creating an expense with percentage split method and invalid percentages
        user1 = CustomUser.objects.create_user(email='user1@example.com', name='User One', mobile='+1234567890', password='testpassword')
        self.client.force_authenticate(user=user1)

        expense_data = {
            'amount': '200.00',
            'title': 'Test Expense',
            'description': 'Test Description',
            'split_method': 'percentage',
            'percentage_splits': [{'user': user1.id, 'percentage': '30.0'}, {'user': user1.id, 'percentage': '70.0'}]
        }
        response = self.client.post(self.create_expense_url, expense_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_expense_percentage_split_invalid_user(self):
        # Test creating an expense with percentage split method and invalid user
        user1 = CustomUser.objects.create_user(email='user1@example.com', name='User One', mobile='+1234567890', password='testpassword')
        self.client.force_authenticate(user=user1)

        expense_data = {
            'amount': '200.00',
            'title': 'Test Expense',
            'description': 'Test Description',
            'split_method': 'percentage',
            'percentage_splits': [{'user': user1.id, 'percentage': '40.0'}, {'user': 999, 'percentage': '60.0'}]
        }
        response = self.client.post(self.create_expense_url, expense_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_expense_percentage_split_total_percentage_not_100(self):
        # Test creating an expense with percentage split method and total percentage not equal to 100%
        user1 = CustomUser.objects.create_user(email='user1@example.com', name='User One', mobile='+1234567890', password='testpassword')
        user2 = CustomUser.objects.create_user(email='user2@example.com', name='User Two', mobile='+9876543210', password='testpassword')
        self.client.force_authenticate(user=user1)

        expense_data = {
            'amount': '200.00',
            'title': 'Test Expense',
            'description': 'Test Description',
            'split_method': 'percentage',
            'percentage_splits': [{'user': user1.id, 'percentage': '40.0'}, {'user': user2.id, 'percentage': '30.0'}]
        }
        response = self.client.post(self.create_expense_url, expense_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    

