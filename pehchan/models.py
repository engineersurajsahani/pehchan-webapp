from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import EmailValidator, RegexValidator
from decimal import Decimal
from datetime import date


class Event(models.Model):
    """Model for managing events"""
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateField(db_index=True)
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    fundraising_goal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Target amount to raise for this event")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming', db_index=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='events_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-event_date']
    
    def __str__(self):
        return f"{self.name} - {self.event_date}"
    
    def save(self, *args, **kwargs):
        # Automatically update status based on event date
        today = timezone.now().date()
        if self.event_date < today:
            self.status = 'completed'
        elif self.event_date == today:
            self.status = 'ongoing'
        else:
            self.status = 'upcoming'
        super().save(*args, **kwargs)
    
    def get_status_display(self):
        # Return appropriate status considering the date
        today = timezone.now().date()
        if self.event_date < today:
            return 'Completed'
        elif self.event_date == today:
            return 'Ongoing'
        else:
            return 'Upcoming'


class EventVolunteer(models.Model):
    """Model for event-specific volunteers"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
    ]
    
    phone_regex = RegexValidator(
        regex=r'^\d{10}$',
        message="Contact number must be exactly 10 digits."
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_volunteers')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='volunteers')
    contact_number = models.CharField(max_length=10, validators=[phone_regex], default='0000000000')
    joined_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    attended = models.BooleanField(default=False, help_text="Did the volunteer actually attend the event?")
    
    class Meta:
        unique_together = ['user', 'event']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.event.name}"


class LifetimeVolunteer(models.Model):
    """Model for lifetime volunteers"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    phone_regex = RegexValidator(
        regex=r'^\d{10}$',
        message="Contact number must be exactly 10 digits."
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lifetime_volunteer')
    contact_number = models.CharField(max_length=10, validators=[phone_regex], default='0000000000')
    joined_at = models.DateTimeField(auto_now_add=True)
    motivation = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_lifetime_volunteers')
    
    class Meta:
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} - Lifetime Volunteer ({self.get_status_display()})"


class Certificate(models.Model):
    """Model for volunteer certificates"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='certificates')
    volunteer = models.ForeignKey(EventVolunteer, on_delete=models.CASCADE, related_name='certificates')
    certificate_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    issue_date = models.DateField(default=timezone.now, db_index=True)
    file = models.FileField(upload_to='certificates/', blank=True, null=True)
    
    class Meta:
        unique_together = ['event', 'volunteer']
        ordering = ['-issue_date']
    
    def save(self, *args, **kwargs):
        if not self.certificate_number:
            year = timezone.now().year
            prefix = f"PYUI/{year}/V/"
            
            with transaction.atomic():
                # Lock the table/rows conceptually by getting the max in a safe way
                last_cert = Certificate.objects.select_for_update().filter(
                    certificate_number__startswith=prefix
                ).order_by('-certificate_number').first()
                
                if last_cert:
                    try:
                        last_sequence = int(last_cert.certificate_number.split('/')[-1])
                        new_sequence = last_sequence + 1
                    except (ValueError, IndexError):
                        new_sequence = 1
                else:
                    new_sequence = 1
                    
                self.certificate_number = f"{prefix}{new_sequence:04d}"
                
                while Certificate.objects.filter(certificate_number=self.certificate_number).exists():
                    new_sequence += 1
                    self.certificate_number = f"{prefix}{new_sequence:04d}"
                    
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Certificate {self.certificate_number or f'#{self.pk}'} - {self.volunteer.user.username} - {self.event.name}"


class MaterialDonation(models.Model):
    """Model for material donations"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('processed', 'Processed'),
    ]
    
    phone_regex = RegexValidator(
        regex=r'^\d{10}$',
        message="Contact number must be exactly 10 digits."
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='material_donations')
    item_name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    location = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=10, validators=[phone_regex], default='0000000000')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.item_name}"
    
    def get_pickup_message(self):
        if self.location.lower() == 'mumbai':
            return "Pehchan team will pick up your material."
        else:
            return "Please courier your material to our office."


