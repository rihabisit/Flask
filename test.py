
from flask import Flask, request, jsonify
import pytesseract
from PIL import Image
import os
#import fitz  # PyMuPDF
from pdf2image import convert_from_path
# Initialize the Flask application
app = Flask(__name__)

output_folder = 'temp'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
# Table de conversion de texte en braille pour l'anglais et le français
BRAILLE_LATIN = {
    'a': '⠁', 'b': '⠃', 'c': '⠉', 'd': '⠙', 'e': '⠑',
    'f': '⠋', 'g': '⠛', 'h': '⠓', 'i': '⠊', 'j': '⠚',
    'k': '⠅', 'l': '⠇', 'm': '⠍', 'n': '⠝', 'o': '⠕',
    'p': '⠏', 'q': '⠟', 'r': '⠗', 's': '⠎', 't': '⠞',
    'u': '⠥', 'v': '⠧', 'w': '⠺', 'x': '⠭', 'y': '⠽',
    'z': '⠵',
    'é': '⠿', 'à': '⠷', 'ç': '⠯',
    '0': '⠴', '1': '⠂', '2': '⠆', '3': '⠒', '4': '⠲',
    '5': '⠢', '6': '⠖', '7': '⠶', '8': '⠦', '9': '⠔',
    ' ': ' ', '.': '⠲', ',': '⠠', '!': '⠖', '?': '⠦',
    '-': '⠤', '_': '⠸⠤', '*': '⠔',
    ':': '⠒', ';': '⠰', "'": '⠄', '"': '⠐',
    '(': '⠐', ')': '⠐', '@': '⠈⠤', '&': '⠮', '/': '⠤⠆'
}

# Table de conversion de texte en braille pour l'arabe
BRAILLE_ARABIC = {
    'ا': '⠁', 'ب': '⠃', 'ت': '⠞', 'ث': '⠹', 'ج': '⠚',
    'ح': '⠓', 'خ': '⠮', 'د': '⠙', 'ذ': '⠹', 'ر': '⠗',
    'ز': '⠵', 'س': '⠎', 'ش': '⠩', 'ص': '⠯', 'ض': '⠿',
    'ط': '⠾', 'ظ': '⠾', 'ع': '⠯', 'غ': '⠱', 'ف': '⠋',
    'ق': '⠟', 'ك': '⠅', 'ل': '⠇', 'م': '⠍', 'ن': '⠝',
    'ه': '⠓', 'و': '⠺', 'ي': '⠊', 'ى': '⠁', 'ء': '⠄',
    'ئ': '⠢', 'ؤ': '⠂', 'ة': '⠤', 'لا': '⠯', 'أ': '⠁',
    'إ': '⠊', 'آ': '⠜'
}
def text_to_braille(text, language):
    if language == 'ara':
        braille_alphabet = BRAILLE_ARABIC
    else:
        braille_alphabet = BRAILLE_LATIN
    
    braille_text = ''.join(braille_alphabet.get(char, char) for char in text)
    return braille_text

@app.route('/ocr', methods=['POST'])
def ocr_endpoint():
    try:
        image = request.files['image']
        languages = request.form.getlist('language')

        image_path = os.path.join(output_folder, 'temp_image.png')
        image.save(image_path)
        
        results = {}

        for language in languages:
            text = pytesseract.image_to_string(Image.open(image_path), lang=language)
            braille_text = text_to_braille(text.lower(), language)
            
            results[language] = {
                'text': text,
                'braille': braille_text
            }

        return jsonify(results)
    
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ocr_pdf', methods=['POST'])
def ocr_pdf_endpoint():
    try:
        pdf_file = request.files['pdf']
        languages = request.form.getlist('language')
        
        # Save PDF to a temporary location
        pdf_path = os.path.join(output_folder, 'temp_pdf.pdf')
        pdf_file.save(pdf_path)
        
        # Convert PDF pages to images
        images = convert_from_path(pdf_path, dpi=300, output_folder=output_folder)
        
        results = {}
        for i, image in enumerate(images):
            image_path = os.path.join(output_folder, f'temp_image_{i}.png')
            image.save(image_path)
            
            page_results = {}
            for language in languages:
                text = pytesseract.image_to_string(image, lang=language)
                braille_text = text_to_braille(text.lower(), language)
                
                page_results[language] = {
                    'text': text,
                    'braille': braille_text
                }
            
            results[f'page_{i + 1}'] = page_results
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)