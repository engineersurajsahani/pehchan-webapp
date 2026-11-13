import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pehchan_webapp.settings')
django.setup()

from django.contrib.auth.models import User
from pehchan.models import Event, EventVolunteer, LifetimeVolunteer, Certificate
from django.utils import timezone

def populate():
    print("=" * 60)
    print("SEEDING DATABASE: Users, Event (Prarambh), Volunteer & Certificate")
    print("=" * 60)

    # 1. Admin User
    admin_user, created_admin = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@pehchanyui.in', 'is_staff': True, 'is_superuser': True}
    )
    if created_admin:
        admin_user.set_password('AdminSecure2026!')
        admin_user.save()
        print("[+] Admin user 'admin' created.")
    else:
        print("[*] Admin user 'admin' already exists.")

    # 2. Regular User
    regular_user, created_user = User.objects.get_or_create(
        username='rahul_sharma',
        defaults={
            'email': 'rahul.sharma@example.com',
            'first_name': 'Rahul',
            'last_name': 'Sharma',
            'is_staff': False,
            'is_superuser': False
        }
    )
    if created_user:
        regular_user.set_password('UserPehchan2026!')
        regular_user.save()
        print("[+] Regular user 'rahul_sharma' created (Password: UserPehchan2026!).")
    else:
        print("[*] User 'rahul_sharma' already exists.")

    # 3. Volunteer User
    volunteer_user, created_vol = User.objects.get_or_create(
        username='priya_volunteer',
        defaults={
            'email': 'priya.patel@example.com',
            'first_name': 'Priya',
            'last_name': 'Patel',
            'is_staff': False,
            'is_superuser': False
        }
    )
    if created_vol:
        volunteer_user.set_password('VolunteerPehchan2026!')
        volunteer_user.save()
        print("[+] Volunteer user 'priya_volunteer' created (Password: VolunteerPehchan2026!).")
    else:
        print("[*] Volunteer user 'priya_volunteer' already exists.")

    # 4. Event: Prarambh (प्रारंभ)
    # Event starts tomorrow, lasts 3 days, from 10:00 AM to 12:00 PM daily in Navi Mumbai
    event_start_date = date.today() + timedelta(days=1)
    event_description = (
        "Prarambh (प्रारंभ) - An empowering community outreach initiative by Pehchan.\n\n"
        "Schedule: 10:00 AM to 12:00 PM (3-Day Community Drive)\n"
        "Focus Areas:\n"
        "• Educational distribution & stationery kits for underprivileged children\n"
        "• Community learning workshops and fun activities\n"
        "• Warm food and winter essentials distribution\n\n"
        "Join us in Navi Mumbai to make a lasting difference in the lives of these bright young minds!"
    )

    event, created_event = Event.objects.get_or_create(
        name='Prarambh',
        defaults={
            'description': event_description,
            'event_date': event_start_date,
            'location': 'Navi Mumbai, Maharashtra',
            'fundraising_goal': 50000.00,
            'is_active': True,
            'status': 'upcoming',
            'created_by': admin_user
        }
    )
    if created_event:
        print(f"[+] Event 'Prarambh' created for {event_start_date} at Navi Mumbai.")
    else:
        event.description = event_description
        event.location = 'Navi Mumbai, Maharashtra'
        event.event_date = event_start_date
        event.save()
        print("[*] Event 'Prarambh' updated with timing (10:00 AM to 12:00 PM) and Navi Mumbai location.")

    # 5. Connect Volunteer to Event
    vol_entry, created_vol_entry = EventVolunteer.objects.get_or_create(
        user=volunteer_user,
        event=event,
        defaults={
            'contact_number': '9820112233',
            'status': 'approved',
            'attended': True
        }
    )
    if created_vol_entry:
        print(f"[+] Volunteer '{volunteer_user.username}' enrolled and approved for '{event.name}'.")
    else:
        vol_entry.status = 'approved'
        vol_entry.attended = True
        vol_entry.contact_number = '9820112233'
        vol_entry.save()
        print(f"[*] Volunteer '{volunteer_user.username}' record confirmed for '{event.name}'.")

    # Also make Priya a Lifetime Volunteer
    lt_vol, created_lt = LifetimeVolunteer.objects.get_or_create(
        user=volunteer_user,
        defaults={
            'contact_number': '9820112233',
            'motivation': 'Dedicated to empowering underprivileged children through continuous grassroots volunteering.',
            'status': 'approved',
            'reviewed_by': admin_user
        }
    )
    if created_lt:
        print(f"[+] Lifetime volunteer status granted to '{volunteer_user.username}'.")

    # 6. Issue Volunteer Certificate
    cert, created_cert = Certificate.objects.get_or_create(
        certificate_number='VOL-PRARAMBH-2026-001',
        defaults={
            'event': event,
            'volunteer': vol_entry,
            'issue_date': date.today()
        }
    )
    if created_cert:
        print(f"[+] Volunteer Certificate '{cert.certificate_number}' issued to '{volunteer_user.username}'.")
    else:
        print(f"[*] Certificate '{cert.certificate_number}' already exists.")

    print("=" * 60)
    print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == '__main__':
    populate()
