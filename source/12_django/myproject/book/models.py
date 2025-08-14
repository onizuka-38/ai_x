from django.db import models
from django import forms
from django.core.validators import MinLengthValidator
from django.core.validators import MinValueValidator
from django.core.validators import MaxValueValidator
from django.urls import reverse
# Create your models here.
def min_length_3_validator(value):
    if len(value)<3:
        raise forms.ValidationError('3글자 이상 입력하세요')

class Book(models.Model): # book_book 테이블
    title = models.CharField(verbose_name="책이름", max_length=50)
    author = models.CharField(verbose_name="글쓴이", 
                            max_length=50, 
                            validators=[min_length_3_validator]
                            # validators=[ MinLengthValidator(3)]
                            )
    publisher = models.CharField(verbose_name="출판사",
                                max_length=50,
                                null=True, blank=True)
    sales = models.IntegerField(verbose_name="판매가",
                                default=1000,
                                validators=[MinValueValidator(0),
                                            MaxValueValidator(100000)])
    ip = models.GenericIPAddressField(blank=True, null=True)
    publication_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}:{self.author}저 {self.sales}원 from{self.ip}"
    
    def get_absolute_url(self):
        return reverse("book:list")
    
    class Meta:
        ordering = ['-publication_date']
        unique_together = (('title','author'),) #title과 author가 같으면 저장 불가
    