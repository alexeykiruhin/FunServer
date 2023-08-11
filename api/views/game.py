# удаление комментария
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

api_game = Blueprint('api_game', __name__)


# переменные из файла mongo.py
# from mongo import comments_collection


@api_game.route('/game', methods=['GET', 'OPTIONS'])
def game():
    # получаем данные из запроса

    # добавить проверку токена, если юзер вышел то нужно запретить отправку нового статуса

    data = request.data
    print(data)

    response = {'Connect': True}

    return response
