from asyncio import events
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import fhirpy
import asyncio

app = Flask(__name__)
app.secret_key = "key"

def parse_date(str_date: str):
    return datetime.strptime(str_date, '%Y-%m-%d')

def parse_date_time(str_date_time: str):
    return datetime.strptime(str_date_time, '%Y-%m-%dT%H:%M:%S')

def validate_date(str_date: str):
    try:
        datetime.strptime(str_date, '%Y-%m-%d')
    except ValueError:
        return False
    return True

class Patient():
    def __init__(self, patient) -> None:
        self.id = patient.get('id')
        self.prefix = patient.get_by_path('name.0.prefix.0')
        self.name = \
            f"{patient.get_by_path('name.0.family')} {patient.get_by_path('name.0.given.0')}"
        self.gender = patient.get_by_path('gender')
        self.birthDate = patient.get_by_path('birthDate')
        self.birth_date = parse_date(self.birthDate)
        self.pretty_birth_date = self.birth_date.strftime('%d %b %Y')

        # self.events = ['badanie tomografem', 'nastawianie kości','wypadek samochodowy']
    
    async def get_med_events(self):
        fetched_observations = await client.resources('Observation').search(patient=self.id).fetch()
        fetched_med_requests = await client.resources('MedicationRequest').search(patient=self.id).fetch()
        observations = [Observation(obs) for obs in fetched_observations]
        med_requests = [MedicationRequest(req) for req in fetched_med_requests]
        med_events = observations + med_requests
        med_events.sort(key=lambda x: x.date_time)
        return med_events
    
class Observation():
    def __init__(self, observation) -> None:
        self.event_id = \
            f"{observation.get_by_path('resourceType')} {observation.get('id')}"
        self.dateTime = observation.get_by_path('effectiveDateTime')[:-6]
        self.date_time = parse_date_time(self.dateTime)
        self.hour = self.date_time.strftime('%X')
        self.date = self.date_time.strftime('%A, %d %b %Y')
        self.display = \
            observation.get_by_path('code.coding.0.display')
        self.value = get_observation_value(observation)
    
def get_observation_value(observation) -> str:
    x = observation.get_by_path('valueQuantity.value')
    if x is None:
        # blood pressure has another display directory
        x_prefix = 'component.0.code' \
            if observation.get_by_path('code.coding.0.code') == '55284-4' \
            else 'valueCodeableConcept'
        x = observation.get_by_path(x_prefix + '.coding.0.display')
    else:
        x = str(round(x, 3))
        unit = str(observation.get_by_path('valueQuantity.unit'))
        if unit != "{score}":
            x = f"{x} {unit}" 
    return x

class MedicationRequest():
    def __init__(self, med_request) -> None:
        self.event_id = \
            f"{med_request.get_by_path('resourceType')} {med_request.get('id')}"
        self.dateTime = str(med_request.get_by_path('authoredOn'))[:-6]
        self.date_time = parse_date_time(self.dateTime)
        self.hour = self.date_time.strftime('%X')
        self.date = self.date_time.strftime('%A, %d %b %Y')
        self.display = \
            med_request.get_by_path('medicationCodeableConcept.coding.0.display')
        self.value = ""


client = fhirpy.AsyncFHIRClient(
        'http://localhost:8080/baseR4/',
        # 'http://hapi.fhir.org/baseR4',
        authorization='Bearer TOKEN'
    )

patients_list = []

@app.route('/')
async def index():

    patients = await client.resources('Patient').fetch()

    patients_list = [Patient(patient) for patient in patients]
    # for patient in patients:
    #     patients_list.append(Patient(patient))

    return render_template("index.html", patients=patients_list)

@app.route('/details/<id>/', methods = ['GET', 'POST'])
async def details(id):
    fetched_patient = await client.resources('Patient').search(_id=[id]).first()
    patient = Patient(fetched_patient)
    med_events = await patient.get_med_events()
    med_events.sort(key=lambda x: x.date_time, reverse=True)

    if request.method == 'POST':
        requestInputFlags = \
            validate_date(request.form['startDate']), \
            validate_date(request.form['endDate'])

        if requestInputFlags[0] or requestInputFlags[1] :
            start_date = \
                parse_date(request.form['startDate']) if requestInputFlags[0] \
                else parse_date("1970-01-01")
            
            end_date = \
                parse_date(request.form['endDate']) if requestInputFlags[1] \
                else parse_date("2100-01-01")

            for event in med_events[:]:
                if event.date_time < start_date or event.date_time > end_date:
                    med_events.remove(event)

    return render_template("details.html", patient=patient, med_events=med_events)

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

if __name__ == "__main__":
    app.run(debug=True)

