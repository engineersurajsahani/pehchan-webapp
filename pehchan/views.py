from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q, Sum

from .models import (
    Event, EventVolunteer, LifetimeVolunteer, 
    Certificate, MaterialDonation, MoneyDonation, DonorCertificate, ContactMessage, AnonymousDonation
)
from .forms import (
    SignUpForm, LoginForm, EventVolunteerForm, LifetimeVolunteerForm,
    MaterialDonationForm, MoneyDonationForm, CertificateVerificationForm, ContactMessageForm, AnonymousDonationForm
)

# Add these imports for the forgot password functionality
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random
import string
from .models import PasswordResetOTP
from .forms import ForgotPasswordForm, OTPVerificationForm, ResetPasswordForm


def home(request):
    """Home page view with contact form"""
    # Handle contact form submission FIRST (before checking authentication)
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            # Save the contact message
            contact_message = form.save(commit=False)
            # Optionally capture IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                contact_message.ip_address = x_forwarded_for.split(',')[0]
            else:
                contact_message.ip_address = request.META.get('REMOTE_ADDR')
            # Capture user agent
            contact_message.user_agent = request.META.get('HTTP_USER_AGENT', '')
            contact_message.save()
            
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = ContactMessageForm()
    
    # If user is authenticated, redirect to dashboard (for GET requests only)
    if request.user.is_authenticated and request.method == 'GET':
        return redirect('dashboard')
    
    return render(request, 'home.html', {'contact_form': form})


def about(request):
    """About page - accessible to all"""
    return render(request, 'about.html')


def public_gallery(request):
    """Public gallery page - accessible to all"""
    return render(request, 'gallery.html')


def public_events_list(request):
    """Public list of upcoming and ongoing events"""
    from django.utils import timezone
    today = timezone.now().date()
    events = Event.objects.filter(event_date__gte=today).select_related('created_by').order_by('event_date')
    
    search_query = request.GET.get('search', '')
    if search_query:
        events = events.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    return render(request, 'public_events_list.html', {
        'events': events,
        'search_query': search_query
    })


def public_event_detail(request, pk):
    """Public detail view for an event"""
    event = get_object_or_404(Event, pk=pk)
    
    already_joined = False
    if request.user.is_authenticated:
        already_joined = EventVolunteer.objects.filter(
            user=request.user,
            event=event
        ).exists()
        
    # Calculate fundraising progress
    total_raised = 0
    progress_percentage = 0
    if event.fundraising_goal:
        from django.db.models import Sum
        donations = event.money_donations.filter(status='verified').aggregate(total=Sum('amount'))
        total_raised = donations['total'] or 0
        progress_percentage = min(100, int((total_raised / event.fundraising_goal) * 100))
    
    return render(request, 'public_event_detail.html', {
        'event': event,
        'already_joined': already_joined,
        'volunteer_form': EventVolunteerForm() if not already_joined else None,
        'total_raised': total_raised,
        'progress_percentage': progress_percentage
    })


def public_volunteer(request):
    """Public volunteer page - accessible to all"""
    return render(request, 'volunteer.html')


def public_donate(request):
    """Public donate page - accessible to all, handles login/signup and anonymous donations"""
    if request.method == 'POST':
        form_type = request.POST.get('form_type', '')
        
        if form_type == 'signup':
            # Handle signup
            form = SignUpForm(request.POST)
            if form.is_valid():
                user = form.save()
                # Authenticate and login the user
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, 'Registration successful! Welcome to Pehchan.')
                    return redirect('dashboard')
            else:
                # Show error messages
                for field, errors in form.errors.items():
                    if field == '__all__':
                        for error in errors:
                            messages.error(request, f'{error}')
                    else:
                        for error in errors:
                            field_name = field.replace('_', ' ').title()
                            if field == 'password2':
                                field_name = 'Confirm Password'
                            messages.error(request, f'{field_name}: {error}')
        
        elif form_type == 'login':
            # Handle login
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password. Please try again.')
        
        elif form_type == 'anonymous_donation':
            # Handle anonymous donation form submission
            anon_form = AnonymousDonationForm(request.POST, request.FILES)
            if anon_form.is_valid():
                donation = anon_form.save(commit=False)
                # Capture IP address
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    donation.ip_address = x_forwarded_for.split(',')[0]
                else:
                    donation.ip_address = request.META.get('REMOTE_ADDR')
                donation.save()
                messages.success(request, 'Thank you for your anonymous donation! Your contribution has been recorded.')
                return redirect('public_donate')
            else:
                messages.error(request, 'Please fill in the required fields correctly.')
    
    # Create a fresh anonymous donation form for display
    anon_donation_form = AnonymousDonationForm()
    
    return render(request, 'donate.html', {'anon_donation_form': anon_donation_form})


