from django import forms
from .models import Graduacao, Item, Pedido, Turma

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

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['nome', 'tipo', 'valor', 'quantidade']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['item', 'quantidade']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['item'].queryset = Item.objects.filter(quantidade__gt=0)

    def clean_quantidade(self):
        quantidade = self.cleaned_data.get('quantidade')
        item = self.cleaned_data.get('item')

        if item and quantidade and quantidade > item.quantidade:
            raise forms.ValidationError(f"A quantidade solicitada ({quantidade}) excede o estoque disponível ({item.quantidade}).")
        
        if quantidade <= 0:
            raise forms.ValidationError("A quantidade deve ser pelo menos 1.")

        return quantidade

class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = ['nome', 'descricao', 'ativa']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
