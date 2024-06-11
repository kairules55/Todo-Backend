# Todo Application

This is a simple todo app with CRUD, Reminder, Notification, Recuurance functionality

# Installation 

```
git clone https://github.com/kairules55/Todo-Plivo
```

# Frontend Setup

```
cd frontend
npm install
npm start
```

Setup a REACT_APP_API_ENDPOINT which is your backend url

# Backend setup

1. Create a virtual env using venv
```
python3 -m venv env
source env/bin/activate
```

2. Install dependency
```
pip install -r requirements.txt
```


3. Add Twillio ENV Variables

```
os.getenv('TWILIO_ACCOUNT_SID')
os.getenv('TWILIO_AUTH_TOKEN')
```

4. Run App
```
python3 app.py
```

Please contact me, if you don't recieve the sms notifcation, might need to whitelist your number
Please contact for TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN