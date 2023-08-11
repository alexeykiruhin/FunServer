from flask import Flask, request, make_response
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_socketio import SocketIO, emit
from threading import Lock
from datetime import datetime
from api import api
from api.views.game import api_game
from api.views.login import api_login
from api.views.refresh import api_refresh
from api.views.sockets import socket_bp
import jwt
from bson import ObjectId

from mongo import users_collection, rooms_collection

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

# регистрируем blueprint
app.register_blueprint(api, url_prefix='/api')
# регистрируем blueprint
app.register_blueprint(api_game, url_prefix='/api')
# регистрируем blueprint Login
app.register_blueprint(api_login, url_prefix='/api')
# регистрируем blueprint Refresh
app.register_blueprint(api_refresh, url_prefix='/api')

# задаем секретный ключ для подписи токена
app.config['JWT_SECRET_KEY'] = '23sa3501080X'
# Ожидаем токенs в куках и хедерах
app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers']
# Имя куки, в которой ожидается refresh-токен
app.config['JWT_REFRESH_COOKIE_NAME'] = 'token'


# jwt = JWTManager(app)  # инициализируем объект JWTManager


class Room:
    def __init__(self, name, id, max_users):
        self.name = name
        self.id = len(rooms) + 1
        self.users = []
        self.max_users = max_users
        self.add_user(id)
        self.stage = 0

    def __str__(self):
        return f'Room: name - {self.name}, id - {self.id}, max_users - {self.max_users}, stage - {self.stage}'

    def add_user(self, id):
        self.users.append(id)

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


def token_to_id():
    token = request.args.get('token')
    out = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    return out


# Функция для проверки токена и его валидности
def verify_token_and_get_user():
    # Проверяем, есть ли токен в WebSocket-соединении
    token = request.args.get('token')
    # Декодируем JWT токен с помощью PyJWT
    decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    # decoded_token.identity - _id user
    if not token:
        print('Not token')
        return None

    try:
        # Валидация и декодирование токена
        string_id = decoded_token["identity"]
        object_id = ObjectId(string_id)
        user = users_collection.find_one({'_id': object_id})
        print(f'TRUE - {user["username"]}')
        return True
    except Exception as e:
        # Если возникла ошибка при декодировании или валидации токена,
        # можно здесь обработать соответствующую логику или вернуть ошибку
        print(e)
        return None


@app.route('/')
def index():
    response = {'users': len(users)}
    return response


#
#
# @app.route('/list_rooms')
# def list_rooms():
#     response = {'rooms': rooms}
#     print(response)
#     return response


"""
Decorator for connect
"""


@socketio.on('connect')
def connect():
    token = request.args.get('token')
    print(f'token connect - {token}')
    user_identity = token_to_id()['identity']
    print(f'user_identity - {user_identity}')
    print(f'sid - {request.sid}')
    # из бд достаём актуальный стейдж
    stage = users_collection.find_one({'_id': ObjectId(user_identity)}, {'_id': 0, 'stage': 1, 'username': 1})
    print(f'stage - {stage["stage"]}')
    socketio.emit('stage', stage, room=request.sid)
    if stage["stage"] == 'game_stage_1':
        # надо получитьюзеров из базы

        # получаем юзеров в данной комнате
        # connect_players = rooms_collection.find_one({'_id': add.inserted_id}, {'players': 1, '_id': 0})

        # операция агрегации
        pipeline = [
            # Находим комнату, в которой находится пользователь
            {
                '$match': {
                    # 'players': user_identity  # тут айди это строка
                    'players': ObjectId(user_identity)
                }
            },
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'players',
                    'foreignField': '_id',
                    'as': 'pl'
                }
            },
            # исключение поля "_id" из документа автора
            {
                '$project': {
                    'name': 1,
                    'pl.username': 1,
                    '_id': 0,
                }
            }
        ]

        # # получаю список имен юзеров
        # user_names = [doc['pl'] for doc in result][0]
        # un = [n['username'] for n in user_names]
        # print(un)

        result = rooms_collection.aggregate(pipeline)
        # получаем название комнаты
        # room_name = [r for r in result]
        # получаю список имен юзеров
        user_names = [doc for doc in result]
        # un = [n['username'] for n in user_names]
        print(user_names[0]['name'])
        print([un['username'] for un in user_names[0]['pl']])
        players = [un['username'] for un in user_names[0]['pl']]
        name = user_names[0]['name']
        # connectPlayers = ['vasja', 'kolja']
        socketio.emit('await_players', {'users': players}, room=request.sid)
        # нужно тут при релоадинге еще отправить название комнаты
        print('await true')


