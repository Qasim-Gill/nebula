from flask import Flask, render_template, redirect, url_for, session, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
# for creating login decorators
from functools import wraps

app = Flask(__name__)
app.secret_key = 'qasim'
# Configuring the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nebula.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('show_login'))  # Redirect to the login page
        return f(*args, **kwargs)
    return decorated_function


# Initializing the database
db = SQLAlchemy(app)

# Defining the User model
class UserData(db.Model):
    __tablename__ = 'users_data'
    
    id = db.Column(db.Integer, primary_key=True)  # Auto-incrementing user ID
    first_name = db.Column(db.String(100), nullable=False)  # First name
    last_name = db.Column(db.String(100), nullable=False)  # Last name
    email = db.Column(db.String(120), unique=True, nullable=False)  # Email
    password = db.Column(db.String(100), nullable=False)  # Password
    city = db.Column(db.String(100), nullable=False)  # city
    state = db.Column(db.String(100), nullable=False)  # state
    country = db.Column(db.String(100), nullable=False)  # country

    # Relationship to FarmData
    farm_data = db.relationship('FarmData', backref='user', lazy=True)
    
    # Adding the __repr__ method for better debugging
    def __repr__(self):
        return f'<UserData {self.id} - {self.first_name} {self.last_name} - {self.email}>'
    
# Defining the FarmData model
class FarmData(db.Model):
    __tablename__ = 'farm_data'

    id = db.Column(db.Integer, primary_key=True)  # Auto-incrementing ID
    crop_type = db.Column(db.String(100), nullable=False)  # Type of crop
    plant_date = db.Column(db.Date, nullable=False)  # Planting date
    field_size = db.Column(db.Float, nullable=False)  # Field size in hectares
    irrigation_method = db.Column(db.String(50), nullable=False)  # Irrigation method
    last_watered = db.Column(db.Date, nullable=True)  # Last watering date
    soil_type = db.Column(db.String(50), nullable=False)  # Soil type
    pest_signs = db.Column(db.String(3), nullable=False)  # Whether pests were noticed (Yes/No)
    pest_control_method = db.Column(db.String(50), nullable=False)  # Pest control method
    weather_issues = db.Column(db.String(200), nullable=True)  # Weather-related issues (e.g., drought, flooding)
    crop_rotation_practice = db.Column(db.String(50), nullable=False)  # Crop rotation practice
    field_location = db.Column(db.String(255), nullable=False)  # Field location as address
    coordinates = db.Column(db.String(300), nullable=False)  # Coordinates of the field

    # Foreign key to associate farm data with a user
    user_id = db.Column(db.Integer, db.ForeignKey('users_data.id'), nullable=False)

    def __repr__(self):
        return f'<FarmData {self.id} - {self.crop_type}>'


@app.route('/', methods=['GET', 'POST'])
def show_signup():
    # return 'Alhamdulilah'
    if 'user_id' not in session:
        session.clear()  # This will clear all session data
    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        password = request.form['password']

        # Check if email already exists
        existing_user = db.session.execute(db.select(UserData).filter_by(email=email)).scalar_one_or_none()
        if existing_user:
            return render_template('signup.html', data="Email already exists. Please use a different email.")
        
         # Create a new UserData instance
        new_user = UserData(first_name=first_name, last_name=last_name, email=email, city=city, state=state, country=country, password=password)

        # Add new user to the session and commit to the database
        try:
            db.session.add(new_user)
            db.session.commit()
            return render_template("login.html")
            # return redirect(url_for('hello_world'))  # Redirect to avoid resubmitting form on refresh
        except Exception as e:
            return f"An error occurred: {e}"
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def show_login():
    if 'user_id' in session:
        session.clear()  # This will clear all session data
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        # Query to check user credentials
        try:
            query = db.session.query(UserData).filter_by(email=email, password=password).first()
            if query:  # If user exists
                session['user_id'] = query.id
                return redirect(url_for("home", id=query.id))
            else:
                return render_template('login.html', data="Invalid Credentials")
        except Exception as e:
            return render_template('login.html', data="An error occurred. Please try again.")
    
    return render_template('login.html')


@app.route('/home/<int:id>', methods=['GET'])
@login_required
def home(id):
    # Check if the logged-in user's id matches the id in the URL
    if 'user_id' in session and session['user_id'] == id:
        user = db.get_or_404(UserData, id)
        # Get forms (farm data) associated with the user
        forms_data = db.session.query(FarmData).filter_by(user_id=id).all()
        return render_template('home.html', user=user, forms_data=forms_data)
    else:
        # If session user_id doesn't match, redirect to login
        return redirect(url_for('show_login'))



