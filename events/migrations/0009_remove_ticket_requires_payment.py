# Generated by Django 5.1.3 on 2024-11-15 12:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0008_alter_ticket_requires_payment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticket',
            name='requires_payment',
        ),
    ]
