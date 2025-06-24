from django import forms
from .models import ProjectUpload, Student, Group

class ProjectUploadForm(forms.ModelForm):
    full_name = forms.CharField(label='ФИО', max_length=255)
    group = forms.ModelChoiceField(queryset=Group.objects.all(), label='Группа')

    class Meta:
        model = ProjectUpload
        fields = ['archive']
        widgets = {
            'archive': forms.ClearableFileInput(attrs={'accept': '.zip,.tar,.tar.gz'})
        } 