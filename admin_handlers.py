from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
import logging

from database import Database
from keyboards import *
from utils import *
from config import ADMIN_PASSWORD, ROLE_ADMIN, PAGINATION_SIZE, ADMIN_SESSION_HOURS

logger = logging.getLogger(__name__)
router = Router()
db = Database()


# ===== STATES =====
class AdminAuth(StatesGroup):
    password = State()


class Broadcast(StatesGroup):
    message_text = State()
    confirm = State()


# ===== ВХОД В АДМИНКУ =====
@router.message(Command("admin"))
async def admin_login(message: Message, state: FSMContext):
    """Вход в админ-панель"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
    
    # Проверяем, является ли пользователь администратором
    is_admin = await db.is_admin(message.from_user.id)
    
    if is_admin:
        await message.answer(
            "✅ Вы уже в админ-панели!",
            reply_markup=get_admin_menu()
        )
        return
    
    # Запрашиваем пароль
    await message.answer(
        "🔐 Введите пароль администратора:",
        reply_markup=get_cancel_button()
    )
    await state.set_state(AdminAuth.password)


@router.message(AdminAuth.password)
async def process_admin_password(message: Message, state: FSMContext):
    """Обработка ввода пароля админа"""
    if message.text == "❌ Отмена":
        await state.clear()
        user = await db.get_user_by_telegram_id(message.from_user.id)
        await message.answer(
            "Отменено.",
            reply_markup=get_main_menu(user['role'] if user else 'customer')
        )
        return
    
    if message.text == ADMIN_PASSWORD:
        user = await db.get_user_by_telegram_id(message.from_user.id)
        
        # Создаем временную админскую сессию
        success = await db.create_admin_session(user['id'], ADMIN_SESSION_HOURS)
        
        if success:
            await message.answer(
                f"✅ Доступ предоставлен на {ADMIN_SESSION_HOURS} часов!\n\n"
                "Добро пожаловать в админ-панель.",
                reply_markup=get_admin_menu()
            )
        else:
            await message.answer("❌ Ошибка создания сессии.")
    else:
        await message.answer("❌ Неверный пароль.")
    
    await state.clear()


# ===== ВЫХОД ИЗ АДМИНКИ =====
@router.message(F.text == "🔙 Выйти из админки")
async def exit_admin_panel(message: Message):
    """Выход из админ-панели"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        return
    
    await message.answer(
        "👋 Вы вышли из админ-панели.",
        reply_markup=get_main_menu(user['role'])
    )


# ===== ПОЛЬЗОВАТЕЛИ =====
@router.message(F.text == "👥 Пользователи")
async def show_users(message: Message):
    """Показать список пользователей"""
    is_admin = await db.is_admin(message.from_user.id)
    
    if not is_admin:
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    users = await db.get_all_users(offset=0, limit=PAGINATION_SIZE)
    total_users = await db.get_users_count()
    total_pages = (total_users + PAGINATION_SIZE - 1) // PAGINATION_SIZE
    
    if not users:
        await message.answer("Пользователей пока нет.")
        return
    
    text = f"👥 <b>Пользователи</b> (стр. 1/{total_pages})\n\n"
    
    for user in users:
        status = "✅" if user['is_active'] else "❌"
        role_emoji = {
            'customer': '🛒',
            'supplier': '🏪',
            'admin': '👑'
        }.get(user['role'], '❓')
        
        text += f"{status} {role_emoji} <b>{escape_html(user['full_name'])}</b>\n"
        text += f"   ID: {user['telegram_id']}\n"
        text += f"   Роль: {user['role']}\n\n"
    
    keyboard = get_pagination_keyboard(0, total_pages, "users")
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("users_page_"))
async def paginate_users(callback: CallbackQuery):
    """Пагинация пользователей"""
    page = int(callback.data.replace("users_page_", ""))
    
    offset = page * PAGINATION_SIZE
    users = await db.get_all_users(offset=offset, limit=PAGINATION_SIZE)
    total_users = await db.get_users_count()
    total_pages = (total_users + PAGINATION_SIZE - 1) // PAGINATION_SIZE
    
    text = f"👥 <b>Пользователи</b> (стр. {page + 1}/{total_pages})\n\n"
    
    for user in users:
        status = "✅" if user['is_active'] else "❌"
        role_emoji = {
            'customer': '🛒',
            'supplier': '🏪',
            'admin': '👑'
        }.get(user['role'], '❓')
        
        text += f"{status} {role_emoji} <b>{escape_html(user['full_name'])}</b>\n"
        text += f"   ID: {user['telegram_id']}\n"
        text += f"   Роль: {user['role']}\n\n"
    
    keyboard = get_pagination_keyboard(page, total_pages, "users")
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


