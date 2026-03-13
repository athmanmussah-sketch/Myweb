from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import random
import string
import hashlib
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'darkx-web-tools-secret'

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# ============================================
# TOOL 1: QR CODE GENERATOR (Inafanya kazi 100%)
# ============================================
@app.route('/api/qr', methods=['POST'])
def generate_qr():
    data = request.json.get('data', 'DarkX Dev')
    import qrcode
    from io import BytesIO
    import base64
    
    img = qrcode.make(data)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return jsonify({'qr': f'data:image/png;base64,{img_str}'})

# ============================================
# TOOL 2: PASSWORD GENERATOR
# ============================================
@app.route('/api/password', methods=['GET'])
def generate_password():
    length = int(request.args.get('length', 12))
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(chars) for _ in range(length))
    return jsonify({'password': password})

# ============================================
# TOOL 3: TEXT ENCRYPT/DECRYPT
# ============================================
@app.route('/api/encrypt', methods=['POST'])
def encrypt_text():
    text = request.json.get('text', '')
    # Simple Caesar cipher
    shift = 3
    result = ""
    for char in text:
        if char.isupper():
            result += chr((ord(char) + shift - 65) % 26 + 65)
        elif char.islower():
            result += chr((ord(char) + shift - 97) % 26 + 97)
        else:
            result += char
    return jsonify({'result': result})

@app.route('/api/decrypt', methods=['POST'])
def decrypt_text():
    text = request.json.get('text', '')
    # Reverse Caesar cipher
    shift = -3
    result = ""
    for char in text:
        if char.isupper():
            result += chr((ord(char) + shift - 65) % 26 + 65)
        elif char.islower():
            result += chr((ord(char) + shift - 97) % 26 + 97)
        else:
            result += char
    return jsonify({'result': result})

# ============================================
# TOOL 4: FILE CONVERTER (TEXT TO PDF)
# ============================================
@app.route('/api/txt-to-pdf', methods=['POST'])
def txt_to_pdf():
    from fpdf import FPDF
    import tempfile
    
    text = request.json.get('text', '')
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Split text into lines
    lines = text.split('\n')
    for line in lines:
        pdf.cell(200, 10, txt=line[:50], ln=True)
    
    # Save to temp file
    temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(temp.name)
    
    return send_file(temp.name, as_attachment=True, download_name='document.pdf')

# ============================================
# TOOL 5: UNIT CONVERTER
# ============================================
@app.route('/api/convert', methods=['POST'])
def convert_units():
    value = float(request.json.get('value', 0))
    from_unit = request.json.get('from', 'cm')
    to_unit = request.json.get('to', 'm')
    
    conversions = {
        'cm_to_m': value / 100,
        'm_to_cm': value * 100,
        'kg_to_g': value * 1000,
        'g_to_kg': value / 1000,
        'c_to_f': (value * 9/5) + 32,
        'f_to_c': (value - 32) * 5/9,
    }
    
    key = f"{from_unit}_to_{to_unit}"
    result = conversions.get(key, value)
    
    return jsonify({'result': round(result, 2)})

# ============================================
# TOOL 6: AGE CALCULATOR
# ============================================
@app.route('/api/age', methods=['POST'])
def calculate_age():
    birth_year = int(request.json.get('year', 2000))
    birth_month = int(request.json.get('month', 1))
    birth_day = int(request.json.get('day', 1))
    
    today = datetime.now()
    birth_date = datetime(birth_year, birth_month, birth_day)
    
    age = today.year - birth_date.year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    return jsonify({'age': age})

# ============================================
# TOOL 7: RANDOM COLOR GENERATOR
# ============================================
@app.route('/api/color', methods=['GET'])
def random_color():
    color = '#' + ''.join(random.choices('0123456789ABCDEF', k=6))
    return jsonify({'color': color})

# ============================================
# TOOL 8: BMI CALCULATOR
# ============================================
@app.route('/api/bmi', methods=['POST'])
def calculate_bmi():
    weight = float(request.json.get('weight', 70))  # kg
    height = float(request.json.get('height', 170)) / 100  # cm to m
    
    bmi = weight / (height * height)
    
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal weight"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    
    return jsonify({
        'bmi': round(bmi, 1),
        'category': category
    })

# ============================================
# TOOL 9: LOAN CALCULATOR
# ============================================
@app.route('/api/loan', methods=['POST'])
def calculate_loan():
    amount = float(request.json.get('amount', 1000000))
    rate = float(request.json.get('rate', 10)) / 100 / 12
    years = int(request.json.get('years', 1))
    months = years * 12
    
    monthly = (amount * rate * (1 + rate)**months) / ((1 + rate)**months - 1)
    total = monthly * months
    
    return jsonify({
        'monthly': round(monthly, 2),
        'total': round(total, 2)
    })

# ============================================
# TOOL 10: TEXT COUNTER
# ============================================
@app.route('/api/count', methods=['POST'])
def count_text():
    text = request.json.get('text', '')
    
    return jsonify({
        'characters': len(text),
        'words': len(text.split()),
        'lines': len(text.split('\n')),
        'spaces': text.count(' ')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
