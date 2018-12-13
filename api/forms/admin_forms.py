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
    librarian_notes = forms.CharField(widget=forms.Textarea, required=False)
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
        model = SpacecraftConfiguration
        fields = '__all__'


class AgencyForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Agency
        fields = '__all__'


class AstronautForm(forms.ModelForm):
    bio = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Astronauts
        fields = '__all__'


class SpacecraftForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Spacecraft
        fields = '__all__'


class SpacecraftFlightForm(forms.ModelForm):
    destination = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = SpacecraftFlight
        fields = '__all__'


class SpaceStationForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = SpaceStation
        fields = '__all__'