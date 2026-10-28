from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Hostel Security Surveillance System is Running!</h1><p>Code successfully hosted on Vercel.</p>"

if __name__ == '__main__':
    app.run(debug=True)
