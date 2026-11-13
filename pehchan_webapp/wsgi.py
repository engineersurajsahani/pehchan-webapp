import os
import shutil
from pathlib import Path
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pehchan_webapp.settings')

# Auto-initialize SQLite in /tmp for Vercel if no external database is configured
if 'VERCEL' in os.environ and not (os.environ.get('DATABASE_URL') or os.environ.get('SUPABASE_URL')):
    base_dir = Path(__file__).resolve().parent.parent
    db_dev = base_dir / 'db_dev.sqlite3'
    db_tmp = Path('/tmp/db.sqlite3')
    if db_dev.exists() and (not db_tmp.exists() or db_tmp.stat().st_size == 0):
        try:
            shutil.copyfile(db_dev, db_tmp)
        except Exception as e:
            print(f"Error copying SQLite database to /tmp: {e}")

application = get_wsgi_application()
app = application
