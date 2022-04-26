from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_username, user_email, user_field
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.utils import valid_email_or_none
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        username = data.get("username")
        email = data.get("email")
        name = data.get("name")
        user = sociallogin.user
        user_username(user, username or "")
        user_email(user, valid_email_or_none(email) or "")
        user_field(user, "first_name", "")
        user_field(user, "last_name", "")
        return user


