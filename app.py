from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gym.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_slot = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registered successfully. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid login', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    time_slots = [
        '6:00 AM - 7:00 AM',
        '7:00 AM - 8:00 AM',
        '8:00 AM - 9:00 AM',
        '5:00 PM - 6:00 PM',
        '6:00 PM - 7:00 PM',
        '7:00 PM - 8:00 PM'
    ]
    return render_template('index.html', time_slots=time_slots)

@app.route('/book', methods=['POST'])
@login_required
def book():
    time_slot = request.form['time_slot']
    date = request.form['date']

    existing = Booking.query.filter_by(user_id=current_user.id, time_slot=time_slot, date=date).first()
    if existing:
        flash('Slot already booked!', 'warning')
    else:
        new_booking = Booking(user_id=current_user.id, time_slot=time_slot, date=date)
        db.session.add(new_booking)
        db.session.commit()
        flash('Booking confirmed!', 'success')

    return redirect(url_for('bookings'))

@app.route('/bookings')
@login_required
def bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template('bookings.html', bookings=bookings)

@app.route('/cancel/<int:booking_id>')
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Not allowed!', 'danger')
    else:
        db.session.delete(booking)
        db.session.commit()
        flash('Booking canceled!', 'info')
    return redirect(url_for('bookings'))

if __name__ == '__main__':
    app.run(debug=True)
