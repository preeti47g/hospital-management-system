
from datetime import datetime
from flask import Flask, render_template, flash, redirect, session, url_for, request
from forms import SignupForm, LoginForm
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash



app = Flask(__name__)
app.config["SECRET_KEY"] = "007"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app_user.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

db = SQLAlchemy(app)

class PatientFile(db.Model):
    __tablename__ = "patient_file"

    patient_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    gender = db.Column(db.String(), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Foreign key linking to the DoctorFile
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_file.doctor_id'), nullable=True)

    # Relationship with treatment (one patient can have many treatments)
    treatment = db.relationship("TreatmentFile", backref="patient", lazy=True)

class TreatmentFile(db.Model):
    __tablename__ = "treatment_file"

    treatment_id = db.Column(db.Integer, primary_key=True)
    diagnosis = db.Column(db.String(200), nullable=False)  # Corrected 'diagonis' to 'diagnosis'
    report_path = db.Column(db.String(200), nullable=False)

    patient_id = db.Column(db.Integer, db.ForeignKey('patient_file.patient_id'), nullable=False)

class AdminFile(db.Model):
    __tablename__ = "admin_file"

    admin_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)  # Changed to String
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)

class DoctorFile(db.Model):
    __tablename__ = "doctor_file"

    doctor_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.Integer, unique=True, nullable=False)
    specialist = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Relationship to patients (One doctor can have many patients)
    patients = db.relationship("PatientFile", backref="doctor", lazy=True)


class AppointmentFile(db.Model):
    __tablename__ = "appointment_file"

    appointment_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient_file.patient_id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_file.doctor_id'), nullable=False)
    appointment_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.String(200), nullable=True)

    # Relationships
    patient = db.relationship("PatientFile", backref="appointments", lazy=True)
    doctor = db.relationship("DoctorFile", backref="appointments", lazy=True)





@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/sign", methods=["GET", "POST"])
def sign():
    form = SignupForm()  
    if form.validate_on_submit():
        # Check if the email is already registered
        existing_user = PatientFile.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already registered. Please log in.", "danger")
            return redirect(url_for('log'))
        
        # Hash the password and create a new user
        hashed_password = generate_password_hash(form.password.data)
        new_user = PatientFile(name=form.name.data, email=form.email.data, age=form.age.data, gender = form.gender.data, password=hashed_password)

        # Add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        flash("Sign up Successful! You can now log in.", "success")
        return redirect(url_for("log"))  # Redirect to login after signup

    return render_template("LOG-SIGN/signup.html", form=form)




@app.route('/login', methods=["GET", "POST"])
def log():
    form = LoginForm()
    if form.validate_on_submit():
        # Check the email in all user types
        admin = AdminFile.query.filter_by(email=form.email.data).first()
        patient = PatientFile.query.filter_by(email=form.email.data).first()
        doctor = DoctorFile.query.filter_by(email=form.email.data).first()

        # Check for Admin Login
        if admin and check_password_hash(admin.password, form.password.data):
            session['user_id'] = admin.admin_id
            session['user_type'] = "administrator"
            admin.last_login = datetime.now()
            db.session.commit()  # Save last_login

            flash("Login Successful!", "success")
            return redirect(url_for("administrator"))

        # Check for Patient Login
        elif patient and check_password_hash(patient.password, form.password.data):
            session['user_id'] = patient.patient_id
            session['user_type'] = "patient"

            flash("Login Successful!", "success")
            return redirect(url_for("pat", patient_id = patient.patient_id))

        # Check for Doctor Login
        elif doctor and check_password_hash(doctor.password, form.password.data):
            session['user_id'] = doctor.doctor_id
            session['user_type'] = "doctor"

            flash("Login Successful!", "success")
            return redirect(url_for("doc", doctor_id = doctor.doctor_id))

        # Invalid Credentials
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template('LOG-SIGN/login.html', form=form)





@app.route("/forgetPassword")
def forget():
    return render_template("forgetpassword.html")

@app.route("/administrator")
def administrator():
    return render_template("ADMIN/administrator.html")




@app.route("/doctor/<int:doctor_id>")
def doc(doctor_id):
    doctor = DoctorFile.query.get_or_404(doctor_id)
    appointments = AppointmentFile.query.filter_by(doctor_id=doctor_id).all()
    return render_template("DOCTOR/doctor.html", doctor=doctor, appointments=appointments)

@app.route("/doctor/<int:doctor_id>/profile")
def doc_profile(doctor_id):
    doctor = DoctorFile.query.get_or_404(doctor_id)
    return render_template('DOCTOR/doctor_profile.html', doctor = doctor)

@app.route("/doctor/<int:doctor_id>/patients")
def doctorsPatients(doctor_id):
    appointments = AppointmentFile.query.filter_by(doctor_id=doctor_id).all()
    return render_template("DOCTOR/doctorspatients.html", appointments=appointments)

