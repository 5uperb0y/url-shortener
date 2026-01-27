from django import forms

class UrlForm(forms.Form):
    # URLs shorter than 48 characters (our domain length) don't need shortening
    # TODO: domain might change. Besides, 48 chars is too long, but our free domain is what it is.
    # (At least it blocks other URL shortener services)
    url = forms.URLField(
        max_length=2048,
        min_length=48,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': '在這裡輸入你的網址',
        }),
        label='Url to be shorten',
        required=True,
        error_messages={
            'min_length': '網址過短，至少需要 48 個字元。',
            'max_length': '網址過長，應小於 2048 個字元。',
        }
    )