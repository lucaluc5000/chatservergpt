from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

# --- Data storage ---
users = {}  # { sid: {username, avatar, msgCount} }
chat_history = []  # [{username, avatar, text, timestamp}]

# --- Routes ---
@app.route('/')
def index():
    return render_template('chat.html')

# --- Socket Events ---

@socketio.on('set_username')
def handle_set_username(data):
    sid = request.sid
    if any(u['username'] == data['username'] for u in users.values()):
        emit('username_error', 'Username already taken!')
        return
    users[sid] = {
        'username': data['username'],
        'avatar': data.get('avatar', ''),
        'msgCount': 0
    }
    emit('chat_history', chat_history)
    emit('update_users', list(users.values()), broadcast=True)

@socketio.on('message')
def handle_message(msg):
    sid = request.sid
    if sid not in users: return
    users[sid]['msgCount'] += 1
    message_data = {
        'username': users[sid]['username'],
        'avatar': users[sid]['avatar'],
        'text': msg,
        'timestamp': datetime.now().strftime('%H:%M')
    }
    chat_history.append(message_data)
    if len(chat_history) > 200: chat_history.pop(0)
    emit('message', message_data, broadcast=True)

    if msg.strip() == '/clear' and users[sid]['username'].upper() == 'ADMIN':
        chat_history.clear()
        emit('refresh_page', broadcast=True)

@socketio.on('typing')
def handle_typing(data):
    sid = request.sid
    if sid not in users: return
    emit('user_typing', {'username': users[sid]['username'], 'typing': data}, broadcast=True, include_self=False)

@socketio.on('admin_update_profile')
def handle_admin_update(data):
    sid = request.sid
    if sid not in users or users[sid]['username'].upper() != 'ADMIN':
        return
    target_name = data['target']
    for u_sid, u in users.items():
        if u['username'] == target_name:
            u['avatar'] = data.get('avatar', u['avatar'])
            emit('profile_update', {'avatar': u['avatar']}, to=u_sid)
            break

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    users.pop(sid, None)
    emit('update_users', list(users.values()), broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
