from pymongo import MongoClient

# создаем подключение к MongoDB
client = MongoClient('mongodb://localhost:27017/')

# выбираем базу данных
db = client['fun']

# выбираем коллекцию пользователей
users_collection = db['users']

# выбираем коллекцию комнат
rooms_collection = db['rooms']