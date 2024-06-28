import os

# 폴더 경로
folder_path = 'transactions'

# 이미지 파일의 확장자 목록
image_extensions = ['.jpg', '.jpeg', '.png', '.gif']

# 새로운 파일 이름 형식 (여기서는 'image_숫자.확장자' 형식으로 변경)
new_file_prefix = 'image_'

# 폴더 안의 파일 목록 가져오기
files = os.listdir(folder_path)

# 파일 이름 변경
import lib_sanitizer as Df
for i, file in enumerate(files):
    break
    file_extension = os.path.splitext(file)[1].lower()
    if file_extension in image_extensions:
        info_box = []
        _date, _branch, _transaction, _description = file.split('.')[0].split('_')

        info_box.append(_date)
        info_box.append(_branch[5::])
        info_box.append(_transaction)
        info_box.append(_description)

        new_file_name = '_'.join(info_box) + file_extension
        os.rename(os.path.join(folder_path, file), os.path.join(folder_path, new_file_name))

print("파일 이름 변경 완료")