@socketio.on('create')
def create(data):
    # print(data)
    user_identity = token_to_id()['identity']
    print(f'user_identity - {user_identity}')
    room = Room(data['name'], user_identity, data['players'])
    print(f'room - {room}')

    # Записываем в переменную стадию для юзера
    stage = 'game_stage_1'

    # создаем новый документ в коллекции rooms
    new_room = {
        # "id": current_id,
        "name": data['name'],
        "max_players": data['players'],
        # "players": [user_identity],
        "players": [ObjectId(user_identity)],
        "stage": 0
    }
    # добавляем в бд
    add = rooms_collection.insert_one(new_room)
    print(f'type - {type(add.inserted_id)}')
    room_id = str(add.inserted_id)
    # name = data['name']
    # # rooms[name] = room
    # rooms.append({'name': data['name'], 'id': request.sid, 'players': data['players'], 'users': room.users})
    # room.start()
    # # вернуть списко ников из списка айди
    # nick_list = [users_collection.find_one({'_id': ObjectId(u)}, {'username': 1, '_id': 0}) for u in room.users]

    users_collection.update_one({'_id': ObjectId(user_identity)}, {'$set': {'stage': stage}})
    socketio.emit('create', {'status': 'OK', 'stage': stage, 'room_id': room_id, 'name': data['name']},
                  room=request.sid)
    # получаем юзеров в данной комнате
    # connect_players = rooms_collection.find_one({'_id': add.inserted_id}, {'players': 1, '_id': 0})

    pipeline = [
        {
            '$match': {
                '_id': add.inserted_id
            }
        },
        {
            '$unwind': '$players'
        },
        {
            '$lookup': {
                'from': 'users',
                'localField': 'players',
                'foreignField': '_id',
                'as': 'player_info'
            }
        },
        {
            '$project': {
                '_id': 0,
                'player_name': '$player_info.username'
            }
        }
    ]

    result = rooms_collection.aggregate(pipeline)

    user_names = [doc['player_name'] for doc in result][0]
    print(user_names)
    socketio.emit('await_players', {'users': user_names}, room=request.sid)
    socketio.emit('get_list_rooms', {'rooms': rooms})


@socketio.on('exit_room')  # выход из комнаты
def exit_room():
    user_identity = token_to_id()['identity']
    print(f'exit_room')
    stage = 'menu'
    rooms_collection.update_one({'_id': ObjectId(user_identity)}, {'$set': {'stage': stage}})


@socketio.on('connect_room')  # коннект к комнате после её создания
def connect():
    token = request.args.get('token')
    print(f'connect_room - {request}')
    socketio.emit('connect_room', {'rooms': rooms})


@socketio.on('get_list_rooms')
def get_list_rooms():
    user_identity = verify_token_and_get_user()
    print(f'user_identity - {user_identity}')
    if user_identity:
        # Ваша логика обработки, основанная на идентификаторе пользователя (user_identity)
        response = {'rooms': rooms}
        emit('get_list_rooms', response)
    else:
        # Если токен недействителен или отсутствует, отправьте соответствующее сообщение или выполните необходимые
        # действия
        emit('error', {'message': f'Invalid or missing token - {user_identity}'}, status=401)


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
    # users.remove(request.sid)
    print(f'All users {len(users)}')


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
