from django.shortcuts import render
from django.urls import path
from .views import SignupView, EmailVerifyView, LoginView, ForgotPasswordAPIView, \
    reset_password_view, TokenValidationView

app_name = 'accounts'

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('validate-token/', TokenValidationView.as_view(), name='validate-token'),

    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordAPIView.as_view(), name='forgot-password'),
    path('reset-password/<uidb64>/<token>/', reset_password_view, name='reset-password'),
    path('reset-password-done/', lambda request: render(request, 'accounts/reset_password_done.html'), name='reset-password-done'),

    path('email-verify/<uidb64>/<token>/', EmailVerifyView.as_view(), name='email-verify'),
]
