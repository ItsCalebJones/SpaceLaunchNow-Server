from django import forms
from api.models import *


class LaunchForm(forms.ModelForm):
    holdreason = forms.CharField(widget=forms.Textarea, required=False)
    failreason = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = Launch
        fields = '__all__'


class LandingForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Landing
        fields = '__all__'


class LauncherForm(forms.ModelForm):
    details = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Launcher
        fields = '__all__'


class PayloadForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Payload
        fields = '__all__'


class MissionForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Mission
        fields = '__all__'


class MissionForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Mission
        fields = '__all__'


class EventsForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Events
        fields = '__all__'


class LauncherConfigForm(forms.ModelForm):
    librarian_notes = forms.CharField(widget=forms.Textarea)
    description = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = LauncherConfig
        fields = '__all__'


class OrbiterForm(forms.ModelForm):
    history = forms.CharField(widget=forms.Textarea)
    details = forms.CharField(widget=forms.Textarea)
    capability = forms.CharField(widget=forms.Textarea)
    flight_life = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = OrbiterConfiguration
        fields = '__all__'


class AgencyForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Agency
        fields = '__all__'
