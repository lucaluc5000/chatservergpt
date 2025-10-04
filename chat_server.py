import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

users = {}
chat_history = []  # store messages

@app.route('/')
def index():
    return render_template('chat.html')

# When a new user sets username
@socketio.on('set_username')
def handle_username(username):
    users[request.sid] = username
    emit("message", f"🔵 {username} joined the chat", broadcast=True)
    # Send chat history to the new user
    for msg in chat_history:
        emit("message", msg)

# Handle incoming chat messages
@socketio.on('message')
def handle_message(msg):
    username = users.get(request.sid, "Anonymous")
    
    # ADMIN command to clear chat
    if username == "ADMIN" and msg.strip().lower() == "/clear":
        chat_history.clear()
        emit("message", "⚠️ Chat history cleared by ADMIN", broadcast=True)
        return
    
    # Normal message
    text = f"{username}: {msg}"
    chat_history.append(text)  # save message
    emit("message", text, broadcast=True)

# Handle user disconnect
@socketio.on('disconnect')
def handle_disconnect():
    username = users.pop(request.sid, "Anonymous")
    emit("message", f"🔴 {username} left the chat", broadcast=True)

if __name__ == '__main__':
    import eventlet
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
