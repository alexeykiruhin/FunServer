from flask import Blueprint
from flask_socketio import SocketIO, emit

socket_bp = Blueprint('socket_bp', __name__)
socketio = SocketIO()


@socket_bp.route('/game')
def index():
    return 'WebSocket Server is running'


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    # Здесь вы можете выполнять дополнительные действия при подключении клиента


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    # Здесь вы можете выполнять дополнительные действия при отключении клиента


@socketio.on('event')
def handle_event(data):
    print('Received event:', data)
    # Здесь вы можете обрабатывать полученные данные или выполнить нужные действия


# Инициализация SocketIO с вашим приложением Flask
def init_socketio(app):
    socketio.init_app(app)
