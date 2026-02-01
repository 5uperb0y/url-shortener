from django import forms


class UrlForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    url = forms.URLField(
        max_length=2048,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': '在這裡輸入你的網址',
        }),
        label='Url to be shorten',
        required=True,
        error_messages={
            'max_length': '網址過長，應小於 2048 個字元。',
        }
    )

    def clean_url(self):
        url = self.cleaned_data['url']
        
        if self.request:
            from urllib.parse import urlparse

            # avoid shortening host
            # 127.0.0.1:8000 -> 127.0.0.1
            # https://mydomain.com/qweu -> mydomain.com
            current_host = self.request.get_host().split(':')[0].lower()
            url_domain = urlparse(url).netloc.split(':')[0].lower()
            
            if current_host == url_domain:
                raise forms.ValidationError('請嘗試縮短它站網址')
        
        return url