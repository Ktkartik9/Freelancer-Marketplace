from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import CustomUser
from .serializer import CustomUserSerializer
from rest_framework import status


@api_view(['POST'])
def register(request):
    serializer = CustomUserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  

@api_view(['POST'])
def login_view(request):
    serializer = CustomUserSerializer(data=request.data)
    if password := request.data.get('password'):
        if serializer.is_valid():
            user = CustomUser.objects.filter(username=serializer.validated_data['username']).first()
            if user and user.check_password(password):
                return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout_view(request):
    # Implement logout logic if using token-based authentication
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)