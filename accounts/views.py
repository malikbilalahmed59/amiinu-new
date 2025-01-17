from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import SignupSerializer
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .models import CustomUser
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator as token_generator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

class TokenValidationView(APIView):
    """
    Validates an access or refresh token and checks if it is expired.
    """
    permission_classes = []

    def post(self, request):
        token = request.data.get('token')

        if not token:
            return Response({'verified': False, 'message': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validate the token
            AccessToken(token)  # Use RefreshToken(token) if validating a refresh token
            return Response({'verified': True, 'message': 'Token is valid.'}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({'verified': False, 'message': 'Token is invalid or expired.'}, status=status.HTTP_401_UNAUTHORIZED)

class ForgotPasswordAPIView(APIView):
    permission_classes = []

    def post(self, request):
        identifier = request.data.get('username')

        if not identifier:
            return Response({'message': 'Email or Username is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=identifier) if '@' in identifier else CustomUser.objects.get(username=identifier)
        except CustomUser.DoesNotExist:
            return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not user.is_active:
            return Response({'message': 'User account is inactive.'}, status=status.HTTP_400_BAD_REQUEST)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        reset_link = f"http://{get_current_site(request).domain}{reverse('accounts:reset-password', kwargs={'uidb64': uid, 'token': token})}"

        subject = "Reset Your Password"
        html_message = render_to_string('accounts/reset_password_email.html', {
            'user': user,
            'reset_link': reset_link,
        })
        email = EmailMultiAlternatives(subject, html_message, settings.DEFAULT_FROM_EMAIL, [user.email])
        email.attach_alternative(html_message, "text/html")
        email.send()

        return Response({'message': 'Password reset link has been sent to your email.'}, status=status.HTTP_200_OK)



def reset_password_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        return render(request, 'accounts/reset_password.html', {'error': 'Invalid or expired reset link.'})

    if not token_generator.check_token(user, token):
        return render(request, 'accounts/reset_password.html', {'error': 'Invalid or expired reset link.'})

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not new_password or not confirm_password:
            return render(request, 'accounts/reset_password.html', {'error': 'Both password fields are required.'})

        if new_password != confirm_password:
            return render(request, 'accounts/reset_password.html', {'error': 'Passwords do not match.'})

        user.set_password(new_password)
        user.save()

        return redirect('accounts:reset-password-done')  # Redirect to a success page

    return render(request, 'accounts/reset_password.html')


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'message': 'Email/Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)

        if user:
            if not user.is_active:
                return Response({'message': 'Account is not active. Please verify your email.'}, status=status.HTTP_400_BAD_REQUEST)

            refresh = RefreshToken.for_user(user)
            refresh['username'] = user.username
            refresh['email'] = user.email
            refresh['role'] = user.role

            return Response({
                'message': 'Login successful.',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)

        return Response({'message': 'The email or password you entered is incorrect. Please try again.'}, status=status.HTTP_401_UNAUTHORIZED)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from .serializers import SignupSerializer
from .models import CustomUser
from .tokens import token_generator  # Ensure your token generator is implemented

class SignupView(APIView):
    permission_classes = []

    def post(self, request):
        # Deserialize user data
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            # Save the user
            user = serializer.save()
            user.role = 'normal'
            user.is_active = False
            user.save()

            # Generate email verification link
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            verification_path = reverse('accounts:email-verify', kwargs={'uidb64': uid, 'token': token})
            verification_link = request.build_absolute_uri(verification_path)

            # Generate absolute URLs for static files
            email_logo_url = request.build_absolute_uri(settings.STATIC_URL + "images/email-logo-img.png")
            email_bg_url = request.build_absolute_uri(settings.STATIC_URL + "images/email-bg-img.jpg")

            # Prepare email content
            subject = "Verify Your Email"
            html_message = render_to_string('accounts/verification_email.html', {
                'user': user,
                'verification_link': verification_link,
                'email_logo_url': email_logo_url,
                'email_bg_url': email_bg_url,
            })
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [user.email]

            # Send email
            try:
                email = EmailMultiAlternatives(subject, "", from_email, recipient_list)
                email.attach_alternative(html_message, "text/html")
                email.send()
                return Response(
                    {'message': 'Your account has been created successfully! Please check your email to verify your account.'},
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'message': f'Failed to send email: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # Handle invalid data
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class EmailVerifyView(APIView):
    permission_classes = []

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return HttpResponse('Invalid activation link.', status=400)

        if token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return HttpResponse('Email verified successfully!', status=200)

        return HttpResponse('Invalid or expired token.', status=400)
