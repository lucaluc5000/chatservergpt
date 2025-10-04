import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# store usernames by session id
users = {}

@app.route('/')
def index():
    return render_template('chat.html')

@socketio.on('set_username')
def handle_username(username):
    users[request.sid] = username
    emit("message", f"🔵 {username} joined the chat", broadcast=True)

@socketio.on('message')
def handle_message(msg):
    username = users.get(request.sid, "Anonymous")
    text = f"{username}: {msg}"
    print(text)
    emit("message", text, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    username = users.pop(request.sid, "Anonymous")
    emit("message", f"🔴 {username} left the chat", broadcast=True)

if __name__ == '__main__':
    import eventlet
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
