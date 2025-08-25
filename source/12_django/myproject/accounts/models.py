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

# 이벤트처리==signals사용(post_save) : profile.save()성공시 가입인사를 메일 전송
from django.db.models.signals import post_save
from django.core.mail import send_mail

def on_send_mail(sender, **kwargs):
  print('★ on_send_mail :', kwargs)
  if kwargs['created']: # True : 회원가입, False : 각종 회원정보 수정
    user = kwargs['instance'].user
    if not user.email: # 회원가입시 메일 입력 안 함
      print('★ 메일 주소가 없어서 메일 못 보내요')
      return
    # 메일 보내기
    subject = f"{user.username}님 XXX에 가입해 주셔서 감사합니다(메일 제목)"
    body = f"안녕하세요 {user.username}님 가입인사를 받으시면 최고의 서비스를 드립니다. 어쩌구 저쩌구(메일내용)"
    bodyHtml = f"<h1>안녕하세요 {user.username}님 가입인사를 받으시면 최고의 서비스를 드림</h1> <p>진심진심(메일내용)</p>"
    # settings.py에 EMAIL_BACKEND 설정
    send_mail(
      subject=subject,
      message=body,
      from_email="comlec0703@gmail.com",
      recipient_list=[user.email],
      html_message=bodyHtml,
      fail_silently=False # 메일 전송이 안 되었을 경우, 아무일도 하지 않음
    )
# on_send_mail함수와 post_save로 연결
post_save.connect(on_send_mail, sender=Profile)