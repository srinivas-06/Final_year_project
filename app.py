#update

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import pickle
#import mysql.connector
import pymysql
pymysql.install_as_MySQLdb()

from sklearn.preprocessing import StandardScaler
from flask_mail import Mail, Message
import smtplib
import csv
import io

app = Flask(__name__)
app.secret_key = '123'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Use your gitemail provider's SMTP server'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'srinivas003scode@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'djbsopibfkgtecwe'   # Replace with your app-specific password
app.config['MAIL_DEFAULT_SENDER'] = 'hellbuddy.06@gmail.com'

mail = Mail(app)


# MySQL Database connection
db = pymysql.connect(
    host="localhost",
    user="root",
    password="Seenu@003",
    database="prediction_data"
)
cursor = db.cursor()

# Dummy user credentials
USER_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin123'
}

scaler = pickle.load(open("scaler.pkl", "rb"))
model = pickle.load(open("svm_model.pkl", "rb"))

@app.route('/')
def log_home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == USER_CREDENTIALS['username'] and password == USER_CREDENTIALS['password']:
            flash('Login successful!', 'success')
            return redirect(url_for('home_main'))
        else:
            flash('Invalid credentials, please try again.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/home')
def home_main():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict_datapoint():
    result = ""

    if request.method == 'POST':
        patient_Id = int(request.form.get("patient_Id"))
        p_name = str(request.form.get("p_name"))
        email = str(request.form.get("email"))  # Ensure email input exists in the form
        Pregnancies = int(request.form.get("Pregnancies"))
        Glucose = float(request.form.get('Glucose'))
        BloodPressure = float(request.form.get('BloodPressure'))
        SkinThickness = float(request.form.get('SkinThickness'))
        Insulin = float(request.form.get('Insulin'))
        BMI = float(request.form.get('BMI'))
        DiabetesPedigreeFunction = float(request.form.get('DiabetesPedigreeFunction'))
        Age = float(request.form.get('Age'))

        new_data = scaler.transform([[Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age]])
        predict = model.predict(new_data)

        if predict[0] == 1:
            result = 'Diabetic'

            # Email content
            subject = "Diabetes Prediction Result"
            body = f"""
            Dear {p_name},

            Your recent diabetes prediction test indicates that you may have diabetes. 
            Please consult a healthcare professional for further assessment.

            Recommendations:
            - Monitor your blood sugar levels regularly.
            - Maintain a balanced, healthy diet.
            - Engage in regular physical activity.
            - Consult a doctor for a personalized treatment plan.

            Stay healthy,
            Diabetes Prediction Team
            """

            # Send Email
            try:
                msg = Message(subject, recipients=[email], body=body)
                mail.send(msg)
                print("Email sent successfully!")
            except Exception as e:
                print(f"Error sending email: {e}")

        else:
            result = 'Non-Diabetic'

        # Insert data into MySQL database
        query = """
        INSERT INTO predictions (patient_Id, p_name, email, Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age, result)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (patient_Id, p_name, email, Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age, result)
        cursor.execute(query, values)
        db.commit()

        # Pass data to result page  
        return render_template(
            'result.html',
            result=result,
            patient_Id=patient_Id,
            p_name=p_name,
            email=email,
            Pregnancies=Pregnancies,
            Glucose=Glucose,
            BloodPressure=BloodPressure,
            SkinThickness=SkinThickness,
            Insulin=Insulin,
            BMI=BMI,
            DiabetesPedigreeFunction=DiabetesPedigreeFunction,
            Age=Age
        )

    else:
        return render_template('predict.html')

@app.route('/result')
def result():
    return render_template('result.html')

@app.route('/report')
def report():
    cursor.execute("SELECT * FROM predictions")
    columns = [col[0] for col in cursor.description]  # Get column names
    predictions = [dict(zip(columns, row)) for row in cursor.fetchall()]  # Convert to dictionaries
    return render_template('report.html', predictions=predictions)


@app.route('/download/<int:patient_Id>')
def download_report(patient_Id):
    cursor.execute("SELECT * FROM predictions WHERE patient_Id = %s", (patient_Id,))
    prediction = cursor.fetchone()

    if not prediction:
        return "Record not found", 404  # More user-friendly error

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Patient ID', 'Patient Name','email', 'Pregnancies', 'Glucose', 'Blood Pressure', 'Skin Thickness', 'Insulin', 'BMI', 'Diabetes Pedigree Function', 'Age', 'Result'])
    writer.writerow(prediction)

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'report_{patient_Id}.csv'
    )
'''
    else:
        return "Record not found", 404
'''
'''
@app.route('/delete/<int:patient_Id>')
def delete_record(patient_Id):
    cursor.execute("DELETE FROM predictions WHERE patient_Id = %s", (patient_Id,))
    db.commit()
    return redirect(url_for('report'))
'''
@app.route('/delete/<int:patient_Id>')
def delete_record(patient_Id):
    cursor.execute("SELECT * FROM predictions WHERE patient_Id = %s", (patient_Id,))
    record = cursor.fetchone()

    if not record:
        return "Record not found", 404  # Handle case when patient does not exist

    cursor.execute("DELETE FROM predictions WHERE patient_Id = %s", (patient_Id,))
    db.commit()
    return redirect(url_for('report'))


if __name__ == '__main__':
    app.run(debug=True)