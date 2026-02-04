import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from config import DATABASE_PATH, ROLE_CUSTOMER, STATUS_PENDING

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация базы данных и создание таблиц"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    full_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    card_number TEXT NOT NULL,
                    bank TEXT NOT NULL,
                    role TEXT DEFAULT 'customer',
                    is_active INTEGER DEFAULT 1,
                    balance REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица парковочных мест
            await db.execute('''
                CREATE TABLE IF NOT EXISTS parking_spots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER NOT NULL,
                    spot_number TEXT NOT NULL,
                    address TEXT,
                    description TEXT,
                    price_per_hour REAL NOT NULL,
                    is_partial_allowed INTEGER DEFAULT 1,
                    is_available INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES users(id)
                )
            ''')

            # Таблица доступности мест
            await db.execute('''
                CREATE TABLE IF NOT EXISTS spot_availability (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spot_id INTEGER NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    is_booked INTEGER DEFAULT 0,
                    booked_by INTEGER,
                    booking_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (spot_id) REFERENCES parking_spots(id),
                    FOREIGN KEY (booked_by) REFERENCES users(id),
                    FOREIGN KEY (booking_id) REFERENCES bookings(id)
                )
            ''')

            # Таблица бронирований
            await db.execute('''
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    spot_id INTEGER NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    total_price REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    payment_method TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES users(id),
                    FOREIGN KEY (spot_id) REFERENCES parking_spots(id)
                )
            ''')

            # Таблица уведомлений
            await db.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    spot_id INTEGER,
                    desired_date DATE NOT NULL,
                    desired_start TIME NOT NULL,
                    desired_end TIME NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            # Таблица админских сессий
            await db.execute('''
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            await db.commit()
            logger.info("База данных инициализирована")

    # ===== ПОЛЬЗОВАТЕЛИ =====
    async def add_user(self, telegram_id: int, username: str, full_name: str, 
                       phone: str, card_number: str, bank: str) -> Optional[int]:
        """Добавление нового пользователя"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    INSERT INTO users (telegram_id, username, full_name, phone, card_number, bank)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (telegram_id, username, full_name, phone, card_number, bank))
                await db.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return None

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по Telegram ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_user_role(self, telegram_id: int, role: str) -> bool:
        """Обновление роли пользователя"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('UPDATE users SET role = ? WHERE telegram_id = ?', (role, telegram_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка обновления роли: {e}")
            return False

    async def get_all_users(self, offset: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение всех пользователей с пагинацией"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?',
                (limit, offset)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_users_count(self) -> int:
        """Получение общего количества пользователей"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT COUNT(*) FROM users') as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def block_user(self, user_id: int) -> bool:
        """Блокировка пользователя"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка блокировки пользователя: {e}")
            return False

    async def unblock_user(self, user_id: int) -> bool:
        """Разблокировка пользователя"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('UPDATE users SET is_active = 1 WHERE id = ?', (user_id,))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка разблокировки пользователя: {e}")
            return False

    # ===== ПАРКОВОЧНЫЕ МЕСТА =====
    async def add_parking_spot(self, supplier_id: int, spot_number: str, 
                               price_per_hour: float, address: str = None, 
                               description: str = None, is_partial_allowed: bool = True) -> Optional[int]:
        """Добавление парковочного места"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    INSERT INTO parking_spots (supplier_id, spot_number, address, description, 
                                               price_per_hour, is_partial_allowed)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (supplier_id, spot_number, address, description, price_per_hour, 
                      1 if is_partial_allowed else 0))
                await db.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка добавления парковочного места: {e}")
            return None

    async def get_spots_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Получение всех мест поставщика"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM parking_spots WHERE supplier_id = ? ORDER BY created_at DESC',
                (supplier_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_parking_spot(self, spot_id: int) -> Optional[Dict[str, Any]]:
        """Получение парковочного места по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM parking_spots WHERE id = ?', (spot_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_spot_price(self, spot_id: int, price: float) -> bool:
        """Обновление цены парковочного места"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('UPDATE parking_spots SET price_per_hour = ? WHERE id = ?', 
                               (price, spot_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка обновления цены: {e}")
            return False

    async def toggle_spot_visibility(self, spot_id: int) -> bool:
        """Переключение видимости места"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('SELECT is_available FROM parking_spots WHERE id = ?', 
                                    (spot_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        new_status = 0 if row[0] == 1 else 1
                        await db.execute('UPDATE parking_spots SET is_available = ? WHERE id = ?', 
                                       (new_status, spot_id))
                        await db.commit()
                        return True
            return False
        except Exception as e:
            logger.error(f"Ошибка переключения видимости: {e}")
            return False

    async def get_all_parking_spots(self) -> List[Dict[str, Any]]:
        """Получение всех парковочных мест"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM parking_spots ORDER BY created_at DESC') as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    # ===== ДОСТУПНОСТЬ МЕСТ =====
    async def add_availability(self, spot_id: int, start_time: datetime, 
                              end_time: datetime) -> Optional[int]:
        """Добавление периода доступности"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    INSERT INTO spot_availability (spot_id, start_time, end_time)
                    VALUES (?, ?, ?)
                ''', (spot_id, start_time, end_time))
                await db.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка добавления доступности: {e}")
            return None

    async def get_available_slots(self, date: datetime) -> List[Dict[str, Any]]:
        """Получение доступных слотов на дату"""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT sa.*, ps.spot_number, ps.price_per_hour, ps.address, 
                       ps.is_partial_allowed, ps.supplier_id
                FROM spot_availability sa
                JOIN parking_spots ps ON sa.spot_id = ps.id
                WHERE ps.is_available = 1
                  AND sa.is_booked = 0
                  AND sa.start_time >= ?
                  AND sa.end_time <= ?
                ORDER BY ps.spot_number
            ''', (start_of_day, end_of_day)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def check_slot_availability(self, spot_id: int, start_time: datetime, 
                                     end_time: datetime) -> bool:
        """Проверка доступности слота"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT COUNT(*) FROM spot_availability
                WHERE spot_id = ?
                  AND is_booked = 0
                  AND start_time <= ?
                  AND end_time >= ?
            ''', (spot_id, start_time, end_time)) as cursor:
                row = await cursor.fetchone()
                return row[0] > 0 if row else False

    async def book_slot(self, availability_id: int, customer_id: int, 
                       booking_id: int) -> bool:
        """Бронирование слота"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE spot_availability 
                    SET is_booked = 1, booked_by = ?, booking_id = ?
                    WHERE id = ?
                ''', (customer_id, booking_id, availability_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка бронирования слота: {e}")
            return False

    # ===== БРОНИРОВАНИЯ =====
    async def create_booking(self, customer_id: int, spot_id: int, 
                           start_time: datetime, end_time: datetime, 
                           total_price: float) -> Optional[int]:
        """Создание бронирования"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    INSERT INTO bookings (customer_id, spot_id, start_time, end_time, total_price)
                    VALUES (?, ?, ?, ?, ?)
                ''', (customer_id, spot_id, start_time, end_time, total_price))
                await db.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка создания бронирования: {e}")
            return None

    async def get_user_bookings(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение бронирований пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT b.*, ps.spot_number, ps.address, ps.supplier_id
                FROM bookings b
                JOIN parking_spots ps ON b.spot_id = ps.id
                WHERE b.customer_id = ?
                ORDER BY b.created_at DESC
            ''', (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_booking(self, booking_id: int) -> Optional[Dict[str, Any]]:
        """Получение бронирования по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT b.*, ps.spot_number, ps.address, ps.supplier_id, ps.price_per_hour
                FROM bookings b
                JOIN parking_spots ps ON b.spot_id = ps.id
                WHERE b.id = ?
            ''', (booking_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_booking_status(self, booking_id: int, status: str) -> bool:
        """Обновление статуса бронирования"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('UPDATE bookings SET status = ? WHERE id = ?', 
                               (status, booking_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка обновления статуса: {e}")
            return False

    async def get_supplier_bookings(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Получение бронирований поставщика"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT b.*, ps.spot_number, u.full_name as customer_name, u.phone
                FROM bookings b
                JOIN parking_spots ps ON b.spot_id = ps.id
                JOIN users u ON b.customer_id = u.id
                WHERE ps.supplier_id = ?
                ORDER BY b.created_at DESC
            ''', (supplier_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_all_bookings(self) -> List[Dict[str, Any]]:
        """Получение всех бронирований"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT b.*, ps.spot_number, 
                       u1.full_name as customer_name,
                       u2.full_name as supplier_name
                FROM bookings b
                JOIN parking_spots ps ON b.spot_id = ps.id
                JOIN users u1 ON b.customer_id = u1.id
                JOIN users u2 ON ps.supplier_id = u2.id
                ORDER BY b.created_at DESC
            ''') as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    # ===== УВЕДОМЛЕНИЯ =====
    async def add_notification_request(self, user_id: int, desired_date: str, 
                                      desired_start: str, desired_end: str) -> Optional[int]:
        """Добавление запроса на уведомление"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    INSERT INTO notifications (user_id, desired_date, desired_start, desired_end)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, desired_date, desired_start, desired_end))
                await db.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка добавления уведомления: {e}")
            return None

    async def get_active_notifications(self) -> List[Dict[str, Any]]:
        """Получение активных уведомлений"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT * FROM notifications WHERE is_active = 1
            ''') as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def deactivate_notification(self, notification_id: int) -> bool:
        """Деактивация уведомления"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('UPDATE notifications SET is_active = 0 WHERE id = ?', 
                               (notification_id,))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка деактивации уведомления: {e}")
            return False

    # ===== АДМИНСКИЕ СЕССИИ =====
    async def create_admin_session(self, user_id: int, hours: int = 24) -> bool:
        """Создание админской сессии"""
        try:
            expires_at = datetime.now() + timedelta(hours=hours)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO admin_sessions (user_id, expires_at)
                    VALUES (?, ?)
                ''', (user_id, expires_at))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка создания админской сессии: {e}")
            return False

    async def check_admin_session(self, user_id: int) -> bool:
        """Проверка активной админской сессии"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT COUNT(*) FROM admin_sessions
                WHERE user_id = ? AND expires_at > ?
            ''', (user_id, datetime.now())) as cursor:
                row = await cursor.fetchone()
                return row[0] > 0 if row else False

    async def is_admin(self, telegram_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        user = await self.get_user_by_telegram_id(telegram_id)
        if not user:
            return False
        
        # Проверяем роль или активную сессию
        if user['role'] == 'admin':
            return True
        
        return await self.check_admin_session(user['id'])

    # ===== СТАТИСТИКА =====
    async def get_statistics(self) -> Dict[str, Any]:
        """Получение общей статистики"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Количество пользователей
            async with db.execute('SELECT COUNT(*) FROM users') as cursor:
                row = await cursor.fetchone()
                stats['total_users'] = row[0] if row else 0
            
            # Количество мест
            async with db.execute('SELECT COUNT(*) FROM parking_spots') as cursor:
                row = await cursor.fetchone()
                stats['total_spots'] = row[0] if row else 0
            
            # Количество бронирований
            async with db.execute('SELECT COUNT(*) FROM bookings') as cursor:
                row = await cursor.fetchone()
                stats['total_bookings'] = row[0] if row else 0
            
            # Активные бронирования
            async with db.execute('''
                SELECT COUNT(*) FROM bookings 
                WHERE status = 'confirmed' OR status = 'pending'
            ''') as cursor:
                row = await cursor.fetchone()
                stats['active_bookings'] = row[0] if row else 0
            
            return stats
