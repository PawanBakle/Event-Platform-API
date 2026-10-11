from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from datetime import date
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import transaction

from .models import Event,CustomUser

class RegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField(required = True)
    password = serializers.CharField(required = True, write_only = True)

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    username = serializers.EmailField(required = True)
    password = serializers.CharField(required = True, write_only = True)

    def validate(self, attrs):
        username = attrs['username']
        password = attrs['password']
        auth = authenticate(username = username, password = password) # what does auth return?
        if auth is not None:
            attrs['user'] = auth
            return attrs
        raise serializers.ValidationError('Username or Password is not correct')

class EventSerializer(serializers.ModelSerializer):
    # what fields are required to be read-only / write-only / unique here and validation too
    '''
    title = required
    description
    city
    event_datetime 
    capacity
    '''
    title = serializers.CharField(required = True)
    
    class Meta:
        model = Event
        extra_kwargs = {
            'created_at': {'read_only': True},
            'organizer': {'read_only': True},
        }
                # fields
        fields = ['id','title','description','event_datetime','capacity']
        
    def validate_capacity(self, data):
        if data >= 0:
            return data
        raise serializers.ValidationError('Capacity cannot be negative')

    def validate_city_date_time(self,data):
        # format of the data. gotta check if date is today or after  today
        today = date.today()
        if data.date() >= today:
            return data
        raise serializers.ValidationError('Cannot organize events for past date')