from django.shortcuts import render
from django.contrib.auth import login
from .serializers import EventSerializer,RegistrationSerializer,LoginSerializer,ReservationSerializer,EventAttendees
from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny,IsAuthenticated
from .permissions import IsOwnerOrReadOnly
# Create your views here.
from .models import Event,Reservation
from rest_framework.authentication import SessionAuthentication
from django.db import transaction
from rest_framework.decorators import action

from rest_framework import permissions

# class IsOwnerOrReadOnly(permissions.BasePermission):
#     """
#     Custom permission to only allow owners of an object to edit it.
#     """
#     def has_object_permission(self, request, view, obj):
#         # Read permissions are allowed to any request
#         if request.method in permissions.SAFE_METHODS:
#             return True

#         # Write permissions are only allowed to the owner of the object
#         return obj.owner == request.user   

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
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
    permission_classes = [AllowAny]
    authentication_classes = []
    def post(self, request):
        serializer = LoginSerializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        user = serializer.validated_data['user']
        login(request, user)
        username = self.request.user
        return Response({'message': f'{username} user is logged in'},status=status.HTTP_200_OK)
@method_decorator(csrf_exempt, name='dispatch')
class Events(ModelViewSet):
    
    '''
    so here since it's a post data. and i have to assign the server-owned field back to 
    the user. gotta over-ride the perform-create. 
    serializeration is handled here.
    '''
    
    permission_classes = [IsAuthenticated,IsOwnerOrReadOnly]
    authentication_classes = [SessionAuthentication]
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    
    def perform_create(self, serializer):
        print(f'user - {self.request.user}')
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

    # /events/{id}/attendees/
    @action(detail=True, methods=['get'])
    def attendees(self, request,pk = None):
        my_event = self.get_object()
        print(f'all the events {my_event}')
        query = Reservation.objects.filter(event = my_event)
        print(f'all the reservations {query}')
        serializer = EventAttendees(query, many=True)
        # serializer.is_valid(raise_exception=True)
        return Response(serializer.data,status=status.HTTP_202_ACCEPTED)
    


class ReservationView(ModelViewSet):
    '''
    this is a post request/
    i have to run service before proceeding with response. do i over-ride entire create? 
    understand from the POV of the flow
    request comes in - dispatch - auth check - call request handler - serializer is called - now before perform create i have to make sure
    that booking happens in isolation so no other booking can happen at the same time. i.e i gotta over-ride entire create here. 
    since i have to make sure i lock the event then decrement the capacity or there is a chance capacity can go negative.
    another way is OCC . book now and before commit check if capacity is negative then cancel booking
    but for now i am going with - locking specific event. decrementing and creating the reservation then releasing the lock.
    '''
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def create(self, request):
        print(f'sending {request} vs sending {request.user}')

        serializer = ReservationSerializer(data = request.data, context = {'request':request})
        
        serializer.is_valid(raise_exception= True)
        # look what am i locking but? event has huge capacity. i am not retreving a row but a table.
        # basically if 2 requests are made for last booking, how do i resolve? PS cannot work because i am not locking any row here. 
        # nah i am getting it wrong because i am booking event and here event is not an entire table as i thinking
        # it's just a row with capacity so i gotta lock for capacity. we do retrieve event and lock
        event = serializer.validated_data['event']
        print(f'this is the event - {event} and the event id {event.id}')
        # date = serializer.validated_data['reservation_date']
        with transaction.atomic():

            event = Event.objects.select_for_update().get(pk = event.id)
            
            try:
                if event.capacity > 1:
                    print(f'current capacity {event.capacity}')
                    print(f'current user {request.user}')
                    event.capacity -= 1
                    event.save()
                    serializer.save(reserved_by = request.user, event = event)
                    return Response({'message':f'Congratulation! Booked for the {event.title}'},status=status.HTTP_201_CREATED)
                else:
                    return Response({'message':'out of capacity, cant book'},status=status.HTTP_400_BAD_REQUEST)
            except:
                raise ValueError('Internal Error')
                
                

                       