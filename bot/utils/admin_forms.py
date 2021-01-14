from django import forms

from bot.models import SNAPIArticle


class SNAPIArticleForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = SNAPIArticle
        fields = '__all__'