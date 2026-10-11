from django.shortcuts import render
from django.contrib.auth import login
from .serializers import EventSerializer,RegistrationSerializer,LoginSerializer
from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.viewsets import ModelViewSet

# Create your views here.

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    def post(self, request):
        serializer = RegistrationSerializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response({'message': 'user created'}, status=status.HTTP_201_CREATED)

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    '''
    where does the authentication land? in serializer or in view
    '''
    def post(self, request):
        serializer = LoginSerializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response(status=status.HTTP_200_OK)

class Events(ModelViewSet):
    '''
    so here since it's a post data. and i have to assign the server-owned field back to 
    the user. gotta over-ride the perform-create. 
    serializeration is handled here.
    '''
    serializer_class = EventSerializer
    def perform_create(self, serializer):
        # how to access organizer here? 
        # get the specific event. since it's a post but event has not been created yet. 
        serializer.save(organizer = self.request.user) # do i need to send other data as well? nope. 


    '''
    so i have provided serializer class
    obj is created - 
    it goes directly to the post method i.e create method
    it uses the serializer i have provided - 
    it then proceeds to create but since i have over-ridden perform create 


    what does perform create do? what i usually do in create in serializer. create the model. 
    but i create directly using model. since serializer already has model. 
    '''