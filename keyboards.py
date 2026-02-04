from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List
from config import BANKS_LIST


# ===== ГЛАВНОЕ МЕНЮ =====
def get_main_menu(role: str = 'customer') -> ReplyKeyboardMarkup:
    """Главное меню в зависимости от роли"""
    builder = ReplyKeyboardBuilder()
    
    if role == 'customer':
        builder.row(
            KeyboardButton(text="🏠 Свободные места"),
            KeyboardButton(text="📅 Выбрать дату")
        )
        builder.row(
            KeyboardButton(text="📋 Мои бронирования"),
            KeyboardButton(text="🔔 Уведомления")
        )
    elif role == 'supplier':
        builder.row(
            KeyboardButton(text="➕ Добавить место"),
            KeyboardButton(text="🏠 Мои места")
        )
        builder.row(
            KeyboardButton(text="📋 Заявки на бронирование"),
            KeyboardButton(text="📊 Статистика")
        )
    elif role == 'admin':
        builder.row(
            KeyboardButton(text="👥 Пользователи"),
            KeyboardButton(text="🏠 Все места")
        )
        builder.row(
            KeyboardButton(text="📊 Статистика"),
            KeyboardButton(text="📢 Рассылка")
        )
    
    builder.row(KeyboardButton(text="👤 Мой профиль"))
    
    return builder.as_markup(resize_keyboard=True)


def get_cancel_button() -> ReplyKeyboardMarkup:
    """Кнопка отмены"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)


# ===== РЕГИСТРАЦИЯ =====
def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для отправки номера телефона"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📱 Отправить номер", request_contact=True))
    builder.add(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_banks_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора банка"""
    builder = InlineKeyboardBuilder()
    for bank in BANKS_LIST:
        builder.add(InlineKeyboardButton(text=bank, callback_data=f"bank_{bank}"))
    builder.adjust(2)
    return builder.as_markup()


def get_role_selection() -> InlineKeyboardMarkup:
    """Выбор роли после регистрации"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🛒 Я покупатель", callback_data="role_customer"),
        InlineKeyboardButton(text="🏪 Я поставщик", callback_data="role_supplier")
    )
    builder.adjust(1)
    return builder.as_markup()


# ===== ПОСТАВЩИК =====
def get_partial_allowed_keyboard() -> InlineKeyboardMarkup:
    """Разрешить частичную аренду"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Да", callback_data="partial_yes"),
        InlineKeyboardButton(text="❌ Нет", callback_data="partial_no")
    )
    builder.adjust(2)
    return builder.as_markup()


def get_date_selection_keyboard() -> InlineKeyboardMarkup:
    """Быстрый выбор даты (6 дней)"""
    from datetime import datetime, timedelta
    
    builder = InlineKeyboardBuilder()
    today = datetime.now()
    
    for i in range(6):
        date = today + timedelta(days=i)
        date_str = date.strftime("%d.%m.%Y")
        display = "Сегодня" if i == 0 else ("Завтра" if i == 1 else date_str)
        builder.add(InlineKeyboardButton(
            text=display,
            callback_data=f"date_{date_str}"
        ))
    
    builder.add(InlineKeyboardButton(text="✍️ Ввести вручную", callback_data="date_manual"))
    builder.adjust(2)
    return builder.as_markup()


def get_spots_keyboard(spots: List[dict]) -> InlineKeyboardMarkup:
    """Клавиатура со списком мест поставщика"""
    builder = InlineKeyboardBuilder()
    
    for spot in spots:
        status = "🟢" if spot['is_available'] else "🔴"
        builder.add(InlineKeyboardButton(
            text=f"{status} Место {spot['spot_number']} - {spot['price_per_hour']}₽/ч",
            callback_data=f"spot_{spot['id']}"
        ))
    
    builder.adjust(1)
    return builder.as_markup()


def get_spot_management_keyboard(spot_id: int, is_available: bool) -> InlineKeyboardMarkup:
    """Управление парковочным местом"""
    builder = InlineKeyboardBuilder()
    
    visibility_text = "🙈 Скрыть" if is_available else "👁 Показать"
    builder.add(
        InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"edit_price_{spot_id}"),
        InlineKeyboardButton(text=visibility_text, callback_data=f"toggle_vis_{spot_id}"),
        InlineKeyboardButton(text="📅 Добавить период", callback_data=f"add_period_{spot_id}"),
        InlineKeyboardButton(text="📊 Статистика", callback_data=f"spot_stats_{spot_id}"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_spots")
    )
    builder.adjust(2)
    return builder.as_markup()


