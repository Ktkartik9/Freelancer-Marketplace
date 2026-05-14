from rest_framework.serializers import ModelSerializer
from .models import CustomUser

class CustomUserSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'

class RegisterSerializer(ModelSerializer):  
    class Meta:  
        model = CustomUser  
        fields = '__all__'  
        extra_kwargs = {'password': {'write_only': True}} 
          