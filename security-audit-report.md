# Security Audit Report

**Application**: Pehchan Web Application  
**Audit Date**: October 13, 2026  
**Auditor**: Senior Django Developer & Security Specialist  
**Overall Status**: **PASSED (ALL 10 VULNERABILITIES REMEDIATED & VERIFIED)**

---

## 1. Executive Summary

A comprehensive source code review, manual penetration testing, and automated security test suite were conducted on the Pehchan Web Application codebase. Ten distinct vulnerabilities were investigated across authentication, authorization, session management, file uploads, server configuration, and information leakage. 

All identified vulnerabilities have been remediated in the codebase, accompanied by automated regression tests in `pehchan/tests.py`.

---

## 2. Vulnerability Assessment Matrix

| Finding ID | Title | Severity | Affected Component | Status |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | Development Admin Backdoor Endpoint | **High** | `pehchan/urls.py`, `pehchan/views.py` | **FIXED AND VERIFIED** |
| **SEC-02** | User Account Enumeration via Password Reset | **Medium** | `pehchan/views.py` (`forgot_password`) | **FIXED AND VERIFIED** |
| **SEC-03** | Insecure OTP Password Reset State Management | **Medium** | `pehchan/views.py` (`verify_otp`, `reset_password`) | **FIXED AND VERIFIED** |
| **SEC-04** | Disabled Password Complexity Validators | **Medium** | `pehchan_webapp/settings.py`, `pehchan/forms.py` | **FIXED AND VERIFIED** |
| **SEC-05** | Insecure Fallback Production Secret Key | **Medium** | `pehchan_webapp/settings.py` | **FIXED AND VERIFIED** |
| **SEC-06** | Unrestricted Receipt File Uploads | **Medium** | `pehchan/models.py`, `pehchan/forms.py` | **FIXED AND VERIFIED** |
| **SEC-07** | Wildcard Host Header Vulnerability | **Low** | `pehchan_webapp/settings.py` (`ALLOWED_HOSTS`) | **FIXED AND VERIFIED** |
| **SEC-08** | Inadequate Database Exclusion in Gitignore | **Low** | `.gitignore` | **FIXED AND VERIFIED** |
| **SEC-09** | Information Disclosure via Default Error Pages | **Low** | `templates/404.html`, `500.html`, `403.html` | **FIXED AND VERIFIED** |
| **SEC-10** | Obsolete Superuser Scripts with Static Credentials | **Low** | `create_admin.py` | **FIXED AND VERIFIED** |

---

## 3. Deep-Dive Findings and Remediations

### SEC-01: Admin Backdoor Endpoint
* **Vulnerability**: `/fix-admin-now/` was mapped to `fix_admin_view`, which updated or created a superuser with username `admin` and password `admin` upon HTTP GET request.
* **Remediation**:
  * Deleted `/fix-admin-now/` from `pehchan/urls.py`.
  * Removed `fix_admin_view` from `pehchan/views.py`.
  * Preserved the official Django management command `pehchan/management/commands/create_admin_user.py` for deployment workflows.
* **Verification**: `test_sec01_admin_backdoor_removed` confirmed HTTP 404 response.

### SEC-02: Account Enumeration on Password Reset
* **Vulnerability**: Submitting an unregistered email returned `"No user found with this email address."`, allowing automated user enumeration.
* **Remediation**:
  * Harmonized the response to: `"If an account exists with this email address, an OTP has been sent."` for both existing and non-existing accounts.
  * Added 60-second cooldown per session on OTP generation.
* **Verification**: `test_sec02_prevent_account_enumeration` verified identical 302 redirects and messages.

### SEC-03: OTP Password Reset State Management
* **Vulnerability**: The password reset view `/reset-password/` did not verify whether the OTP was actually validated in the current session.
* **Remediation**:
  * Introduced cryptographically secure OTP generation using Python `secrets`.
  * Enforced `otp_verified` session state flag prior to allowing password changes.
  * Added brute-force attempt limits (max 5 incorrect attempts before invalidating OTP).
  * Cleared all reset session state tokens on successful password change.
* **Verification**: `test_sec03_otp_flow_enforcement` and `test_sec03_expired_otp_rejected` passed.

### SEC-04: Password Validation Policy
* **Vulnerability**: `AUTH_PASSWORD_VALIDATORS = []` completely disabled password validation in `settings.py`.
* **Remediation**:
  * Re-enabled standard Django validators (`UserAttributeSimilarityValidator`, `MinimumLengthValidator` [min 8 chars], `CommonPasswordValidator`, `NumericPasswordValidator`).
  * Integrated `validate_password(new_password, user=self.user)` into `ResetPasswordForm.clean_new_password()`.
* **Verification**: `test_sec04_weak_password_rejected_in_reset` confirmed weak passwords (< 8 chars) are rejected.

### SEC-05: Production Secret Key Protection
* **Vulnerability**: `SECRET_KEY` fell back to a publicly known `django-insecure-...` key if omitted from environment variables.
* **Remediation**:
  * Configured `settings.py` to raise `ImproperlyConfigured("SECRET_KEY environment variable is required in production.")` if unset when `DEBUG=False`.
* **Verification**: Confirmed behavior in `settings.py`.

### SEC-06: Donation Receipt Upload Security
* **Vulnerability**: Receipt fields in `MoneyDonation` and `AnonymousDonation` allowed arbitrary file types and unbounded file sizes.
* **Remediation**:
  * Implemented `validate_receipt_file` model validator enforcing maximum file size of **5 MB** and strict file extension whitelist (`.jpg`, `.jpeg`, `.png`, `.webp`, `.pdf`).
  * Generated and applied database migration `0011_alter_anonymousdonation_receipt_and_more.py`.
* **Verification**: `test_sec06_receipt_upload_security` verified rejection of scripts (`.sh`) and files > 5MB.

### SEC-07: Restrict Allowed Hosts
* **Vulnerability**: `ALLOWED_HOSTS = ['*']` was configured when deployed to Vercel, enabling Host header poisoning.
* **Remediation**:
  * Replaced wildcard with explicit domain matching for `.vercel.app`, `.now.sh`, and `$VERCEL_URL`.
* **Verification**: Code inspected in `settings.py`.

### SEC-08: Protect Git Repository
* **Vulnerability**: `.gitignore` only excluded `db.sqlite3`, leaving local database files like `db_dev.sqlite3` exposed to accidental tracking.
* **Remediation**:
  * Broadened pattern to `*.sqlite3` in `.gitignore`. Verified `.env` is untracked.
* **Verification**: `git status` confirms untracked SQLite files are ignored.

### SEC-09: Secure Error Handling
* **Vulnerability**: Absence of custom 404, 500, and 403 error pages risked leaking debug details and server signatures.
* **Remediation**:
  * Created custom branded templates: `templates/404.html`, `templates/500.html`, and `templates/403.html`.
* **Verification**: Confirmed templates adhere to Django template inheritance.

### SEC-10: Remove Obsolete Admin Scripts
* **Vulnerability**: Standalone script `create_admin.py` in repository root contained static default fallback credentials (`admin:admin`).
* **Remediation**:
  * Removed `create_admin.py`.
  * Verified that deployment configuration (`render.yaml`) executes the official `python manage.py create_admin_user` command.
* **Verification**: File deletion confirmed in repository tree.
