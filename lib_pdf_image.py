from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os


def generate_image_pdf(image_paths, file_path):
    # A4 size
    w, h = A4
    c = canvas.Canvas(file_path, pagesize=A4)

    # 한글 전용 폰트 설정
    font_path = "NanumGothic.ttf"  # 프로젝트 디렉토리에 저장된 한글 폰트 파일의 경로
    pdfmetrics.registerFont(TTFont('KoreanFont', font_path))

    # 4개씩 묶기 -> 페이지 분할
    positions = [(0, h / 2), (w / 2, h / 2), (0, 0), (w / 2, 0)]
    sizes = [(w / 2, h / 2), (w / 2, h / 2), (w / 2, h / 2), (w / 2, h / 2)]

    # 페이지 구성 (4개씩)
    for page_num in range(0, len(image_paths), 4):
        # 페이지 한글 폰트 설정
        c.setFont('KoreanFont', 6)

        # 1<=n<=4 개의 이미지들을 페이지에 배치
        page_images = image_paths[page_num:page_num + 4]
        for i, img_path in enumerate(page_images):
            # 이미지 사이즈 및 비율
            img = Image.open(img_path)
            img_width, img_height = img.size
            scale_factor = min(sizes[i][0] / img_width, (sizes[i][1] - 20) / img_height)

            new_width = img_width * scale_factor
            new_height = img_height * scale_factor

            # 페이지 내 이미지 좌표 설정
            x_offset = (sizes[i][0] - new_width) / 2
            y_offset = (sizes[i][1] - new_height) / 2 + 10

            x = positions[i][0] + x_offset
            y = positions[i][1] + y_offset

            # 이미지 배치
            c.drawImage(img_path, x, y, width=new_width, height=new_height)

            # 파일명 텍스트 배치
            filename = os.path.basename(img_path)
            text_x = positions[i][0] + (sizes[i][0] - c.stringWidth(filename, 'KoreanFont', 6)) / 2
            c.drawString(text_x, positions[i][1] + y_offset - 15, filename)

        # 페이지 업데이트
        c.showPage()
        
    c.save()
    print(f"Excel file successfully saved as {file_path}")
    print('...')
