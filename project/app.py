from flask import Flask, render_template, request,json, redirect,jsonify, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import os
from datetime import datetime, date
import re

app = Flask(__name__)
app.secret_key = '007'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi'}

UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
migrate = Migrate(app, db)


wishlist_trips = db.Table(
    'wishlist_trips',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('trip_id', db.Integer, db.ForeignKey('trip.id'), primary_key=True)
)

# Association Table for Booked Trips
booked_trips = db.Table(
    'booked_trips',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('trip_id', db.Integer, db.ForeignKey('trip.id'), primary_key=True)
)

# Association Table for Past Trips
# filepath: /c:/Users/betar/Videos/admin2/app.py
from sqlalchemy import Enum

past_trips = db.Table(
    'past_trips',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('trip_id', db.Integer, db.ForeignKey('trip.id'), primary_key=True),
    db.Column('review', db.Text),
    db.Column('review_type', Enum('private', 'public', name='review_type_enum'), nullable=True)
)

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    place = db.Column(db.String(120), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    template_image = db.Column(db.String(120), nullable=True)
    template_details = db.Column(db.Text, nullable=True)
    view_trip_media = db.Column(db.String(120), nullable=True)
    view_paragraph = db.Column(db.Text, nullable=True)
    things_to_do = db.Column(db.Text, nullable=True)
    gallery = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    details = db.Column(db.Text, nullable=True)
    seat_availability = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='upcoming') 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Ensure this line is present
    user = db.relationship('User', back_populates='trips')  # Ensure this line is present

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    profile_image = db.Column(db.String(120), nullable=True)
    name = db.Column(db.String(120), nullable=True)
    loyalty_points = db.Column(db.Integer, default=0)
    loyalty_rating = db.Column(db.String(20), default='Silver')
    status = db.Column(db.String(20), nullable=True)
    wishlist = db.relationship('Trip', secondary=wishlist_trips, backref='wishlisted_by')
    booked_trips = db.relationship('Trip', secondary=booked_trips, backref='booked_by')
    past_trips = db.relationship('Trip', secondary=past_trips, backref='past_by')
    trips = db.relationship('Trip', back_populates='user') 
    
    
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(120), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    details = db.Column(db.Text, nullable=True)
    points = db.Column(db.Integer, nullable=False) 

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    product = db.relationship('Product', backref='cart_items')
    user = db.relationship('User', backref='cart_items')

DB_FILE = "database.db"

with app.app_context():
    if not os.path.exists(DB_FILE):  
        db.create_all()
        print("Database and tables created successfully!")
    else:
        print("Using existing database.")


@app.route('/')
def front_design():
    """Render the front design page."""
    return render_template('frontdesign.html')

PASSWORD_REGEX = {
    "min_length": r".{8,}",  # At least 8 characters
    "uppercase": r"[A-Z]",   # At least one uppercase letter
    "lowercase": r"[a-z]",   # At least one lowercase letter
    "digit": r"\d",          # At least one digit
    "special_char": r"[!@#$%^&*(),.?\":{}|<>]",  # At least one special character
}

