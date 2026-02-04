# 👨‍💻 Руководство для Разработчиков

## 🗄️ Работа с Базой Данных

### Примеры использования Database API

```python
from database import Database
from datetime import datetime, timedelta

# Инициализация
db = Database()
await db.init_db()
```

### Пользователи

```python
# Добавить пользователя
user_id = await db.add_user(
    telegram_id=123456789,
    username="john_doe",
    full_name="Иван Иванов",
    phone="+7 900 123 45 67",
    card_number="1234567812345678",
    bank="Сбербанк"
)

# Получить пользователя
user = await db.get_user_by_telegram_id(123456789)
print(user['full_name'])  # "Иван Иванов"

# Обновить роль
await db.update_user_role(123456789, 'supplier')

# Заблокировать пользователя
await db.block_user(user_id)

# Разблокировать
await db.unblock_user(user_id)

# Получить всех пользователей с пагинацией
users = await db.get_all_users(offset=0, limit=10)

# Количество пользователей
count = await db.get_users_count()
```

### Парковочные места

```python
# Добавить парковочное место
spot_id = await db.add_parking_spot(
    supplier_id=1,
    spot_number="A12",
    price_per_hour=150.0,
    address="ул. Ленина, 10",
    description="У входа",
    is_partial_allowed=True
)

# Получить места поставщика
spots = await db.get_spots_by_supplier(supplier_id=1)

# Получить конкретное место
spot = await db.get_parking_spot(spot_id)

# Обновить цену
await db.update_spot_price(spot_id, 200.0)

# Скрыть/показать место
await db.toggle_spot_visibility(spot_id)

# Все места
all_spots = await db.get_all_parking_spots()
```

### Доступность мест

```python
# Добавить период доступности
start = datetime(2024, 12, 25, 9, 0)
end = datetime(2024, 12, 25, 18, 0)

availability_id = await db.add_availability(
    spot_id=1,
    start_time=start,
    end_time=end
)

# Получить доступные слоты на дату
date = datetime(2024, 12, 25)
slots = await db.get_available_slots(date)

# Проверить доступность слота
is_available = await db.check_slot_availability(
    spot_id=1,
    start_time=datetime(2024, 12, 25, 10, 0),
    end_time=datetime(2024, 12, 25, 12, 0)
)

# Забронировать слот
await db.book_slot(
    availability_id=1,
    customer_id=2,
    booking_id=1
)
```

### Бронирования

```python
# Создать бронирование
booking_id = await db.create_booking(
    customer_id=2,
    spot_id=1,
    start_time=datetime(2024, 12, 25, 10, 0),
    end_time=datetime(2024, 12, 25, 15, 0),
    total_price=750.0
)

# Получить бронирования пользователя
bookings = await db.get_user_bookings(user_id=2)

# Получить конкретное бронирование
booking = await db.get_booking(booking_id)

# Обновить статус
await db.update_booking_status(booking_id, 'confirmed')

# Бронирования поставщика
supplier_bookings = await db.get_supplier_bookings(supplier_id=1)

# Все бронирования
all_bookings = await db.get_all_bookings()
```

### Уведомления

```python
# Добавить запрос на уведомление
notification_id = await db.add_notification_request(
    user_id=2,
    desired_date="25.12.2024",
    desired_start="09:00",
    desired_end="18:00"
)

# Получить активные уведомления
notifications = await db.get_active_notifications()

# Деактивировать уведомление
await db.deactivate_notification(notification_id)
```

### Админские сессии

```python
# Создать сессию (на 24 часа)
await db.create_admin_session(user_id=1, hours=24)

# Проверить активную сессию
is_admin = await db.check_admin_session(user_id=1)

# Проверить является ли админом
is_admin = await db.is_admin(telegram_id=123456789)
```

### Статистика

```python
# Получить общую статистику
stats = await db.get_statistics()

print(f"Пользователей: {stats['total_users']}")
print(f"Мест: {stats['total_spots']}")
print(f"Бронирований: {stats['total_bookings']}")
print(f"Активных: {stats['active_bookings']}")
```