@app.route('/add_form/<int:id>', methods=['GET', 'POST'])
@login_required
def save_form(id):
    if request.method == "POST":
        # Get user ID from session (assuming you've set it after user login)
        user_id = session.get('user_id')

        # Extract form data using correct field names
        last_watered = request.form['last_watered']
        plant_date = request.form['plant_date']
        plant_date = datetime.strptime(plant_date, '%Y-%m-%d').date()
        last_watered = datetime.strptime(last_watered, '%Y-%m-%d').date() if last_watered else None
        crop_type = request.form['crop_type']
        field_size = request.form['field_size']
        irrigation_method = request.form['irrigation_method']
        soil_type = request.form['soil_type']
        pest_signs = request.form['pest_signs']
        pest_control_method = request.form['pest_control_method']
        
        # Collect weather issues from checkboxes
        # weather_issues = []
        # if request.form.get('weather_issues'):
        #     # Check if the checkbox for each issue is checked
        #     if 'Drought' in request.form:
        #         weather_issues.append('Drought')
        #     if 'Flooding' in request.form:
        #         weather_issues.append('Flooding')
        #     if 'Pests' in request.form:
        #         weather_issues.append('Pests')
        #     if 'Temperature Changes' in request.form:
        #         weather_issues.append('Temperature Changes')
        
        # Join weather issues into a single string
        # weather_issues_str = ', '.join(weather_issues)
        weather_issues_str = request.form['weather_issues[]']

        crop_rotation_practice = request.form['crop_rotation_practice']
        field_location = request.form['field_location']
        coordinates = request.form['coordinates']

        # Create a new FarmData instance
        new_farm_data = FarmData(
            crop_type=crop_type,
            plant_date=plant_date,
            field_size=field_size,
            irrigation_method=irrigation_method,
            last_watered=last_watered,
            soil_type=soil_type,
            pest_signs=pest_signs,
            pest_control_method=pest_control_method,
            weather_issues=weather_issues_str,
            crop_rotation_practice=crop_rotation_practice,
            field_location=field_location,
            coordinates=coordinates,
            user_id=user_id  # Associate with the logged-in user
        )

        # Add new farm data to the session and commit to the database
        try:
            db.session.add(new_farm_data)
            db.session.commit()
            return redirect(url_for('show_forms', id=session['user_id']))  # Redirect to a success page or another route
        except Exception as e:
            return f"An error occurred while saving data: {e}"
        

    # Check if the logged-in user's id matches the id in the URL
    if 'user_id' in session and session['user_id'] == id:
        user = db.get_or_404(UserData, id)
        return render_template('add_form.html', user=user)
    else:
        # If session user_id doesn't match, redirect to login
        return redirect(url_for('show_login'))
    
    
@app.route('/update_form/<int:form_id>', methods=['GET', 'POST'])
@login_required
def update_form(form_id):
    # Fetch the form data by its ID
    form_data = db.get_or_404(FarmData, form_id)
    user = db.get_or_404(UserData, session['user_id'])
    
    if request.method == 'POST':
        # Get user ID from session (assuming you've set it after user login)
        user_id = session.get('user_id')

        # Extract form data using correct field names
        last_watered = request.form['last_watered']
        plant_date = request.form['plant_date']
        plant_date = datetime.strptime(plant_date, '%Y-%m-%d').date()
        last_watered = datetime.strptime(last_watered, '%Y-%m-%d').date() if last_watered else None
        crop_type = request.form['crop_type']
        field_size = request.form['field_size']
        irrigation_method = request.form['irrigation_method']
        soil_type = request.form['soil_type']
        pest_signs = request.form['pest_signs']
        pest_control_method = request.form['pest_control_method']
        
        # Collect weather issues from checkboxes
        weather_issues = []
        if request.form.get('weather_issues'):
            # Check if the checkbox for each issue is checked
            if 'Drought' in request.form:
                weather_issues.append('Drought')
            if 'Flooding' in request.form:
                weather_issues.append('Flooding')
            if 'Pests' in request.form:
                weather_issues.append('Pests')
            if 'Temperature Changes' in request.form:
                weather_issues.append('Temperature Changes')
        
        # Join weather issues into a single string
        weather_issues_str = ', '.join(weather_issues)

        crop_rotation_practice = request.form['crop_rotation_practice']
        field_location = request.form['field_location']
        coordinates = request.form['coordinates']

        # Update the existing FarmData instance
        form_data.crop_type = crop_type
        form_data.plant_date = plant_date
        form_data.field_size = field_size
        form_data.irrigation_method = irrigation_method
        form_data.last_watered = last_watered
        form_data.soil_type = soil_type
        form_data.pest_signs = pest_signs
        form_data.pest_control_method = pest_control_method
        form_data.weather_issues = weather_issues_str
        form_data.crop_rotation_practice = crop_rotation_practice
        form_data.field_location = field_location
        form_data.coordinates = coordinates
        
        # Commit the changes to the database
        db.session.commit()
        return redirect(url_for('show_forms', id=session['user_id']))

    # Pass the form_data to the update_form.html
    return render_template('update_form.html', user=user, form_data=form_data)


