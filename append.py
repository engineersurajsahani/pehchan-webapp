with open('pehchan/views.py', 'a') as f:
    f.write('''
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
''')
