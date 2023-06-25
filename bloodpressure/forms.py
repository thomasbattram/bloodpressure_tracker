from django import forms
from .models import BloodPressure

class BloodPressureForm(forms.ModelForm):
    measured_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))

    class Meta:
        model = BloodPressure
        fields = ('systolic', 'diastolic', 'measured_at')
