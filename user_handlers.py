from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timedelta
import logging

from database import Database
from keyboards import *
from utils import *
from config import ROLE_CUSTOMER, ROLE_SUPPLIER, STATUS_PENDING, STATUS_CONFIRMED

logger = logging.getLogger(__name__)
router = Router()
db = Database()


# ===== STATES =====
class Registration(StatesGroup):
    full_name = State()
    phone = State()
    card_number = State()
    bank = State()


class AddSpot(StatesGroup):
    spot_number = State()
    price = State()
    address = State()
    description = State()
    partial_allowed = State()
    date = State()
    start_time = State()
    end_time = State()


class SearchSpot(StatesGroup):
    date = State()
    viewing_slots = State()


class BookingProcess(StatesGroup):
    select_time = State()
    confirm = State()


class NotificationRequest(StatesGroup):
    date = State()
    start_time = State()
    end_time = State()


# ===== РЕГИСТРАЦИЯ =====
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if user:
        # Пользователь уже зарегистрирован
        await message.answer(
            f"С возвращением, {user['full_name']}! 👋",
            reply_markup=get_main_menu(user['role'])
        )
    else:
        # Начинаем регистрацию
        await message.answer(
            "👋 Добро пожаловать в систему аренды парковочных мест!\n\n"
            "Для начала работы необходимо зарегистрироваться.\n\n"
            "Введите ваше имя и фамилию:",
            reply_markup=get_cancel_button()
        )
        await state.set_state(Registration.full_name)


@router.message(Registration.full_name)
async def process_full_name(message: Message, state: FSMContext):
    """Обработка ввода имени и фамилии"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Регистрация отменена.", reply_markup=types.ReplyKeyboardRemove())
        return
    
    await state.update_data(full_name=message.text)
    await message.answer(
        "📱 Отправьте ваш номер телефона:",
        reply_markup=get_phone_keyboard()
    )
    await state.set_state(Registration.phone)


@router.message(Registration.phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка ввода телефона"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Регистрация отменена.", reply_markup=types.ReplyKeyboardRemove())
        return
    
    phone = None
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text
    
    if not validate_phone(phone):
        await message.answer("❌ Неверный формат номера телефона. Попробуйте еще раз:")
        return
    
    formatted_phone = format_phone(phone)
    await state.update_data(phone=formatted_phone)
    
    await message.answer(
        "💳 Введите номер вашей банковской карты (16 цифр):",
        reply_markup=get_cancel_button()
    )
    await state.set_state(Registration.card_number)


@router.message(Registration.card_number)
async def process_card(message: Message, state: FSMContext):
    """Обработка ввода номера карты"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Регистрация отменена.", reply_markup=types.ReplyKeyboardRemove())
        return
    
    if not validate_card_number(message.text):
        await message.answer("❌ Неверный формат номера карты. Введите 16 цифр:")
        return
    
    await state.update_data(card_number=message.text)
    await message.answer(
        "🏦 Выберите ваш банк:",
        reply_markup=get_banks_keyboard()
    )
    await state.set_state(Registration.bank)


