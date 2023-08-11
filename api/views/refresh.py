# удаление комментария
import datetime

from flask import Blueprint, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, create_refresh_token
from mongo import users_collection

api_refresh = Blueprint('api_refresh', __name__)


# переменные из файла mongo.py
# from mongo import comments_collection


@api_refresh.route('/refresh', methods=['GET'])
@jwt_required(refresh=True)
def refresh():
    # получаем рефреш токен из куки
    # token = request.cookies.get('token')
    # print(f"cookie  -  {request.cookies.get('token')}")

    # получаем id юзера из токена
    current_user = get_jwt_identity()
    # print(f'user - {current_user}')

    # получаем данные юзера
    user = users_collection.find_one({'id': current_user}, {'_id': 0, 'password': 0, 'statusText': 0, 'rating': 0})
    # print(f'user - {user["refresh_token"]}')

    # !!!! из-за 2х запросов подряд  к рефрешу токен не успевает обновится в куках и кука призодит со старым токеном
    # а в бд уже новый проверка токена с токеном из бд if token != user['refresh_token']: return {'message': 'No
    # valid token'}

    # после проверки токена удаляю его из объекта юзера, перед ответом на клиент
    del user['refresh_token']

    new_access_token = create_access_token(
        identity=current_user, expires_delta=datetime.timedelta(seconds=5))
    new_refresh_token = create_refresh_token(
        identity=current_user, expires_delta=datetime.timedelta(days=30))
    print('новые токены сгенерированы')

    # обновляем токен в бд
    users_collection.update_one({'id': current_user}, {'$set': {'refresh_token': new_refresh_token}})
    # тут использую make_response т.к. set_cookie метод объекта response без него получаю ошибку 'dict' object has no
    # attribute 'set_cookie' в остальных ответах фласк сам преобразует в json
    response = make_response(
        {'user_obj': user, 'isAuth': True, 'access_token': new_access_token})
    response.set_cookie('token', new_refresh_token, httponly=True,
                        max_age=30 * 24 * 60 * 60, samesite='None', secure=True, path='/api')
    return response
