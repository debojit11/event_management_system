# Generated by Django 5.1.3 on 2024-11-15 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0009_remove_ticket_requires_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='razorpay_account_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]