@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def update_profile(user_id):
    # Fetch the form data by its ID
    user = db.get_or_404(UserData, user_id)
    
    if request.method == 'POST':
        # Get user ID from session (assuming you've set it after user login)
        user_id = session.get('user_id')

        # Extract form data using correct field names
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        password = request.form['password']

        # Update the existing FarmData instance
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.city = city
        user.state = state
        user.country = country
        user.password = password

        # Commit the changes to the database
        db.session.commit()
        return redirect(url_for('home', id=session['user_id']))

    # Pass the form_data to the update_form.html
    return render_template('profile.html', user=user)


@app.route('/delete_form/<int:form_id>', methods=['GET', 'POST'])
@login_required
def delete_form(form_id):
    # Fetch the form data by its ID
    form_data = db.get_or_404(FarmData, form_id)
    db.session.delete(form_data)
    db.session.commit()  # Commit the changes
    return redirect(url_for('show_forms', id=session['user_id']))



@app.route('/forms/<int:id>', methods=['GET'])
@login_required
def show_forms(id):
    # Check if the logged-in user's id matches the id in the URL
    if 'user_id' in session and session['user_id'] == id:
        user = db.get_or_404(UserData, id)
        # Get forms (farm data) associated with the user
        forms_data = db.session.query(FarmData).filter_by(user_id=id).all()
        # Render the forms page with both user and forms data
        return render_template('forms.html', user=user, forms_data=forms_data)
    else:
        # If session user_id doesn't match, redirect to login
        return redirect(url_for('show_login'))


@app.route('/form_det/<int:id>', methods=['GET'])
@login_required
def form_detail(id):
    # Check if the logged-in user's id matches the id in the URL
    if 'user_id' in session:
        user = db.get_or_404(UserData, session['user_id'])
        # Get forms (farm data) associated with the user
        form_data = db.get_or_404(FarmData, id)
        # Render the forms page with both user and forms data
        return render_template('form_det.html', user=user, form_data=form_data)
    else:
        # If session user_id doesn't match, redirect to login
        return redirect(url_for('show_login'))
    

@app.route('/tasks/<int:id>', methods=['GET'])
@login_required
def show_tasks(id):
    # Check if the logged-in user's id matches the id in the URL
    if 'user_id' in session and session['user_id'] == id:
        user = db.get_or_404(UserData, id)
        # Get forms (farm data) associated with the user
        forms_data = db.session.query(FarmData).filter_by(user_id=id).all()
        # Render the forms page with both user and forms data
        return render_template('tasks.html', user=user, forms_data=forms_data)
    else:
        # If session user_id doesn't match, redirect to login
        return redirect(url_for('show_login'))
    

@app.route('/events/<int:id>', methods=['GET'])
@login_required
def show_events(id):
    # Check if the logged-in user's id matches the id in the URL
    if 'user_id' in session and session['user_id'] == id:
        user = db.get_or_404(UserData, id)
        # Get forms (farm data) associated with the user
        forms_data = db.session.query(FarmData).filter_by(user_id=id).all()
        # Render the forms page with both user and forms data
        return render_template('events.html', user=user, forms_data=forms_data)
    else:
        # If session user_id doesn't match, redirect to login
        return redirect(url_for('show_login'))

@app.route('/disease_checker', methods=['GET'])
@login_required
def disease_checker():
    # Check if the logged-in user's id matches the id in the URL
    if 'user_id' in session:
        user = db.get_or_404(UserData, session['user_id'])
        # Get forms (farm data) associated with the user
        forms_data = db.session.query(FarmData).filter_by(user_id=user.id).all()
        # Render the forms page with both user and forms data
        return render_template('disease_checker.html', user=user, forms_data=forms_data)
    else:
        # If session user_id doesn't match, redirect to login
        return redirect(url_for('show_login'))
    
@app.route('/plant_care', methods=['GET'])
@login_required
def plant_care():
    # Check if the logged-in user's id matches the id in the URL
    if 'user_id' in session:
        user = db.get_or_404(UserData, session['user_id'])
        # Get forms (farm data) associated with the user
        forms_data = db.session.query(FarmData).filter_by(user_id=user.id).all()
        # Render the forms page with both user and forms data
        return render_template('plant_care.html', user=user, forms_data=forms_data)
    else:
        # If session user_id doesn't match, redirect to login
        return redirect(url_for('show_login'))


if __name__ == "__main__":
    # Create the database and the table
    with app.app_context():
        db.create_all()
    app.run(debug=True)