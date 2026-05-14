from django import forms
from .models import Project, Bid

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'budget', 'deadline', 'skills_required']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your project...'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Budget in $'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'skills_required': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, Django (comma separated)'}),
        }

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount', 'proposal']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Your bid amount'}),
            'proposal': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Why should we hire you?'}),
        }
