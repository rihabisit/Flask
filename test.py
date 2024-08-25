
"""
Ce script Flask implÃ©mente un service web d'OCR (Reconnaissance Optique de CaractÃ¨res) qui convertit des images 
et des fichiers PDF en texte, puis en braille. Le service prend en charge plusieurs langues, notamment l'arabe et 
les langues basÃ©es sur l'alphabet latin.

Les principales fonctionnalitÃ©s du script sont :
1. Conversion d'images en texte avec l'OCR.
2. Conversion de fichiers PDF en images pour en extraire le texte.
3. Traduction du texte extrait en braille, en fonction de la langue spÃ©cifiÃ©e.

Modules utilisÃ©s :
- Flask : pour crÃ©er une application web lÃ©gÃ¨re.
- Pytesseract : une interface pour Tesseract-OCR, utilisÃ©e pour extraire du texte Ã  partir d'images.
- PIL (Python Imaging Library) : pour la manipulation d'images.
- pdf2image : pour convertir les pages PDF en images.
- os : pour interagir avec le systÃ¨me de fichiers.

FonctionnalitÃ©s dÃ©taillÃ©es :
- `text_to_braille`: Fonction qui prend du texte et une langue en entrÃ©e et convertit le texte en braille 
   en fonction de la table de correspondance dÃ©finie pour la langue.
   
- `ocr_endpoint`: Route Flask qui gÃ¨re les requÃªtes POST envoyÃ©es avec une image. 
   L'image est sauvegardÃ©e, puis analysÃ©e avec Tesseract pour extraire le texte dans les langues spÃ©cifiÃ©es. 
   Le texte extrait est ensuite converti en braille et retournÃ© sous forme de JSON.
   
- `ocr_pdf_endpoint`: Route Flask qui gÃ¨re les requÃªtes POST envoyÃ©es avec un fichier PDF. 
   Le PDF est converti en images, puis chaque page est analysÃ©e pour extraire le texte dans les langues spÃ©cifiÃ©es. 
   Le texte de chaque page est ensuite converti en braille et retournÃ© sous forme de JSON.

- `BRAILLE_LATIN` et `BRAILLE_ARABIC`: Tables de conversion qui mappent les caractÃ¨res des alphabets latin et arabe 
   vers leurs Ã©quivalents en braille.

- `if __name__ == '__main__'`: DÃ©marre l'application Flask en mode debug pour permettre le dÃ©veloppement local.
"""
from flask import Flask, request, jsonify
import pytesseract
from PIL import Image
import cv2
import os
from flask_cors import CORS
from pdf2image import convert_from_path
from pdf2image import convert_from_path
app = Flask(__name__)
CORS(app)
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
    'إ': '⠊', 'آ': '⠜',
    '0': '⠴', '1': '⠂', '2': '⠆', '3': '⠒', '4': '⠲',
    '5': '⠢', '6': '⠖', '7': '⠶', '8': '⠦', '9': '⠔',
    ' ': ' ', '.': '⠲', ',': '⠠', '!': '⠖', '?': '⠦',
    '-': '⠤', '_': '⠸⠤', '*': '⠔',
    ':': '⠒', ';': '⠰', "'": '⠄', '"': '⠐',
    '(': '⠐', ')': '⠐', '@': '⠈⠤', '&': '⠮', '/': '⠤⠆'
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
         print("Received files:", request.files)
         print("Received form data:", request.form)
         pytesseract.pytesseract.tesseract_cmd = r"Tesseract-OCR/tesseract.exe"
         pytesseract.pytesseract.tesseract_cmd = r"C:\Users\DELL\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
         image = request.files['image']
         languages = request.form.getlist('language[]')
         gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
         threshold_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
         image_path = os.path.join(output_folder, 'temp_image.png')
         image.save(image_path)
         results = {}
         for language in languages:
             text = pytesseract.image_to_string(Image.open(image_path), lang=language)
             print(f"Extracted text for language {language}: {text}")
             results[language] = {
                 'text': text,
             }

         return jsonify(results)
    
     except Exception as e:
         return jsonify({'error': str(e)}), 500

    

@app.route('/ocr_pdf', methods=['POST'])
def ocr_pdf_endpoint():
     try:
         pdf_file = request.files['pdf']
         languages = request.form.getlist('language[]')
        
         pdf_path = os.path.join(output_folder, 'temp_pdf.pdf')
         pdf_file.save(pdf_path)
         pytesseract.pytesseract.tesseract_cmd = r"C:\Users\DELL\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
         poppler_path = r"C:\Users\DELL\poppler-24.07.0\Library\bin"
         images = convert_from_path(pdf_path, dpi=300, output_folder=output_folder, poppler_path=poppler_path)
         gray = cv2.cvtColor(images, cv2.COLOR_BGR2GRAY)
         threshold_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
         results = {}
         for i, image in enumerate(images):
             image_path = os.path.join(output_folder, f'temp_image_{i}.png')
             image.save(image_path)
            
          
             for language in languages:
                 text = pytesseract.image_to_string(image, lang=language)
                 print(f"Extracted text for language {language}: {text}")
                 results[language] = {
                     'text': text,
                 }
            
           
        
         return jsonify(results)
    
     except Exception as e:
       
         return jsonify({'error': str(e)}), 500
     
     
@app.route('/transcribe_braille', methods=['POST'])
def transcribe_braille_endpoint():
     try:
         text = request.form.get('text', '')  
         language = request.form.get('language', 'eng')  

         braille_text = text_to_braille(text.lower(), language)
         return braille_text  

     except Exception as e:
         return str(e), 500  


if __name__ == '__main__':
     port = int(os.environ.get('PORT', 5000))
     app.run(host='0.0.0.0', port=port)

