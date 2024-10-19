from django.shortcuts import render
from rest_framework import generics
from .models import CustomUser, Expense, BalanceSheet
from .serializers import CustomUserSerializer, CustomUserListSerializer, ExpenseCreateSerializer
from rest_framework.permissions import IsAuthenticated,AllowAny
import csv
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .serializers import BalanceSheetSerializer
from django.http import StreamingHttpResponse
from io import StringIO

# Create your views here.

class CreateUserView(generics.CreateAPIView):
    
    """
    API view to create a new CustomUser.
    """
    
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]


class UserListView(generics.ListAPIView):
    
    """
    API view to list all CustomUser instances.
    """
    
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserListSerializer
    permission_classes = [AllowAny]
    
class ExpenseCreateView(generics.CreateAPIView):
    
    """
    API view to create a new Expense instance.
    """
    
    queryset = Expense.objects.all()
    serializer_class = ExpenseCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()
        

class GenerateBalanceSheetCSVView(generics.GenericAPIView):
    
    """
    API view to generate a CSV report of BalanceSheet for the current user.
    """
    
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Filter BalanceSheet by the current user
        balance_sheets = BalanceSheet.objects.filter(user=user)
        
        # Create streaming response with CSV content
        response = StreamingHttpResponse(
            streaming_content=self.generate_csv(balance_sheets),
            content_type='text/csv',
        )
        response['Content-Disposition'] = 'attachment; filename="balance_sheet.csv"'
        
        return response

    def generate_csv(self, balance_sheets):
        # Generator function to yield CSV rows progressively
        pseudo_buffer = StringIO()
        writer = csv.writer(pseudo_buffer)
        
        # Write header row
        writer.writerow(['ID', 'Expense ID', 'Split Amount', 'Owner ID', 'Total Amount', 'Title', 'Description'])
        
        for sheet in balance_sheets:
            expense = sheet.expense
            writer.writerow([
                sheet.id,
                expense.id,
                sheet.split_amount,
                sheet.owner.id,
                sheet.amount,
                expense.title,
                expense.description
            ])
            
            # Yield the content of the buffer
            yield pseudo_buffer.getvalue()
            
            # Reset the buffer
            pseudo_buffer.seek(0)
            pseudo_buffer.truncate(0)


class GenerateOverallBalanceSheetCSVView(generics.GenericAPIView):
    """
    API view to generate a CSV report of the overall BalanceSheet for all users.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Fetch all balance sheets
        balance_sheets = BalanceSheet.objects.all()
        
        # Create streaming response with CSV content
        response = StreamingHttpResponse(
            streaming_content=self.generate_csv(balance_sheets),
            content_type='text/csv',
        )
        response['Content-Disposition'] = 'attachment; filename="overall_balance_sheet.csv"'
        
        return response

    def generate_csv(self, balance_sheets):
        # Generator function to yield CSV rows progressively
        pseudo_buffer = StringIO()
        writer = csv.writer(pseudo_buffer)
        
        # Write header row
        writer.writerow(['ID', 'Expense ID', 'User ID', 'Split Amount', 'Owner ID', 'Total Amount', 'Title', 'Description'])
        
        for sheet in balance_sheets:
            expense = sheet.expense
            writer.writerow([
                sheet.id,
                expense.id,
                sheet.user.id,
                sheet.split_amount,
                sheet.owner.id,
                sheet.amount,
                expense.title,
                expense.description
            ])
            
            # Yield the content of the buffer
            yield pseudo_buffer.getvalue()
            
            # Reset the buffer
            pseudo_buffer.seek(0)
            pseudo_buffer.truncate(0)
    
    
class GetUserByEmailView(APIView):
    permission_classes = [AllowAny]  # Example permission, adjust as needed

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')  # Assuming email is sent as JSON in the request body
        if not email:
            return Response({'error': 'Email field is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
            serializer = CustomUserListSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        

class GetUserExpensesView(generics.ListAPIView):
    serializer_class = ExpenseCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Expense.objects.filter(owner=user)
    
    
class GetAllExpensesView(generics.ListAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseCreateSerializer
    permission_classes = [AllowAny]
    

class GetExpensesByUserView(generics.ListAPIView):
    serializer_class = ExpenseCreateSerializer
    permission_classes = [AllowAny]  # Adjust permission as per your requirement

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Expense.objects.filter(owner_id=user_id)