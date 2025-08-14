from django import forms
from django.core.validators import MinLengthValidator
from django.core.validators import MinValueValidator
from django.core.validators import MaxValueValidator
from .models import Book

def min_length_3_validator(value):
    if len(value)<3:
        raise forms.ValidationError('3글자 이상 입력하세요')

class BookForm(forms.Form): 
    title = forms.CharField(label="책제목")
    author = forms.CharField(label="글쓴이", 
                            validators=[min_length_3_validator]
                            # validators=[ MinLengthValidator(3)]
                            )
    publisher = forms.CharField(label="출판사", required=False)
    sales = forms.IntegerField(label="판매가",
                                initial=1000,
                                validators=[MinValueValidator(0),
                                            MaxValueValidator(100000)])
    def save(self, commit=True):
        book = Book(**self.cleaned_data) # cleaned_data 입력데이터들을 검증 완료 데이터
        if commit:
            book.save()
        return book
    
class BookModelForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'publisher', 'sales']
        # fields = '__all__'