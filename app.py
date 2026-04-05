from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

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

# --- THE AUTO-FIX: Create tables before the first request ---
with app.app_context():
    db.create_all()

# 3. ROUTES
@app.route('/')
def index():
    cat = request.args.get('category')
    if cat:
        all_items = Item.query.filter_by(type=cat).all()
    else:
        all_items = Item.query.all()
    return render_template('index.html', items=all_items, current_cat=cat)

@app.route('/add', methods=['GET', 'POST'])
def add_item():
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
            image_file=filename
        )
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_item.html')

@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    item_to_delete = Item.query.get_or_404(item_id)
    if item_to_delete.image_file != 'default.jpg':
        image_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], item_to_delete.image_file)
        if os.path.exists(image_path):
            os.remove(image_path)
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)