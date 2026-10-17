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
from .permissions import IsOwnerOrReadOnly,IsBookedOrReadOnly
# Create your views here.
from .models import Event,Reservation
from rest_framework.authentication import SessionAuthentication
from django.db import transaction
from rest_framework.decorators import action
from rest_framework import filters
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
    search_fields = ['title','city']
    filter_backends = (filters.SearchFilter,)
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def get_queryset(self):
        if self.action == 'retrieve':
            return Event.objects.select_related('event').all()
        return Event.objects.all().order_by('city_date_time')
    
    def perform_create(self, serializer):
        print(f'user - {self.request.user}')
        # how to access organizer here? 
        # get the specific event. since it's a post but event has not been created yet. 
        serializer.save(organizer = self.request.user) # do i need to send other data as well? nope. 
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
    
    @action(detail=False, methods = ['get'])
    def summary(self, request):
        '''
        Aggregate stats across the requester's own events: 
        total events, total reservations received, seats still open.

        -----------------------------------------------------
        > since complete information is not provided. should i like compute across all events?
        if organizer has 3 events. do i need a separate summary for each event? or do i need a
        total across all the events?

        > if i am looping i can just as well compute for each event but that's not optimized for now. 
        '''

        '''
        1. total events ☑️
        2. total reservations (for each?) ☑️ 
        3. seats still open (for each?) ☑️
        -----

        '''
        # my_event = self.get_object() # get current event object
        event_summary = Event.objects.filter(organizer = request.user) #[1,3,4]
        print(f'total events - {event_summary}')
        total_summary = {}
        total_summary['total-events-created'] = f"{len(event_summary)} Events total"
        total_summary[f"Reservations per event"] = []
        # reserved_seats = Reservation.objects.filter(event = my_event) # seats reserved for the event
        for each_event in (event_summary):
            print(f'testing for {each_event.title}')
            # for each event get the reservations booked
            reserved_seats = Reservation.objects.filter(event = each_event)
            total_summary[f"Reservations per event"].append(f'\nEvent {each_event} had {len(reserved_seats)} seats reserved out of {each_event.capacity}')
            if each_event.capacity > len(reserved_seats):
                seats_left = each_event.capacity - len(reserved_seats)
                total_summary[f"Seats-left-for-Event {each_event}"] = seats_left
            else:
                seats_left = len(reserved_seats) - each_event.capacity 
            total_summary[f"Seats-left-for-Event {each_event}"] = seats_left
        return Response(total_summary,status=status.HTTP_200_OK)
        
        # for capacity left gotta use reservation to fetch how many users have reserved for the event
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
    permission_classes = [IsAuthenticated,IsBookedOrReadOnly]
    authentication_classes = [SessionAuthentication]
    def get_queryset(self):
        return Reservation.objects.filter(reserved_by=self.request.user)
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
                
                

                       