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
    # 저장 경로 생성
    path = f'{FILE_PATH}/{file.filename}'

    try:
        # 업로드 파일의 읽기 위치를 처음으로 이동
        file.file.seek(0)
        # 새 파일 생성
        # xb: 바이너리 쓰기 모드, 같은 이름이 있으면 오류 발생
        with open(path,'xb') as file_obj:
            created = True
            shutil.copyfileobj(file.file,file_obj)  # file.file 데이터를 읽어서 file_ohj에 복사
        success = True
        print(f'{file.filename} 저장 완료')

    except FileExistsError:
        # 기존 파일은 삭제하지 않음
        print(f'같은 이름의 파일이 이미 있습니다: {file.filename}')

    except Exception as e:
        print(f'파일 저장 실패: {e}')

        # 이번 업로드에서 생성한 불완전한 파일만 삭제
        if created:
            try:
                os.remove(path)
            except OSError as cleanup_error:
                print(f'실패한 파일 삭제 오류: {cleanup_error}')

    return success