# ===== ПОКУПАТЕЛЬ =====
def get_available_slots_keyboard(slots: List[dict]) -> InlineKeyboardMarkup:
    """Клавиатура доступных слотов"""
    builder = InlineKeyboardBuilder()
    
    for slot in slots:
        from datetime import datetime
        start = datetime.fromisoformat(slot['start_time'])
        end = datetime.fromisoformat(slot['end_time'])
        
        builder.add(InlineKeyboardButton(
            text=f"Место {slot['spot_number']} | {start.strftime('%H:%M')}-{end.strftime('%H:%M')} | {slot['price_per_hour']}₽/ч",
            callback_data=f"book_slot_{slot['id']}"
        ))
    
    builder.adjust(1)
    return builder.as_markup()


def get_bookings_keyboard(bookings: List[dict]) -> InlineKeyboardMarkup:
    """Клавиатура бронирований"""
    builder = InlineKeyboardBuilder()
    
    for booking in bookings:
        from datetime import datetime
        start = datetime.fromisoformat(booking['start_time'])
        
        status_emoji = {
            'pending': '⏳',
            'confirmed': '✅',
            'cancelled': '❌',
            'completed': '✔️'
        }.get(booking['status'], '❓')
        
        builder.add(InlineKeyboardButton(
            text=f"{status_emoji} Место {booking['spot_number']} | {start.strftime('%d.%m %H:%M')}",
            callback_data=f"booking_{booking['id']}"
        ))
    
    builder.adjust(1)
    return builder.as_markup()


def get_booking_actions_keyboard(booking_id: int, status: str) -> InlineKeyboardMarkup:
    """Действия с бронированием"""
    builder = InlineKeyboardBuilder()
    
    if status == 'pending':
        builder.add(InlineKeyboardButton(
            text="❌ Отменить бронирование",
            callback_data=f"cancel_booking_{booking_id}"
        ))
    
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_bookings"))
    builder.adjust(1)
    return builder.as_markup()


def get_confirm_booking_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    """Подтверждение бронирования поставщиком"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_book_{booking_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_book_{booking_id}")
    )
    builder.adjust(2)
    return builder.as_markup()


# ===== АДМИН-ПАНЕЛЬ =====
def get_admin_menu() -> ReplyKeyboardMarkup:
    """Меню администратора"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="👥 Пользователи"),
        KeyboardButton(text="🏠 Парковочные места")
    )
    builder.row(
        KeyboardButton(text="📊 Статистика"),
        KeyboardButton(text="📢 Рассылка")
    )
    builder.row(
        KeyboardButton(text="⚙️ Настройки"),
        KeyboardButton(text="🔙 Выйти из админки")
    )
    return builder.as_markup(resize_keyboard=True)


def get_pagination_keyboard(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    """Клавиатура пагинации"""
    builder = InlineKeyboardBuilder()
    
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"{prefix}_page_{page-1}"))
    
    buttons.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="page_info"))
    
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"{prefix}_page_{page+1}"))
    
    builder.row(*buttons)
    return builder.as_markup()


def get_user_actions_keyboard(user_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """Действия с пользователем"""
    builder = InlineKeyboardBuilder()
    
    status_text = "🔓 Разблокировать" if not is_active else "🔒 Заблокировать"
    status_action = f"unblock_user_{user_id}" if not is_active else f"block_user_{user_id}"
    
    builder.add(
        InlineKeyboardButton(text=status_text, callback_data=status_action),
        InlineKeyboardButton(text="👑 Сделать админом", callback_data=f"make_admin_{user_id}"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_users")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение рассылки"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Да, отправить", callback_data="confirm_broadcast"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")
    )
    builder.adjust(2)
    return builder.as_markup()


# ===== ПРОФИЛЬ =====
def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура профиля"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✏️ Изменить телефон", callback_data="edit_phone"),
        InlineKeyboardButton(text="💳 Изменить карту", callback_data="edit_card"),
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
    )
    builder.adjust(1)
    return builder.as_markup()
