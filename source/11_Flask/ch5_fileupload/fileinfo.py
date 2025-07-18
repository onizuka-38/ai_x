# 특정폴더(uploads/)안의 파일들의 정보를 listup
import os
import datetime

UPLOAD_FOLDER = './uploads/'

def stamp2datetime(stamp):
  return datetime.datetime.fromtimestamp(stamp)

def info(filename):
  ctime = os.path.getctime(UPLOAD_FOLDER + filename) # 파일의 생성 시간
  mtime = os.path.getmtime(UPLOAD_FOLDER + filename) # 파일의 최종 수정 시간
  atime = os.path.getatime(UPLOAD_FOLDER + filename) # 파일의 최종 접근 시간 
  size = os.path.getsize(UPLOAD_FOLDER + filename) # 파일의 크기(byte 단위)
  if size >= 1024 * 1024:
    size = size / (1024 * 1024)
    size = "{:.3f}MB".format(size)
  elif size >= 1024:  
    size = size / 1024
    size = "{:.3f}KB".format(size)
  else:
    size = "{}B".format(size)
  return stamp2datetime(ctime), stamp2datetime(mtime), stamp2datetime(atime), size

if __name__ == '__main__':
  filelist = os.listdir(UPLOAD_FOLDER) # 해당 폴더의 파일이름 목록
  for filename in filelist:
    ctime, mtime, atime, size = info(filename)
    print(filename, ctime, mtime, atime, size)
    
# filelist = os.listdir(UPLOAD_FOLDER) # 해당 폴더의 파일이름 목록
# # print(filelist)
# for filename in filelist:
#   ctime = os.path.getctime(UPLOAD_FOLDER + filename) # 파일의 생성 시간
#   mtime = os.path.getmtime(UPLOAD_FOLDER + filename) # 파일의 최종 수정 시간
#   atime = os.path.getatime(UPLOAD_FOLDER + filename) # 파일의 최종 접근 시간 
#   size = os.path.getsize(UPLOAD_FOLDER + filename) # 파일의 크기(byte 단위)
#   print(filename, ctime, mtime, atime, size)