# удаление комментария
import datetime
from flask import Blueprint, request, make_response, current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from mongo import users_collection
import jwt

api_login = Blueprint('api_login', __name__)


# переменные из файла mongo.py
# from mongo import comments_collection


@api_login.route('/login', methods=['POST'])
def login():
    # получаем данные из запроса
    data = request.json
    print(f'login - {data}')
    # ищем пользователя в базе данных
    user = users_collection.find_one({'username': data['username']}, {
        '_id': 1, 'statusText': 0, 'rating': 0, 'refresh_token': 0})
    # user = users_collection.find_one({'username': data['username']}, {
    #     '_id': 0, 'statusText': 0, 'rating': 0, 'refresh_token': 0})
    if user is None:
        print(f'Пользователя с логином {data["username"]} не существует')
        return {'messageError': f'Пользователя с логином {data["username"]} не существует'}, 401
    # проверяем пароль
    if user['password'] == data['password']:
        # # создаем токен, вынести в отдельную функцию
        # access_token = create_access_token(
        #     identity=str(user['_id']), expires_delta=datetime.timedelta(seconds=5))
        # refresh_token = create_refresh_token(
        #     identity=str(user['_id']), expires_delta=datetime.timedelta(days=30))

        # Создаем JWT токен с помощью PyJWT
        payload = {'identity': str(user['_id'])}
        access_token = jwt.encode(payload, current_app.config['SECRET_KEY'])
        # добавляем токен в бд
        users_collection.update_one({'username': data['username']}, {
            '$set': {'access_token': access_token}})
        # # добавляем токен в бд
        # users_collection.update_one({'username': data['username']}, {
        #     '$set': {'refresh_token': refresh_token}})
        # после проверки пароля удаляю его из объекта юзера, перед ответом на клиент
        del user['password']
        del user['_id']

        response = make_response({'user_obj': user, 'isAuth': True, 'stage': 'menu',
                                  'access_token': access_token})
        # response = make_response({'status': 'OK'}) response.set_cookie('refresh_token', refresh_token,
        # httponly=True, max_age=30*24*60*60, samesite='None', secure=True, path='/api')
        response.set_cookie('token', access_token, httponly=True, max_age=30 * 24 * 60 * 60,
                            samesite='None', secure=True, path='/api')  # попробовать секьюр флаг поменять
        return response
    # возвращаем ошибку
    print('Неверный пароль')
    return {'messageError': 'Неверный пароль'}, 401
