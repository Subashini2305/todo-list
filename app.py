import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from dotenv import load_dotenv
load_dotenv()  # Load variables from .env
app = Flask(__name__)
app.secret_key = 'ehfbhioohtipuj'
app.config['MONGO_URI'] = os.getenv('MONGO')


mongo = PyMongo(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']

@login_manager.user_loader
def load_user(user_id):
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    return User(user) if user else None

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        user = mongo.db.users.find_one({'email': email})
        if user:
            flash("User already exists. Try a different email.")
            return redirect(url_for('register'))  # Use redirect here!
         # ✅ Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # ✅ Save hashed password to DB
        mongo.db.users.insert_one({
            'email': email,
            'username': username,
            'password': hashed_password
        })
        
        flash("Registration successful. You can now log in.")
        return redirect(url_for('login'))

    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = mongo.db.users.find_one({'email': email})
        if user and bcrypt.check_password_hash(user['password'], password):
            login_user(User(user))
            return redirect(url_for('home'))
        flash('Invalid credentials')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    user_data = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    return render_template(
    'home.html',
    todos=user_data.get('todos', []),  # ✅ fallback to empty list
    username=current_user.username
)



@app.route('/add_todo', methods=['POST'])
@login_required
def add_todo():
    task = request.form['task']
    user_data = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    todos = user_data.get('todos',[])
    new_id = todos[-1]['id'] + 1 if todos else 1
    todos.append({'id': new_id, 'task': task, 'done': False})
    mongo.db.users.update_one({'_id': ObjectId(current_user.id)}, {'$set': {'todos': todos}})
    return redirect(url_for('home'))

@app.route('/update_todo/<int:todo_id>')
@login_required
def update_todo(todo_id):
    user_data = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    todos = user_data['todos']
    for todo in todos:
        if todo['id'] == todo_id:
            todo['done'] = not todo['done']
            break
    mongo.db.users.update_one({'_id': ObjectId(current_user.id)}, {'$set': {'todos': todos}})
    return redirect(url_for('home'))

@app.route('/delete_todo/<int:todo_id>')
@login_required
def delete_todo(todo_id):
    user_data = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    todos = [todo for todo in user_data['todos'] if todo['id'] != todo_id]
    mongo.db.users.update_one({'_id': ObjectId(current_user.id)}, {'$set': {'todos': todos}})
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
    