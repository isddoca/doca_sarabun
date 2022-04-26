from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_username, user_email, user_field
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.utils import valid_email_or_none
from django.urls import reverse


class MyAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        print(f"GET request dict is {request.GET}")
        return reverse('profile', kwargs={'username': request.user.username})