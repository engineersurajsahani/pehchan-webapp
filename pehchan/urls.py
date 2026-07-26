from django.urls import path
from django.views.decorators.cache import cache_page
from . import views

urlpatterns = [
    # Home and Public Pages
    path('', views.home, name='home'),
    path('about/', cache_page(60 * 15)(views.about), name='about'),
    path('gallery/', cache_page(60 * 15)(views.public_gallery), name='public_gallery'),
    path('events/', cache_page(60 * 15)(views.public_events_list), name='public_events'),
    path('events/<int:pk>/', views.public_event_detail, name='public_event_detail'),
    path('volunteer-info/', views.public_volunteer, name='public_volunteer'),
    path('donate-info/', views.public_donate, name='public_donate'),
    path('verify-certificate/', views.certificate_verify, name='public_certificate_verify'),
    
    # Authentication
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Forgot Password
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    
    # Dashboard (Login Required)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('user-dashboard/', views.user_dashboard_ui, name='user_dashboard_ui'),
    
    # Events (Login Required)
    path('dashboard/events/', views.EventListView.as_view(), name='event_list'),
    path('dashboard/events/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('dashboard/events/<int:pk>/join/', views.join_event, name='join_event'),
    
    # Lifetime Volunteer (Login Required)
    path('volunteer/lifetime/', views.LifetimeVolunteerCreateView.as_view(), name='lifetime_volunteer'),
    
    # Certificates (Login Required)
    path('certificates/', views.CertificateListView.as_view(), name='certificate_list'),
    path('certificates/<int:pk>/', views.certificate_detail, name='certificate_detail'),
    path('dashboard/verify-certificate/', views.certificate_verify, name='certificate_verify'),
    path('certificates/donor/', views.DonorCertificateListView.as_view(), name='donor_certificate_list'),
    path('certificates/donor/<int:pk>/', views.donor_certificate_detail, name='donor_certificate_detail'),
    
    # Donations (Login Required)
    path('donate/material/', views.MaterialDonationCreateView.as_view(), name='material_donation'),
    path('donate/money/', views.MoneyDonationCreateView.as_view(), name='money_donation'),
    
    # Admin Certificate Issuance (Staff Only)
    path('admin/issue-volunteer-certificate/<int:volunteer_id>/', views.issue_volunteer_certificate, name='issue_volunteer_certificate'),
    
    # Temporary fix for admin login
    path('fix-admin-now/', views.fix_admin_view, name='fix_admin'),
]