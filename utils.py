import re
from datetime import datetime, timedelta
from typing import Optional, Tuple


def validate_phone(phone: str) -> bool:
    """Валидация российского номера телефона"""
    # Убираем все символы кроме цифр
    phone_digits = re.sub(r'\D', '', phone)
    
    # Проверяем длину (должно быть 11 цифр для российских номеров)
    if len(phone_digits) != 11:
        return False
    
    # Проверяем, что начинается с 7 или 8
    if phone_digits[0] not in ['7', '8']:
        return False
    
    return True


def format_phone(phone: str) -> str:
    """Форматирование номера телефона"""
    phone_digits = re.sub(r'\D', '', phone)
    if phone_digits[0] == '8':
        phone_digits = '7' + phone_digits[1:]
    
    return f"+{phone_digits[0]} ({phone_digits[1:4]}) {phone_digits[4:7]}-{phone_digits[7:9]}-{phone_digits[9:11]}"


def validate_card_number(card: str) -> bool:
    """Валидация номера карты (16 цифр)"""
    card_digits = re.sub(r'\D', '', card)
    return len(card_digits) == 16


def mask_card_number(card: str) -> str:
    """Маскирование номера карты (показываем только последние 4 цифры)"""
    card_digits = re.sub(r'\D', '', card)
    if len(card_digits) != 16:
        return card
    
    return f"**** **** **** {card_digits[-4:]}"


def validate_date(date_str: str) -> Optional[datetime]:
    """Валидация и парсинг даты в формате ДД.ММ.ГГГГ"""
    try:
        date = datetime.strptime(date_str, "%d.%m.%Y")
        # Проверяем, что дата не в прошлом
        if date.date() < datetime.now().date():
            return None
        return date
    except ValueError:
        return None


def validate_time(time_str: str) -> Optional[datetime]:
    """Валидация и парсинг времени в формате ЧЧ:ММ"""
    try:
        time = datetime.strptime(time_str, "%H:%M")
        return time
    except ValueError:
        return None


def parse_datetime(date_str: str, time_str: str) -> Optional[datetime]:
    """Парсинг даты и времени в datetime объект"""
    try:
        datetime_str = f"{date_str} {time_str}"
        return datetime.strptime(datetime_str, "%d.%m.%Y %H:%M")
    except ValueError:
        return None


def calculate_hours(start: datetime, end: datetime) -> float:
    """Расчет количества часов между датами"""
    delta = end - start
    return delta.total_seconds() / 3600


def calculate_price(hours: float, price_per_hour: float) -> float:
    """Расчет стоимости аренды"""
    return round(hours * price_per_hour, 2)


def format_datetime(dt: datetime) -> str:
    """Форматирование datetime для отображения"""
    return dt.strftime("%d.%m.%Y %H:%M")


def format_date(dt: datetime) -> str:
    """Форматирование даты для отображения"""
    return dt.strftime("%d.%m.%Y")


def format_time(dt: datetime) -> str:
    """Форматирование времени для отображения"""
    return dt.strftime("%H:%M")


def get_status_emoji(status: str) -> str:
    """Получение emoji для статуса"""
    status_map = {
        'pending': '⏳',
        'confirmed': '✅',
        'cancelled': '❌',
        'completed': '✔️'
    }
    return status_map.get(status, '❓')


def get_status_text(status: str) -> str:
    """Получение текстового описания статуса"""
    status_map = {
        'pending': 'Ожидает подтверждения',
        'confirmed': 'Подтверждено',
        'cancelled': 'Отменено',
        'completed': 'Завершено'
    }
    return status_map.get(status, 'Неизвестно')


def check_time_overlap(start1: datetime, end1: datetime, 
                       start2: datetime, end2: datetime) -> bool:
    """Проверка пересечения временных интервалов"""
    return start1 < end2 and start2 < end1


def split_slot(slot_start: datetime, slot_end: datetime,
               booking_start: datetime, booking_end: datetime) -> list:
    """
    Разделение слота при частичном бронировании.
    Возвращает список свободных интервалов после бронирования.
    """
    free_slots = []
    
    # Если есть свободное время до бронирования
    if slot_start < booking_start:
        free_slots.append((slot_start, booking_start))
    
    # Если есть свободное время после бронирования
    if booking_end < slot_end:
        free_slots.append((booking_end, slot_end))
    
    return free_slots


def is_past_datetime(dt: datetime) -> bool:
    """Проверка, является ли дата/время прошедшим"""
    return dt < datetime.now()


def get_upcoming_dates(days: int = 6) -> list:
    """Получение списка ближайших дат"""
    today = datetime.now()
    dates = []
    
    for i in range(days):
        date = today + timedelta(days=i)
        dates.append(date)
    
    return dates


def validate_price(price_str: str) -> Optional[float]:
    """Валидация цены"""
    try:
        price = float(price_str)
        if price <= 0:
            return None
        return round(price, 2)
    except ValueError:
        return None


def format_booking_info(booking: dict, user_type: str = 'customer') -> str:
    """Форматирование информации о бронировании"""
    from datetime import datetime
    
    start = datetime.fromisoformat(booking['start_time'])
    end = datetime.fromisoformat(booking['end_time'])
    
    hours = calculate_hours(start, end)
    
    info = f"📋 <b>Бронирование #{booking['id']}</b>\n\n"
    info += f"🏠 Место: {booking['spot_number']}\n"
    
    if booking.get('address'):
        info += f"📍 Адрес: {booking['address']}\n"
    
    info += f"📅 Дата: {format_date(start)}\n"
    info += f"🕐 Время: {format_time(start)} - {format_time(end)}\n"
    info += f"⏱ Длительность: {hours:.1f} ч\n"
    info += f"💰 Стоимость: {booking['total_price']} ₽\n"
    info += f"📊 Статус: {get_status_emoji(booking['status'])} {get_status_text(booking['status'])}\n"
    
    return info


def format_spot_info(spot: dict) -> str:
    """Форматирование информации о парковочном месте"""
    info = f"🏠 <b>Место #{spot['spot_number']}</b>\n\n"
    info += f"💰 Цена: {spot['price_per_hour']} ₽/час\n"
    
    if spot.get('address'):
        info += f"📍 Адрес: {spot['address']}\n"
    
    if spot.get('description'):
        info += f"📝 Описание: {spot['description']}\n"
    
    partial = "Да ✅" if spot['is_partial_allowed'] else "Нет ❌"
    info += f"🔀 Частичная аренда: {partial}\n"
    
    status = "Доступно 🟢" if spot['is_available'] else "Скрыто 🔴"
    info += f"📊 Статус: {status}\n"
    
    return info


def format_user_info(user: dict) -> str:
    """Форматирование информации о пользователе"""
    info = f"👤 <b>{user['full_name']}</b>\n\n"
    info += f"🆔 Telegram ID: {user['telegram_id']}\n"
    
    if user.get('username'):
        info += f"👤 Username: @{user['username']}\n"
    
    info += f"📱 Телефон: {user['phone']}\n"
    info += f"💳 Карта: {mask_card_number(user['card_number'])}\n"
    info += f"🏦 Банк: {user['bank']}\n"
    info += f"👔 Роль: {user['role']}\n"
    
    status = "Активен ✅" if user['is_active'] else "Заблокирован ❌"
    info += f"📊 Статус: {status}\n"
    
    created = datetime.fromisoformat(user['created_at'])
    info += f"📅 Регистрация: {format_date(created)}\n"
    
    return info


def escape_html(text: str) -> str:
    """Экранирование HTML символов"""
    if not text:
        return ""
    
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    
    return text


def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезка текста до максимальной длины"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."