@router.callback_query(Registration.bank, F.data.startswith("bank_"))
async def process_bank(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора банка"""
    bank = callback.data.replace("bank_", "")
    data = await state.get_data()
    
    # Создаем пользователя
    user_id = await db.add_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=data['full_name'],
        phone=data['phone'],
        card_number=data['card_number'],
        bank=bank
    )
    
    if user_id:
        await callback.message.edit_text(
            "✅ Регистрация завершена!\n\n"
            "Теперь выберите вашу роль:",
            reply_markup=get_role_selection()
        )
    else:
        await callback.message.edit_text("❌ Ошибка при регистрации. Попробуйте снова /start")
        await state.clear()


@router.callback_query(F.data.startswith("role_"))
async def process_role_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора роли"""
    role = callback.data.replace("role_", "")
    
    success = await db.update_user_role(callback.from_user.id, role)
    
    if success:
        role_text = "покупателя" if role == ROLE_CUSTOMER else "поставщика"
        await callback.message.edit_text(
            f"✅ Вы зарегистрированы как {role_text}!\n\n"
            "Используйте меню для начала работы."
        )
        await callback.message.answer(
            "Главное меню:",
            reply_markup=get_main_menu(role)
        )
    else:
        await callback.message.edit_text("❌ Ошибка при выборе роли.")
    
    await state.clear()


# ===== ПОСТАВЩИК - ДОБАВЛЕНИЕ МЕСТА =====
@router.message(F.text == "➕ Добавить место")
async def start_add_spot(message: Message, state: FSMContext):
    """Начало добавления парковочного места"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user or user['role'] != ROLE_SUPPLIER:
        await message.answer("❌ Эта функция доступна только поставщикам.")
        return
    
    await message.answer(
        "🏠 Добавление нового парковочного места\n\n"
        "Введите номер места (например: А12, 45):",
        reply_markup=get_cancel_button()
    )
    await state.set_state(AddSpot.spot_number)


@router.message(AddSpot.spot_number)
async def process_spot_number(message: Message, state: FSMContext):
    """Обработка ввода номера места"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_menu(ROLE_SUPPLIER))
        return
    
    await state.update_data(spot_number=message.text)
    await message.answer("💰 Введите цену за час (в рублях):")
    await state.set_state(AddSpot.price)


@router.message(AddSpot.price)
async def process_spot_price(message: Message, state: FSMContext):
    """Обработка ввода цены"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_menu(ROLE_SUPPLIER))
        return
    
    price = validate_price(message.text)
    if not price:
        await message.answer("❌ Неверный формат цены. Введите число:")
        return
    
    await state.update_data(price=price)
    await message.answer(
        "📍 Введите адрес (или отправьте '-' чтобы пропустить):"
    )
    await state.set_state(AddSpot.address)


@router.message(AddSpot.address)
async def process_spot_address(message: Message, state: FSMContext):
    """Обработка ввода адреса"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_menu(ROLE_SUPPLIER))
        return
    
    address = None if message.text == "-" else message.text
    await state.update_data(address=address)
    
    await message.answer(
        "📝 Введите описание (или отправьте '-' чтобы пропустить):"
    )
    await state.set_state(AddSpot.description)


@router.message(AddSpot.description)
async def process_spot_description(message: Message, state: FSMContext):
    """Обработка ввода описания"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_menu(ROLE_SUPPLIER))
        return
    
    description = None if message.text == "-" else message.text
    await state.update_data(description=description)
    
    await message.answer(
        "🔀 Разрешить частичную аренду места?",
        reply_markup=get_partial_allowed_keyboard()
    )
    await state.set_state(AddSpot.partial_allowed)


@router.callback_query(AddSpot.partial_allowed, F.data.startswith("partial_"))
async def process_partial_allowed(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора частичной аренды"""
    is_partial = callback.data == "partial_yes"
    data = await state.get_data()
    
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    # Создаем парковочное место
    spot_id = await db.add_parking_spot(
        supplier_id=user['id'],
        spot_number=data['spot_number'],
        price_per_hour=data['price'],
        address=data.get('address'),
        description=data.get('description'),
        is_partial_allowed=is_partial
    )
    
    if spot_id:
        await callback.message.edit_text(
            f"✅ Место {data['spot_number']} успешно добавлено!\n\n"
            "Теперь добавьте период доступности."
        )
        await callback.message.answer(
            "📅 Выберите дату:",
            reply_markup=get_date_selection_keyboard()
        )
        await state.update_data(spot_id=spot_id)
        await state.set_state(AddSpot.date)
    else:
        await callback.message.edit_text("❌ Ошибка при добавлении места.")
        await state.clear()


@router.callback_query(AddSpot.date, F.data.startswith("date_"))
async def process_availability_date(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора даты доступности"""
    if callback.data == "date_manual":
        await callback.message.edit_text(
            "✍️ Введите дату в формате ДД.ММ.ГГГГ:"
        )
        return
    
    date_str = callback.data.replace("date_", "")
    await state.update_data(date=date_str)
    
    await callback.message.edit_text(
        f"📅 Дата: {date_str}\n\n"
        "🕐 Введите время начала в формате ЧЧ:ММ (например: 09:00):"
    )
    await state.set_state(AddSpot.start_time)


@router.message(AddSpot.start_time)
async def process_start_time(message: Message, state: FSMContext):
    """Обработка ввода времени начала"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_menu(ROLE_SUPPLIER))
        return
    
    time_obj = validate_time(message.text)
    if not time_obj:
        await message.answer("❌ Неверный формат времени. Используйте ЧЧ:ММ:")
        return
    
    await state.update_data(start_time=message.text)
    await message.answer(
        "🕐 Введите время окончания в формате ЧЧ:ММ (например: 18:00):"
    )
    await state.set_state(AddSpot.end_time)


@router.message(AddSpot.end_time)
async def process_end_time(message: Message, state: FSMContext):
    """Обработка ввода времени окончания"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_menu(ROLE_SUPPLIER))
        return
    
    time_obj = validate_time(message.text)
    if not time_obj:
        await message.answer("❌ Неверный формат времени. Используйте ЧЧ:ММ:")
        return
    
    data = await state.get_data()
    
    # Парсим дату и время
    start_dt = parse_datetime(data['date'], data['start_time'])
    end_dt = parse_datetime(data['date'], message.text)
    
    if not start_dt or not end_dt:
        await message.answer("❌ Ошибка парсинга даты/времени.")
        await state.clear()
        return
    
    if end_dt <= start_dt:
        await message.answer("❌ Время окончания должно быть позже времени начала.")
        return
    
    # Добавляем период доступности
    availability_id = await db.add_availability(
        spot_id=data['spot_id'],
        start_time=start_dt,
        end_time=end_dt
    )
    
    if availability_id:
        await message.answer(
            f"✅ Период доступности добавлен!\n\n"
            f"📅 {data['date']}\n"
            f"🕐 {data['start_time']} - {message.text}\n\n"
            "Место теперь доступно для бронирования.",
            reply_markup=get_main_menu(ROLE_SUPPLIER)
        )
    else:
        await message.answer("❌ Ошибка при добавлении периода.")
    
    await state.clear()


# ===== ПОСТАВЩИК - МОИ МЕСТА =====
@router.message(F.text == "🏠 Мои места")
async def show_my_spots(message: Message):
    """Показать все места поставщика"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user or user['role'] != ROLE_SUPPLIER:
        await message.answer("❌ Эта функция доступна только поставщикам.")
        return
    
    spots = await db.get_spots_by_supplier(user['id'])
    
    if not spots:
        await message.answer(
            "У вас пока нет добавленных мест.\n\n"
            "Используйте кнопку '➕ Добавить место' для создания первого места."
        )
        return
    
    await message.answer(
        f"🏠 Ваши парковочные места ({len(spots)}):\n\n"
        "Выберите место для управления:",
        reply_markup=get_spots_keyboard(spots)
    )


@router.callback_query(F.data.startswith("spot_"))
async def show_spot_details(callback: CallbackQuery):
    """Показать детали парковочного места"""
    spot_id = int(callback.data.replace("spot_", ""))
    spot = await db.get_parking_spot(spot_id)
    
    if not spot:
        await callback.answer("❌ Место не найдено")
        return
    
    info = format_spot_info(spot)
    
    await callback.message.edit_text(
        info,
        reply_markup=get_spot_management_keyboard(spot_id, spot['is_available']),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("toggle_vis_"))
async def toggle_spot_visibility(callback: CallbackQuery):
    """Переключение видимости места"""
    spot_id = int(callback.data.replace("toggle_vis_", ""))
    
    success = await db.toggle_spot_visibility(spot_id)
    
    if success:
        spot = await db.get_parking_spot(spot_id)
        status = "показано" if spot['is_available'] else "скрыто"
        await callback.answer(f"✅ Место {status}")
        
        # Обновляем информацию
        info = format_spot_info(spot)
        await callback.message.edit_text(
            info,
            reply_markup=get_spot_management_keyboard(spot_id, spot['is_available']),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Ошибка")


# ===== ПОКУПАТЕЛЬ - ПОИСК МЕСТ =====
@router.message(F.text == "🏠 Свободные места")
async def show_available_spots(message: Message):
    """Показать свободные места на сегодня"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
    
    today = datetime.now()
    slots = await db.get_available_slots(today)
    
    if not slots:
        await message.answer(
            "К сожалению, на сегодня нет доступных мест. 😔\n\n"
            "Попробуйте выбрать другую дату или настройте уведомления."
        )
        return
    
    await message.answer(
        f"🏠 Доступные места на сегодня ({len(slots)}):\n\n"
        "Выберите подходящий слот:",
        reply_markup=get_available_slots_keyboard(slots)
    )


@router.message(F.text == "📅 Выбрать дату")
async def select_date_for_search(message: Message, state: FSMContext):
    """Выбор даты для поиска"""
    await message.answer(
        "📅 Выберите дату:",
        reply_markup=get_date_selection_keyboard()
    )
    await state.set_state(SearchSpot.date)


@router.callback_query(SearchSpot.date, F.data.startswith("date_"))
async def process_search_date(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора даты для поиска"""
    if callback.data == "date_manual":
        await callback.message.edit_text(
            "✍️ Введите дату в формате ДД.ММ.ГГГГ:"
        )
        return
    
    date_str = callback.data.replace("date_", "")
    date = validate_date(date_str)
    
    if not date:
        await callback.answer("❌ Неверная дата")
        return
    
    slots = await db.get_available_slots(date)
    
    if not slots:
        await callback.message.edit_text(
            f"К сожалению, на {date_str} нет доступных мест. 😔\n\n"
            "Попробуйте другую дату или настройте уведомления."
        )
        await state.clear()
        return
    
    await callback.message.edit_text(
        f"🏠 Доступные места на {date_str} ({len(slots)}):\n\n"
        "Выберите подходящий слот:",
        reply_markup=get_available_slots_keyboard(slots)
    )
    await state.clear()


# ===== ПОКУПАТЕЛЬ - БРОНИРОВАНИЯ =====
@router.message(F.text == "📋 Мои бронирования")
async def show_my_bookings(message: Message):
    """Показать бронирования пользователя"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Вы не зарегистрированы.")
        return
    
    bookings = await db.get_user_bookings(user['id'])
    
    if not bookings:
        await message.answer(
            "У вас пока нет бронирований.\n\n"
            "Используйте '🏠 Свободные места' для поиска парковки."
        )
        return
    
    await message.answer(
        f"📋 Ваши бронирования ({len(bookings)}):\n\n"
        "Выберите бронирование для просмотра:",
        reply_markup=get_bookings_keyboard(bookings)
    )


@router.callback_query(F.data.startswith("booking_"))
async def show_booking_details(callback: CallbackQuery):
    """Показать детали бронирования"""
    booking_id = int(callback.data.replace("booking_", ""))
    booking = await db.get_booking(booking_id)
    
    if not booking:
        await callback.answer("❌ Бронирование не найдено")
        return
    
    info = format_booking_info(booking, 'customer')
    
    # Получаем информацию о поставщике для реквизитов
    supplier = await db.get_user_by_telegram_id(booking['supplier_id'])
    if supplier and booking['status'] in [STATUS_CONFIRMED, STATUS_PENDING]:
        info += f"\n💳 <b>Реквизиты для оплаты:</b>\n"
        info += f"Банк: {supplier['bank']}\n"
        info += f"Карта: {mask_card_number(supplier['card_number'])}\n"
    
    await callback.message.edit_text(
        info,
        reply_markup=get_booking_actions_keyboard(booking_id, booking['status']),
        parse_mode="HTML"
    )


# ===== ПРОФИЛЬ =====
@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message):
    """Показать профиль пользователя"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Вы не зарегистрированы.")
        return
    
    info = format_user_info(user)
    
    await message.answer(
        info,
        reply_markup=get_profile_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    await callback.message.delete()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_menu(user['role'] if user else ROLE_CUSTOMER)
    )
