from flask import Flask, request, make_response
from flask_socketio import SocketIO, emit
from threading import Lock
from datetime import datetime

"""
Background Thread
"""
# thread = None
# thread_lock = Lock()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'q23sa'
socketio = SocketIO(app, cors_allowed_origins='*')

rooms = []
users = []


class Room:
    def __init__(self, name, sid, max_users):
        self.name = name
        self.id = len(rooms) + 1
        self.users = []
        self.max_users = max_users
        self.add_user(sid)
        self.stage = 0

    def __str__(self):
        return f'Room: name - {self.name}, id - {self.id}, max_users - {self.max_users}, stage - {self.stage}'

    def add_user(self, sid):
        self.users.append(sid)

    def start(self):
        if len(self.users) < self.max_users:
            print('malo')


class User:
    def __init__(self, sid):
        self.name = 'Default_Name'
        self.sid = sid

    def set_name(self, name):
        self.name = name


"""
Serve root index file
"""


@app.route('/')
def index():
    response = {'users': len(users)}
    return response


@app.route('/list_rooms')
def list_rooms():
    response = {'rooms': rooms}
    print(response)
    return response


"""
Decorator for connect
"""


@socketio.on('connect')
def connect():
    user = User(request.sid)
    users.append(user)
    # print('Client connected')
    # print(f'All users {len(users)}')


@socketio.on('create')
def create(data):
    # print(data)
    room = Room(data['name'], request.sid, data['players'])
    name = data['name']
    # rooms[name] = room
    rooms.append({'name': data['name'], 'id': request.sid, 'players': data['players']})
    room.start()
    print(rooms)
    # for i in rooms:
    #     print(i)
    # print([{'name': p.name, 'id': p.id} for i, p in rooms])
    # rooms.append({'name': room.name, 'id': room.id})
    # print('HOOLKAA')
    # emit('get_list_rooms', {'rooms': rooms})
    # print(rooms)
    socketio.emit('create', {'rooms': rooms})
    socketio.emit('get_list_rooms', {'rooms': rooms})


@socketio.on('get_list_rooms')
def get_list_rooms():
    # print(rooms)
    response = {'rooms': rooms}
    socketio.emit("get_list_rooms", response)


@socketio.on('set_name')
def set_name(name):
    print(f'name - {name}')
    print(f'request.sid - {request.sid}')


"""
Game stages
"""


@socketio.on('game_stage_1')
def game_stage_1():
    response = {'rooms': rooms}
    emit("get_list_rooms", response)


"""
Decorator for disconnect
"""


@socketio.on('disconnect')
def disconnect():
    print('Client disconnected', request.sid)


"""
Get current date time
"""


def get_current_datetime():
    now = datetime.now()
    return now.strftime("%m/%d/%Y %H:%M:%S")


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


if __name__ == '__main__':
    socketio.run(app, debug=True, host='127.0.0.1')
