from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] 

    def __str__(self):
        return self.email

class Event(models.Model):
    title = models.CharField(max_length=10,blank = False)
    description = models.TextField(max_length=100)
    city = models.CharField(max_length=40)
    city_date_time = models.DateTimeField(auto_now=False, auto_now_add=False) # should i go for auto now or fixed?
    capacity = models.PositiveIntegerField(default=0,blank=False,null=False) # positive
    organizer = models.ForeignKey(CustomUser,on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

# as of now going with 1 user can book only 1 event at a time.
class Reservation(models.Model):
    reserved_by = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    reservation_date = models.DateTimeField(auto_now_add=True) # not required? since i don't have multiple dates feature
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True) # write only


