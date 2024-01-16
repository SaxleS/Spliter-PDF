from flask import Flask, request, render_template, send_from_directory
import fitz  # PyMuPDF
import os
import io
import tempfile
import zipfile
from flask import Response



app = Flask(__name__)
SAVE_FOLDER = 'static/downloads/'


@app.route('/download/all', methods=['GET'])
def download_all_files():
    # Получите список всех файлов, которые вы хотите объединить
    split_files = [os.path.join(SAVE_FOLDER, filename) for filename in os.listdir(SAVE_FOLDER)]

    # Создайте временный архив, в который добавьте все файлы
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as archive:
            for split_file in split_files:
                # Добавьте каждый файл в архив
                archive.write(split_file, os.path.basename(split_file))

    # Определите имя архива
    zip_filename = 'all_split_files.zip'

    # Откройте архив для чтения и передайте его как поток веб-ответа
    with open(temp_zip.name, 'rb') as zip_file:
        response = Response(zip_file.read())
        response.headers['Content-Type'] = 'application/zip'
        response.headers['Content-Disposition'] = f'attachment; filename="{zip_filename}"'

    # Удалите временный архив после отправки
    os.remove(temp_zip.name)

    # Удалите все файлы в SAVE_FOLDER
    for split_file in split_files:
        os.remove(split_file)

    return response


def split_for_printing(pdf_stream, num_splits_horizontal, num_splits_vertical):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_file_path = temp_file.name
    with open(temp_file_path, "wb") as f:
        f.write(pdf_stream.read())

    doc = fitz.open(temp_file_path)
    split_pdf_paths = []

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        page_width = page.rect.width
        page_height = page.rect.height
        split_width = page_width / num_splits_horizontal
        split_height = page_height / num_splits_vertical

        for i in range(num_splits_horizontal):
            for j in range(num_splits_vertical):
                split_pdf = fitz.open()
                split_pdf_writer = split_pdf.new_page(-1, width=split_width, height=split_height)
                clip_rect = fitz.Rect(i * split_width, j * split_height, (i + 1) * split_width, (j + 1) * split_height)
                split_pdf_writer.show_pdf_page(split_pdf_writer.rect, doc, page_number, clip=clip_rect)
                split_pdf_stream = io.BytesIO()
                split_pdf.save(split_pdf_stream)
                split_pdf.close()

                split_pdf_path = os.path.join(SAVE_FOLDER, f"split_page_{page_number + 1}_part_{i + 1}_{j + 1}.pdf")
                with open(split_pdf_path, "wb") as out_file:
                    out_file.write(split_pdf_stream.getvalue())
                split_pdf_paths.append(split_pdf_path)

    doc.close()
    os.remove(temp_file_path)
    return split_pdf_paths

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('file')
        num_splits_horizontal = int(request.form.get('num_splits_horizontal', 4))
        num_splits_vertical = int(request.form.get('num_splits_vertical', 5))

        if file and file.filename:
            return process_uploaded_file(file, num_splits_horizontal, num_splits_vertical)
        return "No selected file"
    return render_template('index.html')

def process_uploaded_file(file, num_splits_horizontal, num_splits_vertical):
    split_files = split_for_printing(file.stream, num_splits_horizontal, num_splits_vertical)
    download_links = [os.path.join(SAVE_FOLDER, os.path.basename(file_path)) for file_path in split_files]
    return render_template('download_links.html', files=download_links)


@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    num_splits_horizontal = int(request.form.get('num_splits_horizontal', 4)) 
    num_splits_vertical = int(request.form.get('num_splits_vertical', 5))  # значение по умолчанию 5

    if file and file.filename:
        return process_uploaded_file(file, num_splits_horizontal, num_splits_vertical)
    return "No file part"

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    if '..' in filename or filename.startswith('/'):
        return "Invalid file path", 400
    return send_from_directory(SAVE_FOLDER, filename, as_attachment=True)

# if __name__ == '__main__':
#     if not os.path.exists(SAVE_FOLDER):
#         os.makedirs(SAVE_FOLDER)
#     app.run(debug=True)

if __name__ == '__main__':
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)
    
    # Получить порт из переменной окружения PORT, или использовать 5000 по умолчанию
    port = int(os.environ.get('PORT', 5000))
    
    app.run(host='0.0.0.0', port=port, debug=True)
