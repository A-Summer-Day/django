from crispy_forms.layout import Submit
from django import forms
#from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from django.utils.translation import ugettext_lazy as _
from crispy_forms.helper import FormHelper
from .models import User


class UserLoginForm(AuthenticationForm):
    username = UsernameField(
        label='Email Address',
        widget=forms.TextInput(attrs={'autofocus': True})
    )

    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_errors = False

        self.helper.add_input(Submit('submit', 'Login', css_class='btn btn-primary btn-lg px-4 mt-3'))



class UserRegisterForm(UserCreationForm):
    username = forms.EmailField(required=True, label='Email Address', max_length=100, help_text='')


    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        #self.fields['username'].help_text = 'Required. 150 characters or fewer.'

    def save(self, commit=True):
        user = super(UserRegisterForm, self).save(commit=False)
        user.email = self.cleaned_data.get('username')
        if commit:
            print('saved!')
            user.save()
        else:
            print('not saved!')
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'username': 'Username',
            'email': 'Email Address',
            'first_name': 'First Name',
            'last_name': 'Last Name'
        }
