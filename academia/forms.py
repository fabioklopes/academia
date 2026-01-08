from django import forms
from .models import Graduacao, Item, Pedido, Turma, User
from django.contrib.auth.forms import PasswordResetForm

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="E-mail",
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'})
    )

class SolicitacaoAcessoForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    whatsapp = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    # Adicionado 'required': 'required' para validação do navegador
    birthday = forms.DateField(
        required=True, 
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date', 'required': 'required'})
    )
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)
    photo = forms.ImageField(required=False)
    has_responsible = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    responsible_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    def clean_whatsapp(self):
        whatsapp = self.cleaned_data.get('whatsapp')
        if whatsapp:
            digits_only = ''.join(filter(str.isdigit, whatsapp))
            if len(digits_only) == 11:
                return f"({digits_only[0:2]}) {digits_only[2:7]}-{digits_only[7:]}"
            elif len(digits_only) == 10:
                return f"({digits_only[0:2]}) {digits_only[2:6]}-{digits_only[6:]}"
            else:
                return digits_only
        return whatsapp

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password != password_confirm:
            raise forms.ValidationError("As senhas não coincidem.")

        return cleaned_data

class PerfilEditForm(forms.ModelForm):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    whatsapp = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # Definido explicitamente para forçar required=True, ignorando o blank=True do Model
    birthday = forms.DateField(
        label="Data de Nascimento",
        required=True,
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'})
    )
    
    faixa = forms.ChoiceField(choices=Graduacao.FAIXA_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    grau = forms.IntegerField(min_value=0, max_value=6, required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'whatsapp', 'birthday', 'photo', 'faixa', 'grau']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Se a data de nascimento já estiver preenchida, desabilita o campo
            if self.instance.birthday:
                self.fields['birthday'].disabled = True
                self.fields['birthday'].required = False # Necessário para o Django não reclamar de campo disabled vazio no POST
                self.fields['birthday'].help_text = "A data de nascimento não pode ser alterada após o preenchimento."

        if self.instance and hasattr(self.instance, 'graduacao'):
            self.fields['faixa'].initial = self.instance.graduacao.faixa
            self.fields['grau'].initial = self.instance.graduacao.grau

    def clean_whatsapp(self):
        whatsapp = self.cleaned_data.get('whatsapp')
        if whatsapp:
            digits_only = ''.join(filter(str.isdigit, whatsapp))
            if len(digits_only) == 11:
                return f"({digits_only[0:2]}) {digits_only[2:7]}-{digits_only[7:]}"
            elif len(digits_only) == 10:
                return f"({digits_only[0:2]}) {digits_only[2:6]}-{digits_only[6:]}"
            else:
                return digits_only
        return whatsapp

    def save(self, commit=True):
        user = super().save(commit=False)
        
        if user.is_student():
            graduacao, created = Graduacao.objects.get_or_create(aluno=user)
            
            faixa = self.cleaned_data.get('faixa')
            if faixa:
                graduacao.faixa = faixa
            
            grau = self.cleaned_data.get('grau')
            if grau is not None:
                graduacao.grau = grau
            else:
                graduacao.grau = 0
                
            if commit:
                graduacao.save()
        
        if commit:
            user.save()
            
        return user

class GraduacaoForm(forms.ModelForm):
    class Meta:
        model = Graduacao
        fields = ['aluno', 'faixa', 'grau', 'data_graduacao']
        widgets = {
            'aluno': forms.Select(attrs={'class': 'form-select'}),
            'faixa': forms.Select(attrs={'class': 'form-select'}),
            'grau': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_graduacao': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
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
