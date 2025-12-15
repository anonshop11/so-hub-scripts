from flask import Flask, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import hashlib 
import os
import sys

# 1. การตั้งค่า Flask และฐานข้อมูล
app = Flask(__name__)
# ใช้ Environment Variable สำหรับ Secret Key (Production) หรือค่าเริ่มต้น (Development)
app.secret_key = os.environ.get('SECRET_KEY', 'ekfwofkoekfwok0002301232ofe[w[afsfafaffaf]]') 

# 🟢 บรรทัดที่ถูกแก้ไข: ดึง URL และปรับแก้ให้เข้ากับ Render/SQLAlchemy
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///users.db')

# ปรับแก้ URL จาก 'postgres://' เป็น 'postgresql+psycopg2://' เพื่อให้ Render ใช้งานได้
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 2. Model ฐานข้อมูล
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False) 

    def __repr__(self):
        return f'<User {self.username}>'

# ฟังก์ชันสำหรับเข้ารหัสรหัสผ่าน
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

with app.app_context():
    db.create_all()


# 9. ฟังก์ชันช่วยในการอ่านไฟล์ HTML และแทนที่ตัวแปร
def read_html_file(filename, **kwargs):
    """อ่านเนื้อหา HTML และแทนที่ตัวแปรที่ส่งมา"""
    base_dir = os.path.dirname(sys.argv[0])
    filepath = os.path.join(base_dir, filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
            # แทนที่ตัวแปร เช่น {{ username }}
            for key, value in kwargs.items():
                html_content = html_content.replace(f'{{{{ {key} }}}}', str(value))
            return html_content
    except FileNotFoundError:
        return f"<h1>Error: File {filename} not found.</h1><p>โปรดตรวจสอบว่าไฟล์ HTML อยู่ในไดเรกทอรีเดียวกับ app.py</p>"


# 3. กำหนดเส้นทาง (Routes)
@app.route('/')
def index():
    if 'username' in session:
        # หากเข้าสู่ระบบแล้ว: แสดงหน้า dashboard.html
        return read_html_file('dashboard.html', username=session['username'])
            
    # 👇 เปลี่ยนจาก 'index.html' เป็น 'landing.html'
    return read_html_file('landing.html')


# 4. เส้นทางสำหรับแสดงหน้าสมัครสมาชิก (GET)
@app.route('/register', methods=['GET']) 
def show_register():
    return read_html_file('register.html')

# 5. เส้นทางสำหรับการประมวลผลการลงทะเบียน (POST)
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if not username or not password or not confirm_password:
        return read_html_file('register.html').replace('<h2>สมัครสมาชิก</h2>', '<h2>กรุณากรอกข้อมูลให้ครบทุกช่อง</h2>')

    if password != confirm_password:
        return read_html_file('register.html').replace('<h2>สมัครสมาชิก</h2>', '<h2>รหัสผ่านไม่ตรงกัน กรุณาลองใหม่</h2>')

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return read_html_file('register.html').replace('<h2>สมัครสมาชิก</h2>', '<h2>ชื่อผู้ใช้นี้มีผู้ใช้งานแล้ว</h2>')
    
    hashed_pass = hash_password(password)
    
    new_user = User(username=username, password_hash=hashed_pass)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('show_login'))

# 6. เส้นทางสำหรับแสดงหน้าเข้าสู่ระบบ (GET)
@app.route('/login', methods=['GET'])
def show_login():
    return read_html_file('login.html')

# 7. เส้นทางสำหรับการประมวลผลการเข้าสู่ระบบ (POST)
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = User.query.filter_by(username=username).first()

    if user and user.password_hash == hash_password(password):
        session['username'] = user.username 
        return redirect(url_for('index'))
    else:
        return read_html_file('login.html').replace('<h2>เข้าสู่ระบบ</h2>', '<h2>ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง</h2>')

# 8. เส้นทางสำหรับการออกจากระบบ
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# การกำหนดค่าสำหรับ Production Deployment
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)