from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

users = {}  # sid -> username
chat_history = []  # [{username, text, timestamp}]

@app.route('/')
def index():
    return render_template('chat.html')

@socketio.on('set_username')
def set_username(username):
    sid = request.sid
    if username in [u for u in users.values()]:
        emit('username_error', 'Username already taken!')
        return
    users[sid] = username
    emit('chat_history', chat_history)
    emit('update_users', list(users.values()), broadcast=True)

@socketio.on('message')
def handle_message(msg):
    sid = request.sid
    if sid not in users:
        return
    user = users[sid]
    timestamp = datetime.now().strftime("%H:%M")

    # Handle ADMIN /clear
    if msg.strip() == "/clear" and user.upper() == "ADMIN":
        chat_history.clear()
        emit('refresh_page', broadcast=True)
        return

    data = {"username": user, "text": msg, "timestamp": timestamp}
    chat_history.append(data)
    if len(chat_history) > 200:
        chat_history.pop(0)
    emit('message', data, broadcast=True)

@socketio.on('disconnect')
def disconnect():
    sid = request.sid
    users.pop(sid, None)
    emit('update_users', list(users.values()), broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
