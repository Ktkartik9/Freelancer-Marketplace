from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from .models import CustomUser, Notification
from .models import Profile
from .forms import ProfileForm, RegistrationForm, LoginForm
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.contrib import messages

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, f'Account created successfully for {user.username}! You can now log in.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            # Errors are handled in the template via form.errors
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.is_verified = True
        user.save()
        messages.success(request, 'Thank you for your email confirmation. Now you can login your account.')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid!')
        return redirect('register')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            
            # Find user by email
            user_obj = CustomUser.objects.filter(email=email).first()
            
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.username}!")
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Invalid password.')
            else:
                messages.error(request, 'No account found with this email.')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

from projects.models import Project, Bid, Message

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    featured_projects = Project.objects.all().order_by('-id')[:3]
    return render(request, 'home.html', {'featured_projects': featured_projects})

@login_required
def dashboard(request):
    user = request.user
    context = {}
    
    if user.role == 'client':
        my_projects = Project.objects.filter(client=user).order_by('-id')
        total_projects = my_projects.count()
        active_projects = my_projects.filter(is_assigned=True).count()
        total_bids_received = Bid.objects.filter(project__client=user).count()
        
        context = {
            'projects': my_projects,
            'total_projects': total_projects,
            'active_projects': active_projects,
            'total_bids': total_bids_received,
        }
    else:
        my_bids = Bid.objects.filter(freelancer=user).order_by('-id')
        total_bids = my_bids.count()
        assigned_projects = Project.objects.filter(assigned_to=user)
        total_earnings = sum(p.budget for p in assigned_projects) # Simple calculation
        
        context = {
            'bids': my_bids,
            'total_bids': total_bids,
            'assigned_projects': assigned_projects,
            'total_earnings': total_earnings,
        }
        
    # Calculate profile completion
    profile, _ = Profile.objects.get_or_create(user=user)
    completion = 40 # Base
    if profile.bio: completion += 20
    if profile.skills: completion += 20
    if profile.profile_image: completion += 20
    context['profile_completion'] = completion

    return render(request, 'dashboard.html', context)

@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    return render(request, 'profile.html', {
        'profile': profile
    })


@login_required
def edit_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {'form': form})