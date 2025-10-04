import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# user session_id -> info
users = {}
# list of messages
messages = []

# banned usernames (optional, for later kick/ban)
banned_users = set()

@app.route('/')
def index():
    return render_template('chat.html')

# Set or update username + avatar/color
@socketio.on('set_username')
def handle_username(data):
    username = data.get('username')
    avatar = data.get('avatar')
    color = data.get('color', '#1976d2')

    # Check for uniqueness
    if username in [u['username'] for u in users.values() if u['username'] != username]:
        emit('username_error', 'Username already taken.')
        return

    old_user = users.get(request.sid)
    users[request.sid] = {
        'username': username,
        'avatar': avatar,
        'color': color
    }

    if old_user:
        emit('system_message', f"🔄 {old_user['username']} changed username to {username}", broadcast=True)
    else:
        emit('system_message', f"🔵 {username} joined the chat", broadcast=True)
        # send chat history to new user
        for msg in messages:
            emit('message', msg)

    # update online users for all clients
    emit('update_users', list(u['username'] for u in users.values()), broadcast=True)

# Handle typing events
@socketio.on('typing')
def handle_typing(is_typing):
    username = users.get(request.sid, {}).get('username', 'Anonymous')
    emit('user_typing', {'username': username, 'typing': is_typing}, broadcast=True, include_self=False)

# Handle chat messages
@socketio.on('message')
def handle_message(text):
    user = users.get(request.sid)
    if not user:
        return

    username = user['username']

    # ADMIN clear command
    if username == "ADMIN" and text.strip().lower() == "/clear":
        messages.clear()
        emit('system_message', '⚠️ Chat history cleared by ADMIN', broadcast=True)
        emit('refresh_page', {}, broadcast=True)  # trigger refresh
        return

    timestamp = datetime.now().strftime('%H:%M')
    msg = {
        'id': len(messages) + 1,
        'username': username,
        'avatar': user.get('avatar', ''),
        'color': user.get('color', '#1976d2'),
        'text': text,
        'timestamp': timestamp
    }
    messages.append(msg)
    emit('message', msg, broadcast=True)

# Handle disconnect
@socketio.on('disconnect')
def handle_disconnect():
    user = users.pop(request.sid, None)
    if user:
        emit('system_message', f"🔴 {user['username']} left the chat", broadcast=True)
        emit('update_users', list(u['username'] for u in users.values()), broadcast=True)

if __name__ == '__main__':
    import eventlet
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
