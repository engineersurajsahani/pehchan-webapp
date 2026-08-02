from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import MoneyDonation, Expense, PehchanWallet, Certificate, DonorCertificate
from django.core.mail import EmailMessage


@receiver(post_save, sender=MoneyDonation)
def handle_donation_wallet_transaction(sender, instance, created, **kwargs):
    """Automatically deposit money to wallet when a money donation is made"""
    if created:
        wallet = PehchanWallet.get_wallet()
        wallet.deposit(
            amount=instance.amount,
            description=f"Donation from {instance.user.get_full_name() or instance.user.username}",
            transaction_type="donation"
        )


@receiver(post_save, sender=Expense)
def handle_expense_wallet_transaction(sender, instance, created, **kwargs):
    """Automatically withdraw money from wallet when an expense is created"""
    if created:
        wallet = PehchanWallet.get_wallet()
        wallet.withdraw(
            amount=instance.amount,
            description=f"Expense: {instance.title}",
            transaction_type="expense"
        )


@receiver(post_save, sender=Certificate)
def email_volunteer_certificate(sender, instance, created, **kwargs):
    """Email the volunteer when their certificate is issued"""
    if created and instance.volunteer.user.email:
        subject = f"Your Volunteer Certificate - {instance.event.name}"
        body = f"Hello {instance.volunteer.user.username},\n\nThank you for volunteering at '{instance.event.name}'.\nYour certificate is attached below."
        email = EmailMessage(
            subject=subject,
            body=body,
            to=[instance.volunteer.user.email]
        )
        if instance.file:
            email.attach_file(instance.file.path)
        
        try:
            email.send(fail_silently=True)
        except Exception as e:
            print(f"Certificate email failed: {e}")


@receiver(post_save, sender=DonorCertificate)
def email_donor_certificate(sender, instance, created, **kwargs):
    """Email the donor when their certificate is issued"""
    if created and instance.user.email:
        subject = "Thank You for Your Donation - Pehchan NGO"
        body = f"Hello {instance.user.username},\n\nThank you for your generous donation.\nYour donor certificate is attached."
        email = EmailMessage(
            subject=subject,
            body=body,
            to=[instance.user.email]
        )
        if instance.file:
            email.attach_file(instance.file.path)
        
        try:
            email.send(fail_silently=True)
        except Exception as e:
            print(f"Donor certificate email failed: {e}")