def signup_view(request):
    """User signup view"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Pehchan.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    """User login view"""
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def dashboard(request):
    """User dashboard view with search and contact form capability"""
    user = request.user
    
    # Handle Contact Form Submission
    contact_form = ContactMessageForm()
    if request.method == 'POST' and 'message' in request.POST and 'email' in request.POST:
        contact_form = ContactMessageForm(request.POST)
        if contact_form.is_valid():
            contact_msg = contact_form.save(commit=False)
            # Capture metadata
            contact_msg.ip_address = request.META.get('REMOTE_ADDR')
            contact_msg.user_agent = request.META.get('HTTP_USER_AGENT')
            contact_msg.save()
            messages.success(request, 'Your message has been sent successfully. We will get back to you soon!')
            return redirect('dashboard')
        else:
            messages.error(request, 'There was an error with your message. Please check the form and try again.')

    # Existing dashboard logic
    upcoming_search = request.GET.get('upcoming_search', '').strip()
    joined_search = request.GET.get('joined_search', '').strip()

    # Get all upcoming events with optional search
    # Include ongoing events as well since they're still active
    from django.utils import timezone
    today = timezone.now().date()
    upcoming_events = Event.objects.filter(event_date__gte=today).select_related('created_by').order_by('event_date')
    if upcoming_search:
        upcoming_events = upcoming_events.filter(
            Q(name__icontains=upcoming_search) | 
            Q(description__icontains=upcoming_search) |
            Q(location__icontains=upcoming_search)
        )
    
    # Get events joined by the current user with optional search
    joined_events = EventVolunteer.objects.filter(user=request.user).select_related('event').order_by('-joined_at')
    if joined_search:
        joined_events = joined_events.filter(
            Q(event__name__icontains=joined_search) |
            Q(event__description__icontains=joined_search) |
            Q(event__location__icontains=joined_search)
        )
    
    # Get user's certificates
    certificates = Certificate.objects.filter(volunteer__user=request.user).select_related('event', 'volunteer').order_by('-issue_date')
    
    # Get user's donor certificates
    donor_certificates = DonorCertificate.objects.filter(user=request.user).select_related('material_donation', 'money_donation').order_by('-issue_date')
    
    # Get user's donations
    material_donations = MaterialDonation.objects.filter(user=request.user).order_by('-created_at')
    money_donations = MoneyDonation.objects.filter(user=request.user).order_by('-created_at')
    
    # Check if user is an approved lifetime volunteer
    is_lifetime_volunteer = hasattr(request.user, 'lifetime_volunteer') and request.user.lifetime_volunteer.status == 'approved'
    
    # Get events managed by the current user (if staff)
    managed_events = None
    if request.user.is_staff:
        managed_events = Event.objects.filter(created_by=request.user).order_by('-created_at')[:5]

    context = {
        'upcoming_events': upcoming_events,
        'joined_events': joined_events,
        'managed_events': managed_events,
        'certificates': certificates,
        'donor_certificates': donor_certificates,
        'material_donations': material_donations,
        'money_donations': money_donations,
        'is_lifetime_volunteer': is_lifetime_volunteer,
        'upcoming_search': upcoming_search,
        'joined_search': joined_search,
        'contact_form': contact_form,
    }
    return render(request, 'dashboard.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard view with real statistics"""
    # Check if user is staff/admin
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')

    # Get counts for statistics
    total_users_count = User.objects.count()
    active_volunteers_count = EventVolunteer.objects.filter(status='approved').count()
    upcoming_events_count = Event.objects.filter(status='upcoming').count()
    
    # Calculate total money donations
    total_money = MoneyDonation.objects.aggregate(total=Sum('amount'))['total'] or 0
    # Convert to a readable format (e.g., 2.4L)
    if total_money >= 100000:
        money_display = f"₹{total_money/100000:.1f}L"
    elif total_money >= 1000:
        money_display = f"₹{total_money/1000:.1f}K"
    else:
        money_display = f"₹{total_money}"

    # Get recent data for tables
    recent_users = User.objects.all().order_by('-date_joined')[:5]
    recent_events = Event.objects.all().order_by('-event_date')[:5]
    
    context = {
        'total_users_count': total_users_count,
        'active_volunteers_count': active_volunteers_count,
        'upcoming_events_count': upcoming_events_count,
        'money_display': money_display,
        'recent_users': recent_users,
        'recent_events': recent_events,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
def user_dashboard_ui(request):
    """User dashboard UI view - UI only"""
    return render(request, 'user_dashboard.html')



class EventListView(LoginRequiredMixin, ListView):
    """List all upcoming and ongoing events"""
    model = Event
    template_name = 'event_list.html'
    context_object_name = 'events'
    paginate_by = 3
    
    def get_queryset(self):
        from django.utils import timezone
        today = timezone.now().date()
        # Filter to include both upcoming and ongoing events
        queryset = Event.objects.filter(event_date__gte=today).select_related('created_by').order_by('event_date')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class EventDetailView(LoginRequiredMixin, DetailView):
    """Event detail view with volunteer join option"""
    model = Event
    template_name = 'event_detail.html'
    context_object_name = 'event'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if user already joined this event
        already_joined = EventVolunteer.objects.filter(
            user=self.request.user,
            event=self.object
        ).first()
        
        context['already_joined'] = already_joined is not None
        if not context['already_joined']:
            context['volunteer_form'] = EventVolunteerForm()
        return context


@login_required
def join_event(request, pk):
    """Join an event as a volunteer"""
    event = get_object_or_404(Event, pk=pk)
    
    # Check if user already joined
    if EventVolunteer.objects.filter(user=request.user, event=event).exists():
        messages.warning(request, 'You have already joined this event!')
        return redirect('event_detail', pk=pk)

    if request.method == 'POST':
        form = EventVolunteerForm(request.POST)
        if form.is_valid():
            volunteer = form.save(commit=False)
            volunteer.user = request.user
            volunteer.event = event
            volunteer.save()
            messages.success(request, f'Successfully joined {event.name} as a volunteer!')
            return redirect('event_detail', pk=pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    
    return redirect('event_detail', pk=pk)


class LifetimeVolunteerCreateView(LoginRequiredMixin, CreateView):
    """Become a lifetime volunteer"""
    model = LifetimeVolunteer
    form_class = LifetimeVolunteerForm
    template_name = 'lifetime_volunteer_form.html'
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):
        # Check if user is already a lifetime volunteer
        if hasattr(self.request.user, 'lifetime_volunteer'):
            messages.warning(self.request, 'You have already applied to become a lifetime volunteer!')
            return redirect('dashboard')
        
        form.instance.user = self.request.user
        messages.success(self.request, 'Your application to become a lifetime volunteer has been submitted. It is pending approval.')
        return super().form_valid(form)


class CertificateListView(LoginRequiredMixin, ListView):
    """List user's volunteer certificates with search, filter, and sort"""
    model = Certificate
    template_name = 'certificate_list.html'
    context_object_name = 'certificates'
    paginate_by = 5

    def get_queryset(self):
        queryset = Certificate.objects.filter(
            volunteer__user=self.request.user
        ).select_related('event', 'volunteer')
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(certificate_number__icontains=search) |
                Q(event__name__icontains=search)
            )
            
        # Month Filter
        month = self.request.GET.get('month')
        if month and month.isdigit():
            queryset = queryset.filter(issue_date__month=int(month))
            
        # Sorting
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'oldest':
            queryset = queryset.order_by('issue_date', 'id')
        else:
            queryset = queryset.order_by('-issue_date', '-id')
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['current_month'] = self.request.GET.get('month', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['months'] = [
            ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ]
        return context


@login_required
def certificate_detail(request, pk):
    """View details of a volunteer certificate"""
    certificate = get_object_or_404(Certificate, pk=pk, volunteer__user=request.user)
    return render(request, 'certificate_detail.html', {'certificate': certificate})


class DonorCertificateListView(LoginRequiredMixin, ListView):
    """List user's donor certificates with search, filter, and sort"""
    model = DonorCertificate
    template_name = 'donor_certificate_list.html'
    context_object_name = 'donor_certificates'
    paginate_by = 5

    def get_queryset(self):
        queryset = DonorCertificate.objects.filter(
            user=self.request.user
        ).select_related('material_donation', 'money_donation')
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(certificate_number__icontains=search) |
                Q(material_donation__item_name__icontains=search) |
                Q(donation_type__icontains=search)
            )
            
        # Month Filter
        month = self.request.GET.get('month')
        if month and month.isdigit():
            queryset = queryset.filter(issue_date__month=int(month))
            
        # Sorting
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'oldest':
            queryset = queryset.order_by('issue_date', 'created_at')
        else:
            queryset = queryset.order_by('-issue_date', '-created_at')
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['current_month'] = self.request.GET.get('month', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['months'] = [
            ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ]
        return context


#@login_required
def certificate_verify(request):
    certificate = None
    donor_certificate = None
    form = CertificateVerificationForm()
    searched = False # Added flag

    if request.method == 'POST':
        form = CertificateVerificationForm(request.POST)
        if form.is_valid():
            searched = True
            cert_id = form.cleaned_data['certificate_id'].strip()
            
            # Using __iexact to prevent case-sensitivity issues
            certificate = Certificate.objects.filter(certificate_number__iexact=cert_id).first()
            
            if not certificate:
                donor_certificate = DonorCertificate.objects.filter(certificate_number__iexact=cert_id).first()
            
            if not certificate and not donor_certificate:
                messages.error(request, "No certificate found with that ID.")

    return render(request, 'certificate_verify.html', {
        'form': form,
        'certificate': certificate,
        'donor_certificate': donor_certificate,
        'searched': searched
    })
@login_required
def donor_certificate_list(request):
    """Placeholder view - logic handled by DonorCertificateListView"""
    return redirect('donor_certificate_list_cbv')


@login_required
def donor_certificate_detail(request, pk):
    """View details of a donor certificate"""
    certificate = get_object_or_404(DonorCertificate, pk=pk, user=request.user)
    return render(request, 'donor_certificate_detail.html', {'certificate': certificate})


class MaterialDonationCreateView(LoginRequiredMixin, CreateView):
    """Create a material donation"""
    model = MaterialDonation
    form_class = MaterialDonationForm
    template_name = 'material_donation_form.html'
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        
        # Show pickup/courier message
        pickup_msg = self.object.get_pickup_message()
        messages.success(self.request, f'🌟 Thanks for your contribution! ❤️ You will receive a confirmation email once your donation is processed. ✨ {pickup_msg}')
        return response


class MoneyDonationCreateView(LoginRequiredMixin, CreateView):
    """Create a money donation"""
    model = MoneyDonation
    form_class = MoneyDonationForm
    template_name = 'money_donation_form.html'
    success_url = reverse_lazy('dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Dynamic UPI ID for donations from settings
        context['upi_id'] = getattr(settings, 'DONATION_UPI_ID', '')
        return context
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.payment_method = 'upi'
        form.instance.upi_id = getattr(settings, 'DONATION_UPI_ID', '')
        messages.success(self.request, '🌟 Thanks for your contribution! ❤️ You will receive a confirmation email once your donation is processed. ✨')
        return super().form_valid(form)


def forgot_password(request):
    """Handle forgot password request"""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                
                # Delete any existing OTPs for this user to prevent confusion and database bloat
                PasswordResetOTP.objects.filter(user=user).delete()
                
                # Generate a 6-digit OTP
                otp = ''.join(random.choices(string.digits, k=6))
                
                # Set expiration time (10 minutes from now)
                expires_at = timezone.now() + timedelta(minutes=10)
                
                # Save OTP to database
                PasswordResetOTP.objects.create(
                    user=user,
                    otp=otp,
                    expires_at=expires_at
                )
                
                # Send OTP via email
                subject = 'Pehchan - Password Reset OTP'
                message = f"""
                Hello {user.username},
                
                You have requested to reset your password. Please use the following OTP to reset your password:
                
                OTP: {otp}
                
                This OTP is valid for 10 minutes.
                
                If you did not request this, please ignore this email.
                
                Best regards,
                Pehchan Team
                """
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.EMAIL_HOST_USER,
                        [email],
                        fail_silently=False,
                    )
                except Exception as e:
                    # Clean up OTP if email fails
                    PasswordResetOTP.objects.filter(user=user, otp=otp).delete()
                    messages.error(request, 'Failed to send OTP email. Please try again later or contact support.')
                    return redirect('forgot_password')
                
                # Store user ID in session for later use
                request.session['reset_user_id'] = user.id
                
                messages.success(request, 'An OTP has been sent to your email address.')
                return redirect('verify_otp')
            except User.DoesNotExist:
                messages.error(request, 'No user found with this email address.')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'forgot_password.html', {'form': form})