class MoneyDonation(models.Model):
    """Model for money donations"""
    PAYMENT_METHOD_CHOICES = [
        ('upi', 'UPI'),
    ]
    
    STATUS_CHOICES = [
        ('unverified', 'Unverified'),
        ('verified', 'Verified'),
        ('declined', 'Declined'),
    ]
    
    phone_regex = RegexValidator(
        regex=r'^\d{10}$',
        message="Contact number must be exactly 10 digits."
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='money_donations')
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name='money_donations', help_text="Optional: Link this donation to a specific event")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='upi')
    upi_id = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=10, validators=[phone_regex], default='0000000000')
    receipt_upload = models.FileField(upload_to='receipts/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unverified', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - Rs. {self.amount}"


class DonorCertificate(models.Model):
    """Model for donor certificates"""
    DONATION_TYPE_CHOICES = [
        ('material', 'Material Donation'),
        ('money', 'Money Donation'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donor_certificates')
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPE_CHOICES)
    material_donation = models.ForeignKey(
        MaterialDonation, 
        on_delete=models.CASCADE, 
        related_name='certificates',
        blank=True,
        null=True
    )
    money_donation = models.ForeignKey(
        MoneyDonation, 
        on_delete=models.CASCADE, 
        related_name='certificates',
        blank=True,
        null=True
    )
    
    certificate_number = models.CharField(max_length=50, unique=True, editable=False)
    issue_date = models.DateField(default=timezone.now, db_index=True)
    issued_by = models.CharField(max_length=200, default='Pehchan NGO')
    remarks = models.TextField(blank=True, help_text='Additional remarks or appreciation message')
    file = models.FileField(upload_to='donor_certificates/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date', '-created_at']
        verbose_name = 'Donor Certificate'
        verbose_name_plural = 'Donor Certificates'
    
    def save(self, *args, **kwargs):
        if not self.certificate_number:
            year = timezone.now().year
            prefix = f"PYUI/{year}/D/"
            
            with transaction.atomic():
                last_cert = DonorCertificate.objects.select_for_update().filter(
                    certificate_number__startswith=prefix
                ).order_by('-certificate_number').first()
                
                if last_cert:
                    try:
                        last_sequence = int(last_cert.certificate_number.split('/')[-1])
                        new_sequence = last_sequence + 1
                    except (ValueError, IndexError):
                        new_sequence = 1
                else:
                    new_sequence = 1
                    
                self.certificate_number = f"{prefix}{new_sequence:04d}"
                
                while DonorCertificate.objects.filter(certificate_number=self.certificate_number).exists():
                    new_sequence += 1
                    self.certificate_number = f"{prefix}{new_sequence:04d}"
                    
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Certificate {self.certificate_number} - {self.user.username}"
    
    def get_donation_details(self):
        try:
            if self.donation_type == 'material' and self.material_donation:
                return f"{self.material_donation.item_name} (Qty: {self.material_donation.quantity})"
            elif self.donation_type == 'money' and self.money_donation:
                # Using 'Rs.' instead of '₹' to avoid potential UnicodeEncodeError 
                # in environments that don't support UTF-8 encoding.
                return f"Rs. {self.money_donation.amount}"
        except Exception:
            return "Error retrieving details"
        return "N/A"


class AnonymousDonation(models.Model):
    """Model for anonymous donations without login"""
    donor_name = models.CharField(max_length=200, blank=True, null=True)
    donor_email = models.EmailField(blank=True, null=True)
    donor_phone = models.CharField(max_length=20, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    receipt = models.FileField(upload_to='anonymous_donation_receipts/', blank=True, null=True)
    wants_receipt = models.BooleanField(default=False)
    message = models.TextField(blank=True, null=True)
    google_form_submitted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Anonymous Donation'
        verbose_name_plural = 'Anonymous Donations'
    
    def __str__(self):
        donor = self.donor_name if self.donor_name else 'Anonymous'
        return f"{donor} - Rs. {self.amount} - {self.created_at.strftime('%Y-%m-%d')}"


class ContactMessage(models.Model):
    """Model for contact form messages"""
    STATUS_CHOICES = [('new', 'New'), ('read', 'Read'), ('replied', 'Replied'), ('archived', 'Archived')]
    PRIORITY_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')]

    name = models.CharField(max_length=200)
    email = models.EmailField(validators=[EmailValidator()])
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    admin_notes = models.TextField(blank=True, null=True)
    response = models.TextField(blank=True, null=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contact_responses')
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_short_message(self, limit=50):
        """Returns a truncated version of the message for previews"""
        if self.message and len(self.message) > limit:
            return f"{self.message[:limit]}..."
        return self.message


class PasswordResetOTP(models.Model):
    """Model to store OTP for password reset"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at


class PehchanWallet(models.Model):
    """Model for Pehchan Wallet to track organization funds"""
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Pehchan Wallet'
        verbose_name_plural = 'Pehchan Wallet'
    
    def __str__(self):
        return f"Pehchan Wallet - Balance: Rs. {self.balance}"
    
    @classmethod
    def get_wallet(cls):
        wallet, created = cls.objects.get_or_create(id=1)
        return wallet
    
    def deposit(self, amount, description="", transaction_type="donation"):
        """Deposit money to wallet and record transaction"""
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
            
        with transaction.atomic():
            wallet = PehchanWallet.objects.select_for_update().get(id=self.id)
            wallet.balance = wallet.balance + amount
            wallet.save()
            self.balance = wallet.balance
            
            return WalletTransaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type=transaction_type,
                description=description,
                balance_after_transaction=wallet.balance
            )
    
    def withdraw(self, amount, description="", transaction_type="expense"):
        """Withdraw money from wallet and record transaction"""
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
            
        with transaction.atomic():
            wallet = PehchanWallet.objects.select_for_update().get(id=self.id)
            if amount > wallet.balance:
                raise ValueError("Insufficient funds in wallet")
            
            wallet.balance = wallet.balance - amount
            wallet.save()
            self.balance = wallet.balance
            
            return WalletTransaction.objects.create(
                wallet=wallet,
                amount=-amount,
                transaction_type=transaction_type,
                description=description,
                balance_after_transaction=wallet.balance
            )


class WalletTransaction(models.Model):
    """Model to track all wallet transactions"""
    TRANSACTION_TYPES = [('donation', 'Donation'), ('expense', 'Expense'), ('adjustment', 'Adjustment')]
    
    wallet = models.ForeignKey(PehchanWallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    related_donation = models.ForeignKey(MoneyDonation, on_delete=models.SET_NULL, null=True, blank=True)
    related_expense = models.ForeignKey('Expense', on_delete=models.SET_NULL, null=True, blank=True)
    balance_after_transaction = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']


class Expense(models.Model):
    """Model for tracking organization expenses"""
    CATEGORY_CHOICES = [('office', 'Office'), ('travel', 'Travel'), ('salary', 'Salary'), ('marketing', 'Marketing'), ('other', 'Other')]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    receipt = models.FileField(upload_to='expenses/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='expenses_created')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"