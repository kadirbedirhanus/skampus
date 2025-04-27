from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, University, SubGoalUserRating


# Kayıt formu
class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Ad")
    last_name = forms.CharField(max_length=30, required=True, label="Soyad")
    email = forms.EmailField(required=True, label="E-posta")
    university = forms.ModelChoiceField(
        queryset=University.objects.all(),
        required=True,
        label="Üniversite"
    )

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'university', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email  # Email'i username olarak kullan
        if commit:
            user.save()
        return user


from django.core.validators import FileExtensionValidator


class SubGoalUserRatingForm(forms.ModelForm):
    class Meta:
        model = SubGoalUserRating
        fields = ['rating', 'pdf_upload']

    def __init__(self, *args, **kwargs):
        subgoal = kwargs.pop('subgoal', None)
        super().__init__(*args, **kwargs)

        if subgoal and subgoal.is_numeric:
            self.fields['rating'] = forms.IntegerField(
                label='Puanınızı girin:',
                min_value=0,
                required=True,
                widget=forms.NumberInput(attrs={'class': 'numeric-input'})
            )
        else:
            self.fields['rating'] = forms.ChoiceField(
                widget=forms.RadioSelect,
                choices=[(option.value, option.name) for option in subgoal.options.all()]
            )

        # Kanıt gerektiren alt hedefler için PDF yükleme alanını ekle
        if subgoal and subgoal.requires_proof:
            self.fields['pdf_upload'] = forms.FileField(
                required=True,
                label='Kanıt PDF Yükleyin:',
                validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
            )

        else:
            # Eğer PDF gerekmediyse, formda PDF alanını gizleyebiliriz
            self.fields['pdf_upload'].required = False
