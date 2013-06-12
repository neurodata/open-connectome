from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm
from models import ocpProject


class CreateProjectForm(ModelForm):
#    token = forms.CharField(label=(u'Token'))
#    host = forms.CharField(label=(u'Host'))
#    project = forms.CharField(label=(u'Project'))
#    dataset = forms.CharField(label=(u'Dataset'))
#    dataurl = forms.CharField(initial='http://',label=(u'Data url'))
#    resolution = forms.IntegerField(label=(u'Resolution') ,error_messages=\
#{
#        "required": "This value cannot be empty.",
#        "invalid": "Please enter a valid Resolution",
#    })
#    readonly = forms.ChoiceField(choices=[(x, x) for x in range(0, 2)])
#    exceptions = forms.ChoiceField(choices=[(x, x) for x in range(0, 2)])
    class Meta:
        model = ocpProject
        def clean_project(self):
            if 'project' in self.cleaned_data:
                project = self.cleaned_data['project']
                return project
            raise forms.ValidationError('Please enter a valid project')
        
class UpdateProjectForm(forms.Form):
    currentToken = forms.CharField(label=(u' Current Token'), widget = forms.TextInput(attrs={'readonly':'readonly'}))
    newToken = forms.CharField(label=(u' New Token'))
#    host = forms.CharField(label=(u'Host'))
#    project = forms.CharField(label=(u'Project'))
#    dataset = forms.CharField(label=(u'Dataset'))
#    dataurl = forms.CharField(initial='http://',label=(u'Data url'))
#    resolution = forms.IntegerField(label=(u'Resolution') ,error_messages=\
#{
#        "required": "This value cannot be empty.",
#        "invalid": "Please enter a valid Resolution",
#    })
#    readonly = forms.ChoiceField(choices=[(x, x) for x in range(0, 2)])
#    exceptions = forms.ChoiceField(choices=[(x, x) for x in range(0, 2)])
