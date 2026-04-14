from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "✅ 효원 학식 봇이 24시간 정상 작동 중입니다!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()