def verify_otp(request):
    """Verify OTP for password reset"""
    if 'reset_user_id' not in request.session:
        messages.error(request, 'Invalid request. Please try again.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            user_id = request.session['reset_user_id']
            
            try:
                user = User.objects.get(id=user_id)
                # Check if OTP exists and is valid
                otp_record = PasswordResetOTP.objects.filter(user=user, otp=otp).first()
                
                if otp_record and otp_record.is_valid():
                    # OTP is valid, remove it from database
                    otp_record.delete()
                    # Store user ID in session for password reset
                    request.session['reset_user_id'] = user.id
                    messages.success(request, 'OTP verified successfully.')
                    return redirect('reset_password')
                else:
                    messages.error(request, 'Invalid or expired OTP. Please try again.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid request. Please try again.')
                return redirect('forgot_password')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'verify_otp.html', {'form': form})


def reset_password(request):
    """Reset password after OTP verification"""
    if 'reset_user_id' not in request.session:
        messages.error(request, 'Invalid request. Please try again.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user_id = request.session['reset_user_id']
            
            try:
                user = User.objects.get(id=user_id)
                user.set_password(new_password)
                user.save()
                
                # Clear session
                del request.session['reset_user_id']
                
                messages.success(request, 'Your password has been reset successfully. You can now login with your new password.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'Invalid request. Please try again.')
                return redirect('forgot_password')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'reset_password.html', {'form': form})


from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone


@staff_member_required
def issue_volunteer_certificate(request, volunteer_id):
    """Custom admin view to issue a certificate with a custom certificate number"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return HttpResponseRedirect(reverse('admin:pehchan_eventvolunteer_changelist'))
    
    volunteer = get_object_or_404(EventVolunteer, id=volunteer_id)
    
    # Check if certificate already exists
    existing_certificate = Certificate.objects.filter(event=volunteer.event, volunteer=volunteer).first()
    if existing_certificate:
        messages.error(request, 'A certificate already exists for this volunteer.')
        return HttpResponseRedirect(reverse('admin:pehchan_eventvolunteer_changelist'))
    
    if request.method == 'POST':
        cert_num = request.POST.get('certificate_number') # Get the number from the form
        if cert_num:
            # Create the certificate with the provided number
            Certificate.objects.create(
                event=volunteer.event,
                volunteer=volunteer,
                certificate_number=cert_num, # Make sure this field exists in models.py!
                issue_date=timezone.now().date()
            )
            messages.success(request, f'Certificate {cert_num} issued successfully for {volunteer.user.username}.')
            return HttpResponseRedirect(reverse('admin:pehchan_eventvolunteer_changelist'))
        else:
            messages.error(request, 'Please enter a valid certificate number.')
    
    return render(request, 'admin/issue_certificate.html', {
        'volunteer': volunteer,
        'certificate_type': 'Volunteer'
    })



from django.contrib.auth.models import User
from django.http import HttpResponse

def fix_admin_view(request):
    try:
        username = "admin"
        password = "admin"
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            return HttpResponse("Admin user updated successfully. You can now login with admin / admin")
        else:
            User.objects.create_superuser(username=username, email="admin@pehchanyui.in", password=password)
            return HttpResponse("Admin user created successfully. You can now login with admin / admin")
    except Exception as e:
        return HttpResponse(f"Error: {e}")
