import os
import sys
import django

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pehchan_webapp.settings')

# Initialize Django
try:
    django.setup()
except Exception as e:
    print(f"ERROR: Failed to initialize Django: {e}")
    sys.exit(1)

from django.contrib.auth.models import User

def create_admin():
    # Fetch credentials from environment variables with fallbacks
    username = os.environ.get('ADMIN_USERNAME') or 'admin'
    email = os.environ.get('ADMIN_EMAIL') or 'admin@pehchanyui.in'
    password = os.environ.get('ADMIN_PASSWORD') or 'admin'

    # Security warning for production
    if password == 'admin' and os.environ.get('DEBUG', 'False') == 'False':
        print("WARNING: Using default admin password in production!")
        print("Please set ADMIN_PASSWORD environment variable to a secure password.")

    # Check if the user already exists
    if not User.objects.filter(username=username).exists():
        try:
            print(f"Creating superuser: {username}...")
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            print(f"[*] Superuser '{username}' created successfully!")
            print(f"  Email: {email}")
            print(f"  Login at: /admin/")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to create superuser: {e}")
            return False
    else:
        print(f"[INFO] User '{username}' already exists. Updating privileges and password...")
        user = User.objects.get(username=username)
        user.set_password(password)
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"[*] Superuser '{username}' updated successfully!")
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("Pehchan Admin User Setup")
    print("=" * 60)
    
    try:
        success = create_admin()
        print("=" * 60)
        if success:
            print("[*] Admin setup completed successfully!")
            sys.exit(0)
        else:
            print("[ERROR] Admin setup failed!")
            sys.exit(1)
    except Exception as e:
        print(f"[FATAL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
