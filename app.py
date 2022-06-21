from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import fhirpy
import asyncio

app = Flask(__name__)
app.secret_key = "key"

def parse_admission_date(str_date: str):
    date_int_tuple = tuple(map(int, str_date.split(sep="-")))
    return datetime(*date_int_tuple)

class Patient():
    def __init__(self, patient):
        self.id = patient.get('id')
        self.name = patient.get_by_path('name.0.family') + ' ' + patient.get_by_path('name.0.given.0')
        self.gender = "male"
        self.birthDate = "2018-6-1"

        self.admission_date = parse_admission_date("2018-6-1")
        self.admissionDate = self.admission_date.date()
        self.events = ['badanie tomografem', 'nastawianie kości','wypadek samochodowy']

    def set_admission_date(self, date_str: str):
        self.admission_date = parse_admission_date(date_str)
        self.admissionDate = self.admission_date.date()

# def fhir_to_patient(patient):
#     return Patient(patient.get('id'),
#             patient.get_by_path('name.0.family') + ' ' + patient.get_by_path('name.0.given.0'),
#              "2018-6-1", "y", ['wywiad', 'diagnostyka', 'badanie rtg'])  

# patientargs = ("0", "Alex", "2018-6-1", "y", ['wywiad', 'diagnostyka', 'badanie rtg']), \
#     ("1", "Piotr", "2018-1-13", "y", ['badanie tomografem', 'nastawianie kości','wypadek samochodowy']), \
#     ("2", "Maciej", "2018-3-3", "y", ['zgon', 'podanie środków przeciwpromiennych']), \
#     ("3", "Stachu", "2018-11-15", "y", ['operacja kolana', 'wymiana insuliny']) 

# database = [Patient(*args) for args in patientargs]

client = fhirpy.AsyncFHIRClient(
        'http://localhost:8080/baseR4/',
        authorization='Bearer TOKEN'
    )

patients_list = []

@app.route('/')
async def index():

    patients = await client.resources('Patient').limit(10).fetch()

    patients_list = []
    for patient in patients:
        patients_list.append(Patient(patient))
    return render_template("index.html", patients=patients_list)

@app.route('/insert', methods=['POST'])
def insert():
    # doesnt work
    if request.method == 'POST':

        name = request.form['name']
        admission_date = (request.form['admissionDate'])
        y = request.form['y']

        database.append(Patient(str(max([int(x.id) for x in database])+1), name, admission_date, y))

        flash("Patient created!")
        
        return redirect(url_for('index'))

@app.route('/update', methods = ['GET', 'POST'])
def update():
    # doesnt work
    if request.method == 'POST':
        patient = [x for x in database if x.id == request.form.get('id')][0]
        patient.name = request.form['name']
        patient.set_admission_date(request.form['admissionDate'])
        patient.y = request.form['y']

        flash("Patient updated!")
        return redirect(url_for('index'))

@app.route('/delete/<id>/', methods = ['GET', 'POST'])
def delete(id):
    # doesnt work
    patient = [x for x in database if x.id == id][0]
    database.remove(patient)

    flash(f"Patient {patient.name} deleted!")
    return redirect(url_for('index'))

@app.route('/details/<id>/')
async def details(id):
    # app.logger.info(f"[LOGS] types: {type(patients_list[0])}, {type(id)}")
    # patient = [x for x in patients_list if x.id == id][0]
    patients = await client.resources('Patient').search(_id=[id]).fetch_all()
    return render_template("details.html", patient=Patient(patients[0]))

if __name__ == "__main__":
    app.run(debug=True)

