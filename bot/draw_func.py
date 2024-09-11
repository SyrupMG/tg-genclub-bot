import io
import random

from PIL import Image, ImageDraw

def make_drawing(bg_color = "white") -> tuple[ImageDraw, Image]:
    WIDTH = 512
    HEIGHT = 512

    img = Image.new('RGB', (WIDTH, HEIGHT), color=bg_color)
    return (ImageDraw.Draw(img), img)

def random_color():
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def circle_picture() -> io.BytesIO:
    draw, img = make_drawing()
    
    center_x = random.randint(0, img.width)
    center_y = random.randint(0, img.height)
    radius = random.randint(10, img.width / 2)
    color = random_color()
    
    draw.ellipse([center_x-radius, center_y-radius, center_x+radius, center_y+radius], fill=color)
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return img_byte_arr

def face_picture() -> io.BytesIO:
    # Случайный цвет фона
    background_color = random_color()

    draw, img = make_drawing(background_color)
    
    # Рисуем лицо (эллипс случайного размера и цвета)
    face_color = random_color()
    face_width = random.randint(img.width // 2, img.width - 50)
    face_height = random.randint(img.height // 2, img.height - 50)
    face_left = (img.width - face_width) // 2
    face_top = (img.width - face_height) // 2
    draw.ellipse([face_left, face_top, face_left + face_width, face_top + face_height], fill=face_color)
    
    # Рисуем глаза (два эллипса случайного размера и цвета)
    for _ in range(2):
        eye_color = random_color()
        eye_width = random.randint(face_width // 8, face_width // 4)
        eye_height = random.randint(face_height // 8, face_height // 4)
        eye_left = random.randint(face_left + eye_width, face_left + face_width - 2*eye_width)
        eye_top = random.randint(face_top + eye_height, face_top + face_height//2 - eye_height)
        draw.ellipse([eye_left, eye_top, eye_left + eye_width, eye_top + eye_height], fill=eye_color)
        
        # Рисуем зрачки
        pupil_color = random_color()
        pupil_size = random.randint(eye_width // 4, eye_width // 2)
        pupil_left = eye_left + (eye_width - pupil_size) // 2
        pupil_top = eye_top + (eye_height - pupil_size) // 2
        draw.ellipse([pupil_left, pupil_top, pupil_left + pupil_size, pupil_top + pupil_size], fill=pupil_color)
    
    # Рисуем рот (дуга случайного размера, положения и цвета)
    mouth_color = random_color()
    mouth_width = random.randint(face_width // 2, face_width - 20)
    mouth_height = random.randint(face_height // 4, face_height // 2)
    mouth_left = face_left + (face_width - mouth_width) // 2
    mouth_top = face_top + face_height // 2
    mouth_right = mouth_left + mouth_width
    mouth_bottom = mouth_top + mouth_height
    
    # Случайно выбираем, будет ли рот улыбкой или хмурым
    if random.choice([True, False]):
        # Улыбка
        draw.arc([mouth_left, mouth_top, mouth_right, mouth_bottom], start=0, end=180, fill=mouth_color, width=random.randint(5, 20))
    else:
        # Хмурый рот
        draw.arc([mouth_left, mouth_top, mouth_right, mouth_bottom], start=180, end=360, fill=mouth_color, width=random.randint(5, 20))
    
    # Добавляем случайные элементы (например, веснушки или румянец)
    if random.choice([True, False]):
        freckle_color = random_color()
        for _ in range(random.randint(5, 20)):
            x = random.randint(face_left, face_left + face_width)
            y = random.randint(face_top, face_top + face_height)
            draw.ellipse([x, y, x+5, y+5], fill=freckle_color)
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return img_byte_arr