## 🎨 Работа с Клавиатурами

### Примеры из keyboards.py

```python
from keyboards import *

# Главное меню
menu = get_main_menu(role='customer')
await message.answer("Меню:", reply_markup=menu)

# Кнопка отмены
cancel = get_cancel_button()
await message.answer("Введите данные:", reply_markup=cancel)

# Выбор банка
banks = get_banks_keyboard()
await message.answer("Выберите банк:", reply_markup=banks)

# Выбор роли
roles = get_role_selection()
await message.answer("Выберите роль:", reply_markup=roles)

# Быстрый выбор даты
dates = get_date_selection_keyboard()
await message.answer("Выберите дату:", reply_markup=dates)

# Список мест
spots = await db.get_spots_by_supplier(supplier_id)
keyboard = get_spots_keyboard(spots)
await message.answer("Ваши места:", reply_markup=keyboard)

# Управление местом
keyboard = get_spot_management_keyboard(
    spot_id=1,
    is_available=True
)
await message.answer("Управление:", reply_markup=keyboard)

# Пагинация
keyboard = get_pagination_keyboard(
    page=0,
    total_pages=5,
    prefix="users"
)
await message.answer("Список:", reply_markup=keyboard)
```

## 🛠️ Утилиты

### Примеры из utils.py

```python
from utils import *

# Валидация телефона
is_valid = validate_phone("+7 900 123 45 67")  # True
is_valid = validate_phone("123")  # False

# Форматирование телефона
phone = format_phone("89001234567")  # "+7 (900) 123-45-67"

# Валидация карты
is_valid = validate_card_number("1234567812345678")  # True

# Маскирование карты
masked = mask_card_number("1234567812345678")  # "**** **** **** 5678"

# Валидация даты
date = validate_date("25.12.2024")  # datetime object или None

# Валидация времени
time = validate_time("14:30")  # datetime object или None

# Парсинг даты и времени
dt = parse_datetime("25.12.2024", "14:30")  # datetime object

# Расчет часов
hours = calculate_hours(
    datetime(2024, 12, 25, 10, 0),
    datetime(2024, 12, 25, 15, 0)
)  # 5.0

# Расчет цены
price = calculate_price(hours=5.0, price_per_hour=150.0)  # 750.0

# Форматирование
formatted = format_datetime(datetime(2024, 12, 25, 14, 30))  # "25.12.2024 14:30"
formatted = format_date(datetime(2024, 12, 25))  # "25.12.2024"
formatted = format_time(datetime(2024, 12, 25, 14, 30))  # "14:30"

# Emoji статуса
emoji = get_status_emoji('confirmed')  # '✅'
text = get_status_text('confirmed')  # 'Подтверждено'

# Проверка пересечения
overlap = check_time_overlap(
    datetime(2024, 12, 25, 10, 0),
    datetime(2024, 12, 25, 15, 0),
    datetime(2024, 12, 25, 14, 0),
    datetime(2024, 12, 25, 16, 0)
)  # True

# Разделение слота при частичном бронировании
free_slots = split_slot(
    slot_start=datetime(2024, 12, 25, 10, 0),
    slot_end=datetime(2024, 12, 25, 19, 0),
    booking_start=datetime(2024, 12, 25, 12, 0),
    booking_end=datetime(2024, 12, 25, 17, 0)
)
# [(10:00, 12:00), (17:00, 19:00)]

# Форматирование информации
info = format_booking_info(booking, 'customer')
info = format_spot_info(spot)
info = format_user_info(user)

# Экранирование HTML
safe = escape_html("<script>alert('xss')</script>")

# Обрезка текста
short = truncate_text("Длинный текст...", max_length=10)
```

## 🔄 FSM (Finite State Machine)

### Пример использования состояний

