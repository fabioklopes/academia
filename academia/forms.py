from django import forms
from .models import Graduacao

class GraduacaoForm(forms.ModelForm):
    class Meta:
        model = Graduacao
        fields = ['aluno', 'faixa', 'grau', 'data_graduacao']
        widgets = {
            'aluno': forms.Select(attrs={'class': 'form-select'}),
            'faixa': forms.Select(attrs={'class': 'form-select'}),
            'grau': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_graduacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