@app.route('/appointment_form', methods=['GET'])
def appointment_form():
    return render_template('DOCTOR/appointment.html')

@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    if request.method == "POST":
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')
        appointment_time = request.form.get('appointment_time')
        description = request.form.get('description')

        # Create an appointment object
        new_appointment = AppointmentFile(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_time=datetime.strptime(appointment_time, '%Y-%m-%dT%H:%M'),
            description=description
        )

        # Add to the database
        db.session.add(new_appointment)
        db.session.commit()

        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('pat')) 

@app.route("/allPatients")
def allPatients():
    patients = PatientFile.query.all()
    return render_template("DOCTOR/totalPatient.html", patients=patients)


@app.route("/receptionist")
def reception():
    return render_template("receptionist.html")






@app.route("/patient/<int:patient_id>")
def pat(patient_id):
    patient = PatientFile.query.get_or_404(patient_id)
    return render_template("patient.html", patient= patient)






@app.route("/addAdmin", methods=["GET", "POST"])
def addAdmin():
    if request.method == "POST":
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        role = request.form.get('role', '')
        phone = request.form.get('phone', '')
        is_active = bool(request.form.get('is_active', '0'))  # Default to inactive

        # Validate required fields
        if not (name and email and password and role and phone):
            flash("All fields are required.", "danger")
            return redirect(url_for('addAdmin'))

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Add new admin to the database
        new_admin = AdminFile(
            name=name,
            email=email,
            password=hashed_password,
            role=role,
            phone=int(phone),
            is_active=is_active,
            last_login=datetime.utcnow()
        )
        try:
            db.session.add(new_admin)
            db.session.commit()
            flash("Admin added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    # Retrieve all admins to display on the page
    admins = AdminFile.query.all()
    return render_template("ADMIN/add_admin.html", admins=admins)


@app.route('/manageAdmin', methods=['GET', 'POST'])
def manage_admin():
    if request.method == 'POST':
        action = request.form['action']

        if action.startswith('edit_'):
            admin_id = int(action.split('_')[1])
            admin = AdminFile.query.get(admin_id)

            # Update admin details
            admin.name = request.form[f'name_{admin_id}']
            admin.email = request.form[f'email_{admin_id}']
            admin.role = request.form[f'role_{admin_id}']
            admin.phone = request.form[f'phone_{admin_id}']
            admin.is_active = bool(int(request.form[f'is_active_{admin_id}']))

            db.session.commit()
            flash('Admin details updated successfully!', 'success')

        elif action.startswith('delete_'):
            admin_id = int(action.split('_')[1])
            admin = AdminFile.query.get(admin_id)

            # Delete the selected admin
            db.session.delete(admin)
            db.session.commit()
            flash('Admin deleted successfully!', 'success')

        return redirect('/manageAdmin')

    # GET request: Fetch all admins from the database
    admins = AdminFile.query.all()
    return render_template('Admin/admin_management.html', admins=admins)






@app.route('/addDoctor', methods=['GET', 'POST'])
def add_doctor():
    if request.method == 'POST':
        # Get data from the form
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        specialist = request.form['specialist']


        hashed_password = generate_password_hash(password)

        # Create a new doctor record
        new_doctor = DoctorFile(
            name=name,
            email=email,
            password=hashed_password,
            phone=phone,
            specialist=specialist
        )
        db.session.add(new_doctor)
        db.session.commit()
        flash('Doctor added successfully!', 'success')

        return redirect('/addDoctor')

    # Retrieve all doctors from the database
    doctors = DoctorFile.query.all()
    return render_template('ADMIN/add_doctor.html', doctors=doctors)



@app.route('/manageDoctor', methods=['GET', 'POST'])
def manage_doctor():
    if request.method == 'POST':
        # Get action from the form submission
        action = request.form['action']

        if action.startswith('edit_'):
            doctor_id = int(action.split('_')[1])
            doctor = DoctorFile.query.get(doctor_id)

            # Update the doctor information
            doctor.name = request.form[f'name_{doctor_id}']
            doctor.email = request.form[f'email_{doctor_id}']
            doctor.phone = request.form[f'phone_{doctor_id}']
            doctor.specialist = request.form[f'specialist_{doctor_id}']

            db.session.commit()
            flash('Doctor information updated successfully!', 'success')

        elif action.startswith('delete_'):
            doctor_id = int(action.split('_')[1])
            doctor = DoctorFile.query.get(doctor_id)

            # Delete the doctor from the database
            db.session.delete(doctor)
            db.session.commit()
            flash('Doctor deleted successfully!', 'success')

        return redirect('/manageDoctor')

    # GET request: Fetch all doctors from the database
    doctors = DoctorFile.query.all()
    return render_template('ADMIN/doctor_management.html', doctors=doctors)



if __name__ == "__main__":
    app.run(debug=True)
