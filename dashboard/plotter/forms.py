from django import forms
from .metrics import Metric

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField

class MetricForm(forms.Form):
    checkbox_choices = forms.MultipleChoiceField(
        choices=[(metric.name, metric.value) for metric in Metric], 
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )