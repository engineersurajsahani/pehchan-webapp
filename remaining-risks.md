# Remaining Risks and Recommendations

**Application**: Pehchan Web Application  
**Assessment Date**: October 13, 2026  
**Auditor**: Senior Django Developer & Security Specialist  

---

## 1. Scope Disclaimer

While all 10 reported source code vulnerabilities have been remediated and verified with automated test suites, software security requires ongoing diligence across deployment environments, operational infrastructure, and third-party dependencies.

---

## 2. Operational & Infrastructure Risks

### 1. Missing Production Email Credentials
* **Risk**: In the local and staging environments, SMTP credentials (`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`) are not set, causing a `RuntimeWarning`. On production, failure to supply these variables will cause password reset OTP dispatch to fail.
* **Recommendation**: Ensure production environment variables on Render / Vercel are configured with valid SMTP credentials.

### 2. HTTPS / SSL Flags in Production Deployment
* **Risk**: During local development with `DEBUG=True`, SSL redirection (`SECURE_SSL_REDIRECT`), `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and `SECURE_HSTS_SECONDS` are disabled by design. If `DEBUG=True` is inadvertently deployed to production, traffic will not enforce HTTPS.
* **Recommendation**: Maintain `DEBUG=False` strictly on production hosting to activate the production security headers already defined in `settings.py`.

### 3. Media File Upload Storage Isolation
* **Risk**: Uploaded receipts are validated for size (5MB max) and extension (`.jpg`, `.jpeg`, `.png`, `.webp`, `.pdf`). However, if files are served directly from local filesystem in server environments without CDN isolation, there is a minor risk of static content abuse.
* **Recommendation**: Maintain Cloudinary media storage (`django-cloudinary-storage`) in production with signed media URLs.

### 4. Continuous Dependency Auditing
* **Risk**: Dependencies such as `Pillow`, `Django`, `requests`, and `openpyxl` frequently receive upstream security patches.
* **Recommendation**: Run automated dependency scanning (e.g., GitHub Dependabot or `pip-audit`) as part of CI/CD pipelines.

---

## 3. Recommended Roadmap

1. **Implement Captcha or IP-based Rate Limiting**: Consider integrating Cloudflare Turnstile or `django-ratelimit` for public-facing contact forms and anonymous donation endpoints to prevent automated spam.
2. **Periodic Access Reviews**: Regularly audit admin users created via `python manage.py create_admin_user` to ensure stale administrative privileges are revoked.
