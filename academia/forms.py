from django import forms
from .models import Graduacao, Item, Pedido, Turma, User, Meta as MetaModel, SolicitacaoAlteracaoGraduacao
from django.contrib.auth.forms import PasswordResetForm
import datetime

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
    whatsapp = forms.CharField(required=True, max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    birthday = forms.DateField(
        required=True, 
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date', 'required': 'required'})
    )
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)
    photo = forms.ImageField(required=True)
    has_responsible = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    responsible_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If this is a POST request and 'has_responsible' is checked,
        # make password fields not required.
        if 'data' in kwargs and kwargs['data'].get('has_responsible'):
            self.fields['password'].required = False
            self.fields['password_confirm'].required = False

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
        has_responsible = cleaned_data.get("has_responsible")
        
        # Only validate password confirmation if it's not a dependent registration
        if not has_responsible:
            password = cleaned_data.get("password")
            password_confirm = cleaned_data.get("password_confirm")

            if password and password_confirm and password != password_confirm:
                raise forms.ValidationError("As senhas não coincidem.")

        return cleaned_data

class PerfilEditForm(forms.ModelForm):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    whatsapp = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
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
            if self.instance.birthday:
                self.fields['birthday'].disabled = True
                self.fields['birthday'].required = False
                self.fields['birthday'].help_text = "A data de nascimento não pode ser alterada após o preenchimento."

        if self.instance and hasattr(self.instance, 'graduacoes') and self.instance.graduacoes.exists():
            graduacao = self.instance.graduacoes.first()
            self.fields['faixa'].initial = graduacao.faixa
            self.fields['grau'].initial = graduacao.grau

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
        
        if commit:
            user.save()

        if user.is_student():
            faixa = self.cleaned_data.get('faixa')
            grau = self.cleaned_data.get('grau')
            
            # Verifica se já existe graduação
            graduacao = user.graduacoes.first()
            
            if graduacao:
                # Atualiza existente
                if faixa:
                    graduacao.faixa = faixa
                if grau is not None:
                    graduacao.grau = grau
                if commit:
                    graduacao.save()
            else:
                # Cria nova apenas se tivermos dados mínimos ou definimos defaults
                # Como o banco exige não nulo, precisamos de valores.
                # Se o usuário não preencheu no form, usamos defaults.
                if commit:
                    Graduacao.objects.create(
                        aluno=user,
                        faixa=faixa if faixa else 'WHITE',
                        grau=grau if grau is not None else 0,
                        data_graduacao=datetime.date.today()
                    )
            
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

class SolicitacaoAlteracaoGraduacaoForm(forms.ModelForm):
    class Meta:
        model = SolicitacaoAlteracaoGraduacao
        fields = ['nova_data', 'motivo_solicitacao']
        widgets = {
            'nova_data': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'motivo_solicitacao': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '50'}),
        }

class AlunoNovaGraduacaoForm(forms.ModelForm):
    class Meta:
        model = Graduacao
        fields = ['faixa', 'grau', 'data_graduacao']
        widgets = {
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

class MetaForm(forms.ModelForm):
    class Meta:
        model = MetaModel
        fields = ['titulo', 'data_inicio', 'data_fim', 'meta_aulas', 'minimo_aulas', 'minimo_frequencia']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'meta_aulas': forms.NumberInput(attrs={'class': 'form-control'}),
            'minimo_aulas': forms.NumberInput(attrs={'class': 'form-control'}),
            'minimo_frequencia': forms.NumberInput(attrs={'class': 'form-control'}),
        }