# ===== ПАРКОВОЧНЫЕ МЕСТА (АДМИН) =====
@router.message(F.text == "🏠 Парковочные места")
async def show_all_spots_admin(message: Message):
    """Показать все парковочные места (для админа)"""
    is_admin = await db.is_admin(message.from_user.id)
    
    if not is_admin:
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    spots = await db.get_all_parking_spots()
    
    if not spots:
        await message.answer("Парковочных мест пока нет.")
        return
    
    text = f"🏠 <b>Все парковочные места</b> ({len(spots)})\n\n"
    
    for spot in spots:
        status = "🟢" if spot['is_available'] else "🔴"
        partial = "🔀" if spot['is_partial_allowed'] else "🚫"
        
        text += f"{status} {partial} <b>Место {escape_html(spot['spot_number'])}</b>\n"
        text += f"   Цена: {spot['price_per_hour']} ₽/ч\n"
        text += f"   Поставщик ID: {spot['supplier_id']}\n"
        
        if spot.get('address'):
            text += f"   📍 {escape_html(spot['address'][:50])}\n"
        
        text += "\n"
    
    # Разбиваем на несколько сообщений если текст слишком длинный
    if len(text) > 4000:
        parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for part in parts:
            await message.answer(part, parse_mode="HTML")
    else:
        await message.answer(text, parse_mode="HTML")


# ===== СТАТИСТИКА =====
@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message):
    """Показать статистику системы"""
    is_admin = await db.is_admin(message.from_user.id)
    
    if not is_admin:
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    stats = await db.get_statistics()
    
    text = "📊 <b>Статистика системы</b>\n\n"
    text += f"👥 Всего пользователей: {stats['total_users']}\n"
    text += f"🏠 Всего парковочных мест: {stats['total_spots']}\n"
    text += f"📋 Всего бронирований: {stats['total_bookings']}\n"
    text += f"✅ Активных бронирований: {stats['active_bookings']}\n"
    
    await message.answer(text, parse_mode="HTML")


# ===== РАССЫЛКА =====
@router.message(F.text == "📢 Рассылка")
async def start_broadcast(message: Message, state: FSMContext):
    """Начать рассылку"""
    is_admin = await db.is_admin(message.from_user.id)
    
    if not is_admin:
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    await message.answer(
        "📢 <b>Рассылка сообщения</b>\n\n"
        "Введите текст сообщения для рассылки всем пользователям:",
        reply_markup=get_cancel_button(),
        parse_mode="HTML"
    )
    await state.set_state(Broadcast.message_text)


