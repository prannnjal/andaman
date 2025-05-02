'''
This code defines a custom authentication backend for Django that allows users to log in using their email address instead of the default username. 
'''
from inquiries.models import CustomUser
from django.contrib.auth.backends import ModelBackend   # The default authentication backend that provides basic authentication functionality. By default it authenticates on the basis of username rather than email.

class PhoneBackend(ModelBackend):
    # By default, Django's built-in authentication views pass a parameter called username (not email) to the authenticate method. If you're using Django's default login form, you'll need to either change your form to pass the email as email or adjust the backend to accept username and use that as the email. For example, you might write:
    def authenticate(self, request, email=None, mobile_number=None, password=None, **kwargs):
        #print("=========================> inside authenticate function and username = ", username)
        try:
            if mobile_number:
                user = CustomUser.objects.get(mobile_number=mobile_number)
            elif email:
                user = CustomUser.objects.get(email=email)
                
        except CustomUser.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None