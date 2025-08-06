from django.db import models

# Create your models here.
class Student(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    major = models.CharField(max_length=100, null=True, blank=True)
    age = models.IntegerField(default=0)
    grade = models.IntegerField(default=1)
    def __str__(self):
        return f"{self.id} : {self.name} ({self.major}), {self.grade}학년 {self.age}세"