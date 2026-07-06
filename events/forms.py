from django import forms

from .models import Registration

INPUT_CLASSES = (
    'w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-slate-900 '
    'placeholder-slate-400 focus:border-emerald-600 focus:outline-none focus:ring-2 '
    'focus:ring-emerald-600/20'
)


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['full_name', 'email', 'phone', 'organization', 'category']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Jane Mwakio'}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'you@example.com'}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': '+254 7XX XXX XXX'}),
            'organization': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Taita Taveta University'}),
            'category': forms.Select(attrs={'class': INPUT_CLASSES}),
        }
