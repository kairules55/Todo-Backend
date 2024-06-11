import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from twilio.rest import Client

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

# Configure Twilio client
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Define Task model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(120))
    dueDate = db.Column(db.DateTime, nullable=False)
    priority = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    recurring = db.Column(db.String(20))
    reminder = db.Column(db.DateTime, nullable=False)
    to = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'dueDate': self.dueDate.strftime('%Y-%m-%d') if self.dueDate else None,
            'recurring': self.recurring,
            'status': self.status,
            'reminder': self.reminder.strftime('%Y-%m-%d') if self.reminder else None,
            'to': self.to
        }

with app.app_context():
    db.create_all()

def notify(task):
    print(f"Reminder for task {task.title}")

def scheduled_task_creation(task_data):
    if 'dueDate' in task_data:
        task_data['dueDate'] = datetime.strptime(task_data['dueDate'], '%Y-%m-%d')
    task = Task(**task_data)
    db.session.add(task)
    db.session.commit()

def send_sms_reminder(task, request_data):
    message = client.messages.create(
        body=f"Reminder: {task['title']}",
        from_='+12566671053',
        to=request_data['to'] 
    )
    return message.sid

def notify(task):
    send_sms_reminder(task)

@app.route('/send-reminder', methods=['POST'])
def send_reminder():
    data = request.get_json()
    reminder = data.get('reminder')
    title = data.get('title')
    to = data.get('to')
    if reminder and title and to:
        sid = send_sms_reminder({'title': title}, {'to': to})
        return jsonify({'message': 'Reminder sent', 'sid': sid}), 200

    return jsonify({'error': 'Missing required data'}), 400

@app.route('/tasks', methods=['POST'])
def create_task():
    task_data = request.get_json()
    if 'dueDate' in task_data:
        task_data['dueDate'] = datetime.strptime(task_data['dueDate'], '%Y-%m-%d')
    if 'reminder' in task_data:
        task_data['reminder'] = datetime.strptime(task_data['reminder'], '%Y-%m-%d')
    task = Task(**task_data)
    db.session.add(task)
    db.session.commit()
    if 'recurring' in task_data:
        interval = {'daily': 1, 'weekly': 7, 'monthly': 30}[task.recurring]
        scheduler.add_job(scheduled_task_creation, 'interval', days=interval, args=[task_data])
    if 'reminder' in task_data:
        scheduler.add_job(notify, 'date', run_date=task_data['reminder'], args=[task])
    return jsonify(task_data), 201

@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    return jsonify([task.to_dict() for task in tasks]), 200

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task_data = request.get_json()
    if 'dueDate' in task_data:
        task_data['dueDate'] = datetime.strptime(task_data['dueDate'], '%Y-%m-%d')
    if 'reminder' in task_data:
        task_data['reminder'] = datetime.strptime(task_data['reminder'], '%Y-%m-%d')
    task = Task.query.get(task_id)
    if 'recurring' in task_data and task.recurring != task_data['recurring']:
        for job in scheduler.get_jobs():
            if job.args[0]['id'] == task_id:
                job.remove()
        if task_data['recurring']:
            interval = {'daily': 1, 'weekly': 7, 'monthly': 30}[task_data['recurring']]
            scheduler.add_job(create_task, 'interval', days=interval, args=[task_data])
    Task.query.filter_by(id=task_id).update(task_data)
    db.session.commit()
    return jsonify(task_data), 200

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    Task.query.filter_by(id=task_id).delete()
    db.session.commit()
    return '', 204

# Run the app
if __name__ == '__main__':
    app.run(debug=True)