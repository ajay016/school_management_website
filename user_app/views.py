from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


def login_view(request):
    """
    Website login page.
    - Admin (type 0/1) and Staff (type 2) are redirected to the dashboard.
    - Other authenticated user types are redirected to the home page.
    """
    if request.user.is_authenticated:
        if request.user.user_type in (0, 1, 2):
            return redirect('/dashboard/')
        return redirect('/')

    error = None
    email_val = ''
    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        email_val = request.POST.get('email', '').strip()
        password  = request.POST.get('password', '')
        next_url  = request.POST.get('next', '').strip()

        if not email_val or not password:
            error = 'Please enter both your email address and password.'
        else:
            # USERNAME_FIELD is 'email', so pass email as 'username' to authenticate()
            user = authenticate(request, username=email_val, password=password)
            if user is not None and user.is_active:
                login(request, user)
                if user.user_type in (0, 1, 2):
                    # Honour ?next= but only if it points into the dashboard
                    dest = next_url if (next_url and next_url.startswith('/dashboard/')) else '/dashboard/'
                    return redirect(dest)
                return redirect(next_url or '/')
            else:
                error = 'Invalid email or password. Please try again.'

    return render(request, 'school/auth/login.html', {
        'error':     error,
        'email_val': email_val,
        'next':      next_url,
    })


def logout_view(request):
    """Log the user out and return to the home page."""
    logout(request)
    return redirect('/')
