import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Пароль администратора
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'qwerty123')

# База данных
DATABASE_PATH = 'parking_bot.db'

# Настройки
ADMIN_SESSION_HOURS = 24  # Длительность админ-сессии в часах
NOTIFICATION_REMINDER_HOURS = 1  # За сколько часов напоминать о бронировании
PAGINATION_SIZE = 10  # Количество элементов на странице

# Банки для выбора
BANKS_LIST = [
    "Сбербанк",
    "Тинькофф",
    "ВТБ",
    "Альфа-Банк",
    "Газпромбанк",
    "Райффайзенбанк",
    "Росбанк",
    "Открытие",
    "МКБ",
    "Другой"
]

# Роли пользователей
ROLE_CUSTOMER = 'customer'
ROLE_SUPPLIER = 'supplier'
ROLE_ADMIN = 'admin'

# Статусы бронирования
STATUS_PENDING = 'pending'
STATUS_CONFIRMED = 'confirmed'
STATUS_CANCELLED = 'cancelled'
STATUS_COMPLETED = 'completed'
