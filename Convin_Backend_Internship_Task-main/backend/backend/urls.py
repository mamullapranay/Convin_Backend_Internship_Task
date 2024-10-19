from django.urls import path, include
from api.views import CreateUserView, UserListView, ExpenseCreateView, GenerateBalanceSheetCSVView, GetUserByEmailView, GetUserExpensesView, GetAllExpensesView, GetExpensesByUserView, GenerateOverallBalanceSheetCSVView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('api/user/register/', CreateUserView.as_view(), name="register"),
    path('api/token/', TokenObtainPairView.as_view(), name="get_token"),
    path('api/token/refresh/', TokenRefreshView.as_view(), name="refresh"),
    path('api-auth/', include("rest_framework.urls")),
    path('api/users/', UserListView.as_view(), name='user-list'),
    path('api/user/getbyemail/', GetUserByEmailView.as_view(), name='get-user-by-email'),
    path('api/create-expense/', ExpenseCreateView.as_view(), name='expense-create'),
    path('api/user/current-user-expenses/', GetUserExpensesView.as_view(), name='get-user-expenses'),
    path('api/get-all-expenses/', GetAllExpensesView.as_view(), name='get-all-expenses'),
    path('api/user/<int:user_id>/expenses/', GetExpensesByUserView.as_view(), name='get-expenses-by-user'),
    path('api/balance-sheet/', GenerateBalanceSheetCSVView.as_view(), name='balance-sheet-csv'),
    path('api/overall-balance-sheet/', GenerateOverallBalanceSheetCSVView.as_view(), name='overall-balance-sheet-csv'),
]