```python
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Определение состояний
class MyStates(StatesGroup):
    step1 = State()
    step2 = State()
    step3 = State()

# Установка состояния
@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.set_state(MyStates.step1)
    await message.answer("Шаг 1: Введите данные")

# Обработка состояния
@router.message(MyStates.step1)
async def process_step1(message: Message, state: FSMContext):
    # Сохраняем данные
    await state.update_data(data1=message.text)
    
    # Переходим к следующему шагу
    await state.set_state(MyStates.step2)
    await message.answer("Шаг 2: Введите еще данные")

# Получение данных
@router.message(MyStates.step2)
async def process_step2(message: Message, state: FSMContext):
    # Получаем все сохраненные данные
    data = await state.get_data()
    data1 = data.get('data1')
    
    # Очищаем состояние
    await state.clear()
    await message.answer("Готово!")
```

## 📝 Логирование

```python
import logging

logger = logging.getLogger(__name__)

# Уровни логирования
logger.debug("Отладочная информация")
logger.info("Информационное сообщение")
logger.warning("Предупреждение")
logger.error("Ошибка")
logger.critical("Критическая ошибка")

# С дополнительной информацией
try:
    # какой-то код
    pass
except Exception as e:
    logger.error(f"Ошибка при выполнении: {e}", exc_info=True)
```

## 🔌 Добавление новых обработчиков

```python
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

# Команда
@router.message(Command("mycommand"))
async def my_command(message: Message):
    await message.answer("Моя команда!")

# Текст
@router.message(F.text == "Кнопка")
async def button_handler(message: Message):
    await message.answer("Вы нажали кнопку!")

# Callback
@router.callback_query(F.data == "my_callback")
async def callback_handler(callback: CallbackQuery):
    await callback.message.edit_text("Callback обработан!")
    await callback.answer()

# Регистрация роутера в main.py
dp.include_router(my_router)
```

## 🎯 Best Practices

### 1. Обработка ошибок

```python
try:
    result = await db.some_operation()
    if not result:
        await message.answer("❌ Операция не удалась")
        return
except Exception as e:
    logger.error(f"Ошибка: {e}")
    await message.answer("❌ Произошла ошибка")
```

### 2. Валидация данных

```python
# Всегда валидируйте входные данные
if not validate_phone(phone):
    await message.answer("❌ Неверный формат телефона")
    return

price = validate_price(message.text)
if not price:
    await message.answer("❌ Неверный формат цены")
    return
```

### 3. Проверка прав доступа

```python
user = await db.get_user_by_telegram_id(message.from_user.id)
if user['role'] != 'supplier':
    await message.answer("❌ Эта функция доступна только поставщикам")
    return
```

### 4. Использование emoji

```python
# Используйте emoji для улучшения UX
await message.answer("✅ Успешно добавлено!")
await message.answer("❌ Ошибка!")
await message.answer("⏳ Обработка...")
```

### 5. Форматирование сообщений

```python
# HTML форматирование
text = f"""
<b>Заголовок</b>

📋 Информация:
• Пункт 1
• Пункт 2

<i>Примечание</i>
"""

await message.answer(text, parse_mode="HTML")
```

## 🔐 Безопасность

```python
# НЕ показывайте полные номера карт
masked = mask_card_number(card)  # **** **** **** 5678

# Экранируйте пользовательский ввод
safe_text = escape_html(user_input)

# Валидируйте все данные
if not validate_data(input):
    return

# Используйте параметризованные запросы (уже реализовано в database.py)
```

## 📦 Расширение функционала

### Добавление новой таблицы

```python
# В database.py
async def init_db(self):
    # ... существующие таблицы ...
    
    await db.execute('''
        CREATE TABLE IF NOT EXISTS my_new_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
```

### Добавление новой функции БД

```python
# В database.py
async def my_new_function(self, param: str) -> Optional[int]:
    """Описание функции"""
    try:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'INSERT INTO my_new_table (data) VALUES (?)',
                (param,)
            )
            await db.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return None
```

---

**Удачи в разработке! 💻**
