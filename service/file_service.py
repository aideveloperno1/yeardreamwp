import os
import shutil

from fastapi import UploadFile

FILE_PATH = './upload'

if not os.path.exists(FILE_PATH):
    os.makedirs(FILE_PATH)
    print(f'{FILE_PATH} 폴더 생성 완료')

def file_upload(file:UploadFile) -> bool:
    success = False
    created = False

    # 파일명이 없는 경우
    if not file.filename:
        print('파일명이 없습니다.')
        return False

    # 파일명에 폴더 경로가 포함된 경우
    if '/' in file.filename or '\\' in file.filename:
        print('올바르지 않은 파일명입니다.')
        return False

    # PDF 확장자 확인
    if not file.filename.lower().endswith('.pdf'):
        print('PDF 파일만 업로드할 수 있습니다.')
        return False

    path = f'{FILE_PATH}/{file.filename}'
    try:
        # 같은 이름의 기존 파일은 덮어쓰지 않음
        with open(path,'xb') as file_obj: # 파일 객체 생성
            shutil.copyfileobj(file.file,file_obj)  # file.file 데이터를 읽어서 file_ohj에 복사
            success = True

            print(f'{file.filename} 저장 완료')
    except Exception as e:
        print(e)
        os.remove(path)
    return success