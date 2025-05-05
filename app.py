from flask import Flask, redirect, request, render_template, url_for, session, jsonify, flash
from datetime import datetime
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import os

import cloudinary
import cloudinary.uploader


app = Flask(__name__)

# MySQL Database Configuration
app.config['MYSQL_HOST'] = 'centerbeam.proxy.rlwy.net'
app.config['MYSQL_PORT'] = 17390
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'pLBBUhSWjtMhnDkngBdXHufGuOvOatYA'
app.config['MYSQL_DB'] = 'railway'


mysql = MySQL(app)

# Define your image upload folder path
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'somethingfishy'

# --------------------------------------------------------------------------------------------------



cloudinary.config( 
    cloud_name = "dz2oijnjv", 
    api_key = "954271683457226", 
    api_secret = "BCxhShdmjPoaeJ24MbRaec6Gu2I",  # Replace with actual secret
    secure=True
)



# --------------------------------------------------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''  # initialize message

    if request.method == 'POST':
        name = request.form.get("username")
        password = request.form.get("password")

        try:
            cursor = mysql.connection.cursor()  # Use dictionary=True for readable keys
            query = "SELECT * FROM login WHERE username = %s AND password = %s"
            cursor.execute(query, (name, password))
            user = cursor.fetchall()
            cursor.close()

            if user:
                session['user'] = name
                session['userid'] = user[0][0]  # Assuming your table has 'id' as user ID
                return redirect('/home')
            else:
                message = 'Invalid credentials'

        except Exception as e:
            message = f'Database error: {str(e)}'

        return render_template('login.html', message=message)

    return render_template('login.html', message=message)


# --------------------------------------------------------------------------------------------------


@app.route('/home')
def home():
	if 'user' in session:
		return render_template('index.html')
	else:
		return redirect('/login')

# --------------------------------------------------------------------------------------------------

@app.route('/add-data', methods=['GET', 'POST'])
def add_data():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        # Get form values
        state = request.form.get("state")
        district = request.form.get("district")
        spot = request.form.get("spot")

        stay_names = request.form.getlist("stay_name[]")
        stay_phones = request.form.getlist("stay_phone[]")


        image_file = request.files.get("image")
        image_filename = None

        if image_file and image_file.filename != "":
            try:
                upload_result = cloudinary.uploader.upload(image_file)
                image_filename = upload_result['secure_url']  # Store this in DB
            except Exception as e:
                return render_template('index.html', message=f"Image upload failed: {str(e)}")


        try:
            cursor = mysql.connection.cursor()

            now = datetime.now()
            cursor.execute(
                "INSERT INTO data (user_id, date_time, state, district, spot) VALUES (%s, %s, %s, %s, %s)",
                (str(session['userid']), now, state, district, spot)
            )
            data_id = cursor.lastrowid

            for name, phone in zip(stay_names, stay_phones):
                cursor.execute(
                    "INSERT INTO accommodation (data_id, accommodation_name, phone_number) VALUES (%s, %s, %s)",
                    (data_id, name, phone)
                )

            if image_filename:
                cursor.execute(
                    "INSERT INTO images (data_id, image_path) VALUES (%s, %s)",
                    (data_id, image_filename)
                )

            mysql.connection.commit()
            cursor.close()

            # REDIRECT to avoid resubmission
            return redirect(url_for('add_data', success='true'))

        except Exception as e:
            mysql.connection.rollback()
            return render_template('index.html', message=str(e))

    # GET method here
    message = None
    if request.args.get('success') == 'true':
        message = "Data Added ✅"
    return render_template('index.html', message=message)



# --------------------------------------------------------------------------------------------------


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()  # Removes all session data
    return redirect('/login')


if __name__ == '__main__':
    app.run(ssl_context='adhoc', port=5000)