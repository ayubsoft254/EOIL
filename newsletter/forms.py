from django import forms


class SubscribeForm(forms.Form):
    name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()
