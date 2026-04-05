from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "mits_secret_key_2026" # This keeps the 'Gate Pass' secure

# 1. CONFIGURATION
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'campus.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

db = SQLAlchemy(app)

# 2. DATABASE MODEL
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(20), default="N/A")
    contact = db.Column(db.String(20), nullable=False)
    desc = db.Column(db.Text, nullable=True)
    image_file = db.Column(db.String(100), nullable=True, default='default.jpg')
    student_name = db.Column(db.String(100))
    branch = db.Column(db.String(50))
    semester = db.Column(db.String(10))

# --- SMART DECODER ---
def decode_mits_email(email):
    username = email.split('@')[0]
    dept_code = "".join([char for char in username if char.isalpha()]).lower()
    depts = {'ce': 'Civil', 'me': 'Mechanical', 'cse': 'CS', 'it': 'IT', 'ee': 'Electrical', 'ec': 'Electronics'}
    return depts.get(dept_code, "MITS Student")

with app.app_context():
    db.create_all()

# 3. THE "GATEKEEPER" ROUTES
@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        email = request.form.get('email').lower()
        if email.endswith('@mitsgwl.ac.in'):
            # Set the Gate Pass (Session)
            session['user_email'] = email
            session['user_branch'] = decode_mits_email(email)
            session['user_name'] = "".join([i for i in email.split('@')[0] if not i.isdigit()]).title()
            return redirect(url_for('index'))
        else:
            return "<h1>Invalid Email! Use @mitsgwl.ac.in</h1><a href='/verify'>Try Again</a>"
    return render_template('verify.html')

@app.route('/')
def index():
    if 'user_email' not in session:
        return redirect(url_for('verify'))
    
    cat = request.args.get('category')
    all_items = Item.query.filter_by(type=cat).all() if cat else Item.query.all()
    return render_template('index.html', items=all_items, current_cat=cat)

@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if 'user_email' not in session:
        return redirect(url_for('verify'))

    if request.method == 'POST':
        file = request.files.get('image')
        filename = 'default.jpg'
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename))

        new_entry = Item(
            type=request.form.get('type'),
            title=request.form.get('title'),
            price=request.form.get('price') or "N/A",
            contact=request.form.get('contact'),
            desc=request.form.get('desc'),
            image_file=filename,
            student_name=session['user_name'], # Auto-filled from session
            branch=session['user_branch'],     # Auto-filled from session
            semester=request.form.get('semester')
        )
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_item.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('verify'))

if __name__ == '__main__':
    app.run(debug=True)