@app.route('/homepage')
def homepage():
    """Render the homepage with user profile and public reviews."""
    
    # Get logged-in user details (for navbar)
    username = session.get('username')
    user = User.query.filter_by(username=username).first() if username else None
    profile_image = user.profile_image if user and user.profile_image else 'default.png'  # Use default image if None

    # Use 'name' if available, otherwise use 'username'
    display_name = user.name if user and user.name else user.username if user else "Guest"

    # Fetch public reviews
    public_reviews = db.session.query(
        User.name, 
        User.username, 
        User.profile_image, 
        Trip.title, 
        Trip.start_date, 
        past_trips.c.review  
    ).join(
        past_trips, past_trips.c.user_id == User.id  
    ).join(
        Trip, past_trips.c.trip_id == Trip.id
    ).filter(
        past_trips.c.review_type == 'public'  
    ).all()
    
    reviews = []
    for review_name, review_user, review_profile, trip_title, trip_start_date, review in public_reviews:
        # Use name if available, otherwise use username
        reviewer_name = review_name if review_name else review_user
        print(f"Debug: {reviewer_name} - Profile Image: {review_profile}")  # 🔍 Debugging

        reviews.append({
            'username': reviewer_name,
            'profile_image': review_profile if review_profile else 'default.png',
            'review': review,
            'trip_title': trip_title,
            'trip_start_date': trip_start_date.strftime('%d %b %Y')
        })

    return render_template('homepage.html', username=display_name, profile_image=profile_image, reviews=reviews)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Validation flags and error tracking
        errors = False

        # Username validation
        if not username:
            flash("Username is required.", "user")
            errors = True
        elif User.query.filter_by(username=username).first():
            flash("Username already exists.", "user")
            errors = True

        # Email validation
        if not email:
            flash("Email is required.", "email")
            errors = True
        elif User.query.filter_by(email=email).first():
            flash("Email already registered.", "email")
            errors = True

        # Password validation
        if not password:
            flash("Password is required.", "password")
            errors = True
        elif password != confirm_password:
            flash("Passwords do not match.", "password")
            errors = True
        else:
            if not re.match(PASSWORD_REGEX["min_length"], password):
                flash("Password must be at least 8 characters.", "password")
                errors = True
            if not re.search(PASSWORD_REGEX["uppercase"], password):
                flash("Password must include at least one uppercase letter.", "password")
                errors = True
            if not re.search(PASSWORD_REGEX["lowercase"], password):
                flash("Password must include at least one lowercase letter.", "password")
                errors = True
            if not re.search(PASSWORD_REGEX["digit"], password):
                flash("Password must include at least one digit.", "password")
                errors = True
            if not re.search(PASSWORD_REGEX["special_char"], password):
                flash("Password must include at least one special character.", "password")
                errors = True

        # If any errors, re-render the signup page with flashed messages
        if errors:
            return render_template('signup.html', username=username, email=email)

        # If no errors, create new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Signup successful! Please sign in.", "success")
            return redirect(url_for('signin'))
        except Exception as e:
            flash("An error occurred while creating the account. Please try again.", "danger")
            return render_template('signup.html', username=username, email=email)

    # Render signup page
    return render_template('signup.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    """Handle user signin."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username
            flash("Login successful!", "success")
            return redirect(url_for('homepage'))
        else:
            flash("Invalid credentials!", "error")
    return render_template('signin.html')




@app.route('/get_username')
def get_username():
    user = User.query.filter_by(username=session.get('username')).first()
    return jsonify(username=user.name if user else "Guest")

def update_trip_statuses():
    """Update the status of trips based on the current date."""
    current_date = datetime.utcnow().date()
    upcoming_trips = Trip.query.filter(Trip.status == 'upcoming', Trip.start_date <= current_date, Trip.end_date >= current_date).all()
    for trip in upcoming_trips:
        trip.status = 'ongoing'
    ongoing_trips = Trip.query.filter(Trip.status == 'ongoing', Trip.end_date < current_date).all()
    for trip in ongoing_trips:
        trip.status = 'history'
    db.session.commit()

@app.route('/upcoming')
def upcoming():
    """Render the upcoming trips page."""
    update_trip_statuses()
    current_date = datetime.utcnow().date()
    trips = Trip.query.filter(Trip.start_date > current_date).all()
    formatted_trips = []
    username = session.get('username')
    user = User.query.filter_by(username=username).first() if username else None
    profile_image = user.profile_image if user.profile_image else 'default.png' 
    
    for trip in trips:
        try:
            start_date = trip.start_date.strftime('%d %b %Y')
            end_date = trip.end_date.strftime('%d %b %Y')
            formatted_date = f"From {start_date} to {end_date}"
        except Exception as e:
            formatted_date = "Invalid dates"
        trip_data = {
            'id': trip.id,
            'title': trip.title,
            'template_image': trip.template_image,
            'formatted_date': formatted_date,
            'duration': trip.duration,
            'seat_availability': trip.seat_availability
        }
        formatted_trips.append(trip_data)
    
    # Debugging: Print the formatted trips
    print(formatted_trips)
    
    return render_template('upcoming.html', trips=formatted_trips, profile_image=profile_image)


@app.route('/ongoing')
def ongoing():
    """Render the ongoing trips page."""
    update_trip_statuses()
    current_date = datetime.utcnow().date()
    trips = Trip.query.filter(Trip.start_date <= current_date, Trip.end_date >= current_date).all()
    formatted_trips = []
    username = session.get('username')
    user = User.query.filter_by(username=username).first() if username else None
    profile_image = user.profile_image if user else None

    for trip in trips:
        try:
            start_date = trip.start_date.strftime('%d %b %Y')
            end_date = trip.end_date.strftime('%d %b %Y')
            formatted_date = f"From {start_date} to {end_date}"
        except Exception as e:
            formatted_date = "Invalid dates"
        trip_data = {
            'id': trip.id,
            'title': trip.title,
            'template_image': trip.template_image,
            'formatted_date': formatted_date,
            'duration': trip.duration,
            'seat_availability': trip.seat_availability
        }
        formatted_trips.append(trip_data)
    return render_template('ongoing.html', trips=formatted_trips, profile_image=profile_image)


@app.route('/history')
def history():
    """Render the history trips page."""
    update_trip_statuses()
    current_date = datetime.utcnow().date()
    trips = Trip.query.filter(Trip.end_date < current_date).all()
    formatted_trips = []
    username = session.get('username')
    user = User.query.filter_by(username=username).first() if username else None
    profile_image = user.profile_image if user else None

    for trip in trips:
        try:
            start_date = trip.start_date.strftime('%d %b %Y')
            end_date = trip.end_date.strftime('%d %b %Y')
            formatted_date = f"From {start_date} to {end_date}"
        except Exception as e:
            formatted_date = "Invalid dates"
        trip_data = {
            'id': trip.id,
            'title': trip.title,
            'template_image': trip.template_image,
            'formatted_date': formatted_date,
            'duration': trip.duration,
            'seat_availability': trip.seat_availability
        }
        formatted_trips.append(trip_data)
    return render_template('history.html', trips=formatted_trips, profile_image=profile_image)


@app.route('/profile')
def profile():
    """Render the user's profile page."""
    if 'username' not in session:
        flash("Please login to access your profile.", "error")
        return redirect(url_for('signin'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found!", "error")
        return redirect(url_for('signin'))

    # Update booked trips to past trips if the end date has passed
    update_trip_statuses()

    # Fetch wishlist, booked, and past trips
    wishlist = user.wishlist
    booked_trips = user.booked_trips
    past_trips = user.past_trips

    # Ensure profile_image has a default value if None
    profile_image = user.profile_image if user.profile_image else 'uploads/default.png'

    return render_template('profile.html', user=user, wishlist=wishlist, booked_trips=booked_trips, past_trips=past_trips, profile_image=profile_image)
    
@app.route('/profile_edit')
def profile_edit():
    """Render the profile edit page."""
    if 'username' not in session:
        flash("Please login to access your profile.", "error")
        return redirect(url_for('signin'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    return render_template('profile_edit.html', user=user)


@app.route('/profile_update', methods=['POST'])
def profile_update():
    if 'username' not in session:
        flash("Please login to access your profile.", "error")
        return redirect(url_for('signin'))
    
    username = session['username']
    name = request.form['name']
    phone = request.form['phone']
    profile_image = request.files['profile_image']

    user = User.query.filter_by(username=username).first()
    
    if profile_image and allowed_file(profile_image.filename):
        filename = secure_filename(profile_image.filename)
        profile_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        profile_image.save(profile_image_path)
        user.profile_image = os.path.join('uploads', filename).replace("\\", "/")
    
    user.name = name
    user.phone = phone
    db.session.commit()
    flash('Profile updated successfully.', 'success')
    return redirect(url_for('profile'))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    ADMIN_USERNAME = "ram"
    ADMIN_PASSWORD_HASH = generate_password_hash("007") 
    
    """Handle admin login."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin'] = True
            flash("Login successful!", "success")
            return redirect(url_for('admin'))
        else:
            flash("Invalid admin credentials!", "error")

    return render_template('admin_login.html')


@app.route('/shop')
def shop():
    trips = Trip.query.filter_by(status='upcoming').all()
    products = Product.query.all()

    formatted_trips = []
    for trip in trips:
        try:
            start_date = trip.start_date.strftime('%d %b %Y')
            end_date = trip.end_date.strftime('%d %b %Y')
            formatted_date = f"From {start_date} to {end_date}"
        except Exception as e:
            formatted_date = "Invalid dates"
        
        trip_data = {
            'id': trip.id,
            'title': trip.title,
            'template_image': trip.template_image,
            'formatted_date': formatted_date,
            'duration': trip.duration,
            'seat_availability': trip.seat_availability
        }
        formatted_trips.append(trip_data)

    return render_template('shop.html', trips=formatted_trips, products=products)

    
@app.route('/buy_product/<int:product_id>', methods=['GET', 'POST'])
def buy_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        # Handle the purchase logic here
        flash('Product purchased successfully!', 'success')
        return redirect(url_for('shop'))
    return render_template('buy_product.html', product=product)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
   

    if not session.get('admin'):
        flash("Unauthorized access!", "error")
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        if 'add_trip' in request.form:
            # Handling adding a new trip
            title = request.form.get('title')
            place = request.form.get('place')
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            duration = (datetime.strptime(end_date_str, '%Y-%m-%d') - datetime.strptime(start_date_str, '%Y-%m-%d')).days
            template_image = request.files.get('template_image')
            template_details = request.form.get('template_details')
            view_trip_media = request.files.get('view_trip_media')
            view_paragraph = request.form.get('view_paragraph')
            things_to_do = request.form.get('things_to_do')
            gallery = request.files.getlist('gallery')
            price = request.form.get('price')
            details = request.form.get('details')
            seat_availability = request.form.get('seat_availability')
            points = request.form.get('points')

            current_date = date.today()
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            status = 'upcoming' if current_date < start_date else 'ongoing' if start_date <= current_date <= end_date else 'history'

            upload_folder = app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            def save_file(file):
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    return os.path.join('uploads', filename).replace("\\", "/")
                return None

            template_image_path = save_file(template_image)
            view_trip_media_path = save_file(view_trip_media)
            gallery_paths = [save_file(g) for g in gallery]
            gallery_paths_json = json.dumps(gallery_paths)  # Convert list to JSON string

            new_trip = Trip(title=title, place=place, start_date=start_date, end_date=end_date, duration=duration,
                            template_image=template_image_path, template_details=template_details,
                            view_trip_media=view_trip_media_path, view_paragraph=view_paragraph,
                            things_to_do=things_to_do, gallery=gallery_paths_json, price=price, details=details,
                            status=status, seat_availability=seat_availability, points=points)
            db.session.add(new_trip)
            db.session.commit()
            flash("Trip added successfully!", "success")

        elif 'add_product' in request.form:
            # Handling adding a new product
            product_name = request.form.get('product_name')
            product_image = request.files.get('product_image')
            product_details = request.form.get('product_details')
            product_price = request.form.get('product_price')
            product_points = request.form.get('product_points')

            if product_image and allowed_file(product_image.filename):
                filename = secure_filename(product_image.filename)
                product_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                product_image.save(product_image_path)

                new_product = Product(
                    name=product_name,
                    image=os.path.join('uploads', filename).replace("\\", "/"),
                    details=product_details,
                    price=product_price,
                    points=product_points
                )
                db.session.add(new_product)
                db.session.commit()
                flash("Product added successfully!", "success")

    trips = Trip.query.all()
    products = Product.query.all()
    return render_template('admin.html', trips=trips, products=products,json=json)

@app.route('/delete_product', methods=['POST'])
def delete_product():
    product_id = request.form['product_id']
    product = Product.query.get(product_id)
    
    # Find and delete related cart items
    related_cart_items = CartItem.query.filter_by(product_id=product_id).all()
    for item in related_cart_items:
        db.session.delete(item)
    
    db.session.delete(product)
    db.session.commit()
    flash('Product and related cart items deleted successfully!', 'success')
    return redirect(url_for('admin'))


@app.route('/store')
def store():
    username = session.get('username')
    user = User.query.filter_by(username=username).first() if username else None
    profile_image = user.profile_image if user  and user.profile_image else 'default.png'

    products = Product.query.all()
    return render_template('store.html', products=products, profile_image=profile_image)

@app.route('/delete_trip', methods=['POST'])
def delete_trip():
    trip_id = request.form['trip_id']
    trip = Trip.query.get(trip_id)
    
    if trip:
        db.session.delete(trip)
        db.session.commit()
        flash('Trip deleted successfully!', 'success')
    else:
        flash('Trip not found!', 'error')
    
    return redirect(url_for('admin'))

def save_file(file):
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    return os.path.join('uploads', filename).replace("\\", "/")

def save_files(files):
    filenames = []
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    for file in files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        filenames.append(os.path.join('uploads', filename).replace("\\", "/"))
    return filenames

import json

@app.route('/edit_trip', methods=['POST'])
def edit_trip():
    trip_id = request.form['trip_id']
    title = request.form['edit_title']
    place = request.form['edit_place']
    start_date_str = request.form['edit_start_date']
    end_date_str = request.form['edit_end_date']
    duration = (datetime.strptime(end_date_str, '%Y-%m-%d') - datetime.strptime(start_date_str, '%Y-%m-%d')).days
    template_details = request.form['edit_template_details']
    view_paragraph = request.form['edit_view_paragraph']
    things_to_do = request.form['edit_things_to_do']
    price = request.form['edit_price']
    details = request.form['edit_details']
    seat_availability = request.form['edit_seat_availability']
    points = request.form['edit_points']

    trip = Trip.query.get(trip_id)
    trip.title = title
    trip.place = place
    trip.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    trip.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    trip.duration = duration
    trip.template_details = template_details
    trip.view_paragraph = view_paragraph
    trip.things_to_do = things_to_do
    trip.price = price
    trip.details = details
    trip.seat_availability = seat_availability
    trip.points = points

    if 'edit_template_image' in request.files and request.files['edit_template_image'].filename != '':
        trip.template_image = save_file(request.files['edit_template_image'])
    if 'edit_view_trip_media' in request.files and request.files['edit_view_trip_media'].filename != '':
        trip.view_trip_media = save_file(request.files['edit_view_trip_media'])
    if 'edit_gallery' in request.files:
        gallery_files = request.files.getlist('edit_gallery')
        if gallery_files and gallery_files[0].filename != '':
            trip.gallery = json.dumps(save_files(gallery_files))  # Convert list to JSON string

    db.session.commit()
    flash('Trip updated successfully!', 'success')
    return redirect(url_for('admin'))


@app.route('/edit_product', methods=['POST'])
def edit_product():
    product_id = request.form['product_id']
    product_name = request.form['edit_product_name']
    product_details = request.form['edit_product_details']
    product_price = request.form['edit_product_price']
    product_image = request.files['edit_product_image']

    product = Product.query.get(product_id)
    if product_image and allowed_file(product_image.filename):
        filename = secure_filename(product_image.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        product_image.save(file_path)
        product.image = os.path.join('uploads', filename).replace("\\", "/")
    product.name = product_name
    product.details = product_details
    product.price = product_price
    db.session.commit()
    flash('Product updated successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/view_trip/<int:trip_id>')
def view_trip(trip_id):
    """Render the details of a specific trip."""
    trip = db.session.get(Trip, trip_id)  # Use Session.get() instead of Query.get()
    if trip:
        try:
            # Format the start and end dates for better display
            trip.start_date = trip.start_date.strftime('%d %b %Y')
            trip.end_date = trip.end_date.strftime('%d %b %Y')
        except Exception as e:
            pass
        # Ensure trip.gallery is a list of strings (file paths)
        if isinstance(trip.gallery, str):
            trip.gallery = json.loads(trip.gallery)
        return render_template('view_trip.html', trip=trip)
    else:
        flash('Trip not found.', 'error')
        return redirect(url_for('homepage'))
       

@app.route('/add_to_wishlist', methods=['POST'])
def add_to_wishlist():
    trip_id = request.form.get('trip_id')
    user = User.query.filter_by(username=session.get('username')).first()

    if trip_id and user:
        existing_item = db.session.query(wishlist_trips).filter_by(user_id=user.id, trip_id=trip_id).first()
        if not existing_item:
            new_wishlist_item = wishlist_trips.insert().values(user_id=user.id, trip_id=trip_id)
            db.session.execute(new_wishlist_item)
            user.status = 'wishlist'  # Update the status column
            db.session.commit()
            flash('Trip added to your wishlist!', 'success')
        else:
            flash('Trip already in your wishlist.', 'info')

    return redirect(url_for('profile'))

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'username' not in session:
        flash("Please login to add items to your cart.", "error")
        return redirect(url_for('signin'))

    product_id = request.form.get('product_id')
    user = User.query.filter_by(username=session.get('username')).first()

    if product_id and user:
        existing_item = CartItem.query.filter_by(user_id=user.id, product_id=product_id).first()
        if existing_item:
            existing_item.quantity += 1
        else:
            new_cart_item = CartItem(user_id=user.id, product_id=product_id)
            db.session.add(new_cart_item)
        db.session.commit()
        flash('Product added to your cart!', 'success')

    return redirect(url_for('store'))

@app.route('/logout')
def logout():
    """Handle user logout."""
    session.clear()
  
    return redirect(url_for('front_design'))


def calculate_points_and_loyalty(user, trip_cost, is_first_time, referred_friend, promotion_bonus):
    base_points = trip_cost // 5000
    
    bonus_points = 0
    if is_first_time:
        bonus_points += 50
    
    if user.loyalty_points is None:
        user.loyalty_points = 25
    
    total_points = base_points + bonus_points
    user.loyalty_points += total_points
    
    if user.loyalty_points >= 50000:
        user.loyalty_rating = 'Platinum'
    elif user.loyalty_points >= 2500:
        user.loyalty_rating = 'Gold'
    elif user.loyalty_points >= 1500:
        user.loyalty_rating = 'Silver'
    else:
        user.loyalty_rating = 'Bronze'
    print(f"Updated Loyalty Rating: {user.loyalty_rating}")
    db.session.commit()

@app.route('/payment_page')
def payment_page():
    trip_id = request.args.get('trip_id')
    trip = Trip.query.get(trip_id)
    if not trip:
        flash("Trip not found.", "error")
        return redirect(url_for('profile'))
    return render_template('payment.html', trip=trip)





@app.route('/process_payment', methods=['POST'])
def process_payment():
    if 'username' not in session:
        flash("Please login to proceed with payment.", "error")
        return redirect(url_for('signin'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    
    trip_id = request.form.get('trip_id')
    if not trip_id:
        flash("Trip ID is missing.", "error")
        return redirect(url_for('profile'))
    
    trip = Trip.query.get(trip_id)
    if not trip:
        flash("Trip not found.", "error")
        return redirect(url_for('profile'))
    
    trip_cost = trip.price
    
    is_first_time = True
    referred_friend = True
    promotion_bonus = True
    
    calculate_points_and_loyalty(user, trip_cost, is_first_time, referred_friend, promotion_bonus)
    
    trip.status = 'booked'
    
    with db.session.no_autoflush:
        # Remove trip from wishlist
        db.session.query(wishlist_trips).filter_by(user_id=user.id, trip_id=trip_id).delete()
        
        # Add trip to booked trips
        if trip not in user.booked_trips:
            user.booked_trips.append(trip)
    
    db.session.commit()
    
    flash("Payment successful! Your profile has been updated with loyalty points.", "success")
    return redirect(url_for('profile'))


@app.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    trip_id = request.form.get('trip_id')
    user_id = session.get('user_id')
    
    trip = Trip.query.get(trip_id)
    
    if trip and user_id:
        # Remove trip from Wishlist
        db.session.query(wishlist_trips).filter_by(trip_id=trip_id, user_id=user_id).delete()
        
        # Add trip to Booked Trips
        trip.status = 'booked'
        
        db.session.commit()
    
    return redirect(url_for('profile'))

def update_trip_statuses():
    """Update the status of trips based on the current date."""
    current_date = datetime.utcnow().date()
    
    # Update ongoing trips
    upcoming_trips = Trip.query.filter(Trip.start_date <= current_date, Trip.end_date >= current_date).all()
    for trip in upcoming_trips:
        trip.status = 'ongoing'
    
    # Update past trips
    ongoing_trips = Trip.query.filter(Trip.end_date < current_date).all()
    for trip in ongoing_trips:
        trip.status = 'history'
        
        # Move the trip from booked trips to past trips for each user
        users_with_trip = User.query.join(User.booked_trips).filter(Trip.id == trip.id).all()
        for user in users_with_trip:
            if trip in user.booked_trips:
                user.booked_trips.remove(trip)
            if trip not in user.past_trips:
                user.past_trips.append(trip)
    
    db.session.commit()

# filepath: /c:/Users/betar/Videos/admin2/app.py
@app.route('/submit_review', methods=['POST'])
def submit_review():
    if 'username' not in session:
        flash("Please login to submit a review.", "error")
        return redirect(url_for('signin'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    
    trip_id = request.form.get('trip_id')
    review = request.form.get('review')
    review_type = request.form.get('review_type')
    
    if review and review_type:
        stmt = past_trips.update().where(
            (past_trips.c.user_id == user.id) & (past_trips.c.trip_id == trip_id)
        ).values(review=review, review_type=review_type)
        db.session.execute(stmt)
        db.session.commit()
        flash("Review submitted successfully!", "success")
    else:
        flash("Review and review type cannot be empty.", "error")
    
    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True)