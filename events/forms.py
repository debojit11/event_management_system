from django import forms
from .models import Event, Ticket
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class EventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = ['name', 'description', 'location', 'start_date', 'end_date', 'speakers']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['event', 'ticket_type', 'price', 'quantity']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')  # Extract the current user
        super().__init__(*args, **kwargs)

        # Filter events by the current user
        self.fields['event'].queryset = Event.objects.filter(organizer=user)


class CustomUserCreationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    password1 = forms.CharField(
        label="Password", 
        widget=forms.PasswordInput, 
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )
    password2 = forms.CharField(
        label="Confirm Password", 
        widget=forms.PasswordInput, 
        min_length=8
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user