@router.message(Broadcast.message_text)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Обработка текста рассылки"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Рассылка отменена.", reply_markup=get_admin_menu())
        return
    
    await state.update_data(message_text=message.text)
    
    total_users = await db.get_users_count()
    
    await message.answer(
        f"📢 Вы уверены, что хотите отправить это сообщение {total_users} пользователям?\n\n"
        f"<b>Текст сообщения:</b>\n{escape_html(message.text)}",
        reply_markup=get_broadcast_confirm_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(Broadcast.confirm)


@router.callback_query(Broadcast.confirm, F.data == "confirm_broadcast")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и выполнение рассылки"""
    data = await state.get_data()
    message_text = data['message_text']
    
    # Получаем всех пользователей
    all_users = []
    offset = 0
    while True:
        users = await db.get_all_users(offset=offset, limit=100)
        if not users:
            break
        all_users.extend(users)
        offset += 100
    
    await callback.message.edit_text("📤 Начинаю рассылку...")
    
    success_count = 0
    fail_count = 0
    
    for user in all_users:
        try:
            await callback.bot.send_message(
                chat_id=user['telegram_id'],
                text=f"📢 <b>Рассылка от администрации</b>\n\n{message_text}",
                parse_mode="HTML"
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю {user['telegram_id']}: {e}")
            fail_count += 1
    
    await callback.message.answer(
        f"✅ Рассылка завершена!\n\n"
        f"Успешно: {success_count}\n"
        f"Ошибок: {fail_count}",
        reply_markup=get_admin_menu()
    )
    
    await state.clear()


@router.callback_query(Broadcast.confirm, F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    """Отмена рассылки"""
    await callback.message.edit_text("❌ Рассылка отменена.")
    await callback.message.answer("Админ-панель:", reply_markup=get_admin_menu())
    await state.clear()


# ===== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ =====
@router.callback_query(F.data.startswith("block_user_"))
async def block_user(callback: CallbackQuery):
    """Блокировка пользователя"""
    user_id = int(callback.data.replace("block_user_", ""))
    
    success = await db.block_user(user_id)
    
    if success:
        await callback.answer("✅ Пользователь заблокирован")
    else:
        await callback.answer("❌ Ошибка блокировки")


@router.callback_query(F.data.startswith("unblock_user_"))
async def unblock_user(callback: CallbackQuery):
    """Разблокировка пользователя"""
    user_id = int(callback.data.replace("unblock_user_", ""))
    
    success = await db.unblock_user(user_id)
    
    if success:
        await callback.answer("✅ Пользователь разблокирован")
    else:
        await callback.answer("❌ Ошибка разблокировки")


@router.callback_query(F.data.startswith("make_admin_"))
async def make_admin(callback: CallbackQuery):
    """Назначение администратором"""
    user_id = int(callback.data.replace("make_admin_", ""))
    
    # Получаем пользователя по внутреннему ID
    all_users = await db.get_all_users(offset=0, limit=10000)
    target_user = None
    
    for user in all_users:
        if user['id'] == user_id:
            target_user = user
            break
    
    if not target_user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    success = await db.update_user_role(target_user['telegram_id'], ROLE_ADMIN)
    
    if success:
        await callback.answer("✅ Пользователь назначен администратором")
        
        # Уведомляем пользователя
        try:
            await callback.bot.send_message(
                chat_id=target_user['telegram_id'],
                text="🎉 Вы были назначены администратором системы!\n\n"
                     "Используйте команду /admin для входа в админ-панель."
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления нового админа: {e}")
    else:
        await callback.answer("❌ Ошибка назначения")


# ===== НАСТРОЙКИ =====
@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    """Показать настройки"""
    is_admin = await db.is_admin(message.from_user.id)
    
    if not is_admin:
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    from config import ADMIN_SESSION_HOURS, NOTIFICATION_REMINDER_HOURS, PAGINATION_SIZE
    
    text = "⚙️ <b>Настройки системы</b>\n\n"
    text += f"🕐 Длительность админ-сессии: {ADMIN_SESSION_HOURS} ч\n"
    text += f"🔔 Напоминание о бронировании: за {NOTIFICATION_REMINDER_HOURS} ч\n"
    text += f"📄 Элементов на странице: {PAGINATION_SIZE}\n"
    text += f"\n💾 База данных: SQLite\n"
    text += f"🤖 Версия бота: 1.0.0\n"
    
    await message.answer(text, parse_mode="HTML")
