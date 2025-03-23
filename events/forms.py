from django import forms
from .models import Event, Ticket
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from captcha.fields import CaptchaField

class EventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = ['name', 'description', 'location', 'start_date', 'end_date', 'speakers']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'name': forms.TextInput(attrs={
                'class': 'transparent-textarea',
                'placeholder': 'Enter event name',
                'style': 'background-color: transparent'
            }),
            'description': forms.Textarea(attrs={
                'class': 'transparent-textarea',
                'placeholder': 'Enter event description',
                'style': 'background-color: transparent'
            }),
            'location': forms.TextInput(attrs={
                'class': 'transparent-textarea',
                'placeholder': 'Enter event location',
                'style': 'background-color: transparent'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'transparent-textarea',
                'style': 'background-color: transparent'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'transparent-textarea',
                'style': 'background-color: transparent'
            }),
            'speakers': forms.TextInput(attrs={
                'class': 'transparent-textarea',
                'placeholder': 'Enter speakers (comma-separated)',
                'style': 'background-color: transparent'
            }),
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

        # Apply transparent widget to the 'event' dropdown and other fields
        self.fields['event'].widget.attrs.update({'class': 'transparent-field'})
        self.fields['ticket_type'].widget.attrs.update({'class': 'transparent-field'})
        self.fields['price'].widget.attrs.update({'class': 'transparent-field'})
        self.fields['quantity'].widget.attrs.update({'class': 'transparent-field'})


class CustomUserCreationForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'transparent-textarea',
            'placeholder': 'First Name',
            'style': 'background-color: transparent'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control transparent-textarea',
            'placeholder': 'Last Name',
            'style': 'background-color: transparent'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control transparent-textarea',
            'placeholder': 'Email Address',
            'style': 'background-color: transparent'
        })
    )
    password1 = forms.CharField(
        label="Password", 
        widget=forms.PasswordInput(attrs={
            'class': 'form-control transparent-textarea',
            'placeholder': 'Password',
            'style': 'background-color: transparent'
        }),
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )
    password2 = forms.CharField(
        label="Confirm Password", 
        widget=forms.PasswordInput(attrs={
            'class': 'form-control transparent-textarea',
            'placeholder': 'Confirm Password',
            'style': 'background-color: transparent'
        }),
        min_length=8
    )
    captcha = CaptchaField()

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'transparent-textarea',
                'placeholder': 'Username',
                'style': 'background-color: transparent'
            }),
        }
        help_texts = {
        'username': '',  # Removes the default help text
        }

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
    

class SupportForm(forms.Form):
    from_email = forms.EmailField(label="Your Email", required=True,
                                  widget=forms.EmailInput(attrs={
                                    'class': 'form-control transparent-textarea',
                                    'placeholder': 'Email Address',
                                    'style': 'background-color: transparent'
                                }))
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'rows': 4, 
                'placeholder': 'Describe your issue or question', 
                'class': 'transparent-textarea'
            }
        )
    )
