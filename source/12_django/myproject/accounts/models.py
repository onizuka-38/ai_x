from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Profile(models.Model):
  user = models.OneToOneField(User,
          on_delete=models.CASCADE) # User가 삭제될 때, profile은 어떻게 할지?
  phone_number = models.CharField(verbose_name="전화", max_length=20)
  address      = models.CharField(verbose_name="주소", max_length=100)
  def __str__(self):
    return "{}({}-{})".format(self.user.username,
                              self.phone_number,
                              self.address)