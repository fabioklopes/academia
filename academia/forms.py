from django import forms
from .models import Item, Pedido, Turma, User, Meta as MetaModel, Graduation
from django.contrib.auth.forms import PasswordResetForm
import datetime

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="E-mail",
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'})
    )

    def get_users(self, email):
        """
        Override to handle cases where an email is shared by a responsible user
        and their dependents. In such cases, only send the reset link to the
        responsible user.
        """
        email_field_name = User.get_email_field_name()
        active_users = User._default_manager.filter(**{
            '%s__iexact' % email_field_name: email,
            'status': 'ATIVO',
        })
        
        users_list = list(active_users)

        # If more than one user shares this email, it's likely a responsible
        # user and their dependents. We should only target the responsible user.
        if len(users_list) > 1:
            # A responsible user is one who is not a dependent of anyone,
            # i.e., their `responsible` field is None.
            responsible_users = [u for u in users_list if u.responsible is None]
            return responsible_users
        
        # If only one user was found, return them in a list.
        return users_list

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
    
    belt = forms.ChoiceField(
        choices=Graduation.BELT_CHOICES,
        required=False,
        label="Faixa",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    degree = forms.IntegerField(
        required=False,
        label="Grau",
        min_value=0,
        max_value=6,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

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

    training_start_date = forms.DateField(
        label="Início dos Treinos",
        required=True,
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'})
    )
    
    belt = forms.ChoiceField(
        choices=Graduation.BELT_CHOICES,
        required=False,
        label="Faixa",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    degree = forms.IntegerField(
        required=False,
        label="Grau",
        min_value=0,
        max_value=6,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'whatsapp', 'birthday', 'training_start_date', 'photo']
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
            
            # Populate belt and degree from user model
            self.fields['belt'].initial = self.instance.actual_belt
            self.fields['degree'].initial = self.instance.actual_degree

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
        super().clean()
        belt = self.cleaned_data.get('belt')
        degree = self.cleaned_data.get('degree')
        
        if belt and degree is not None:
            if belt != 'BLACK' and degree > 4:
                self.add_error('degree', "Para faixas coloridas, o grau máximo é 4.")
            elif belt == 'BLACK' and degree > 6:
                self.add_error('degree', "Para a faixa preta, o grau máximo é 6.")
        
        return self.cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        
        belt = self.cleaned_data.get('belt')
        degree = self.cleaned_data.get('degree')
        
        if belt and degree is not None:
            # Check if graduation changed
            if user.actual_belt != belt or user.actual_degree != degree:
                user.actual_belt = belt
                user.actual_degree = degree
                
                # Create history record
                graduation_date = datetime.date.today()
                if user.birthday and graduation_date < user.birthday:
                    graduation_date = user.birthday
                
                Graduation.objects.create(
                    student=user,
                    belt=belt,
                    degree=degree,
                    date=graduation_date
                )
            
        if commit:
            user.save()
            
        return user

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
