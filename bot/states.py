from aiogram.fsm.state import State, StatesGroup

class BookingStates(StatesGroup):
    """
    Состояния FSM для процесса записи клиента
    """
    waiting_for_name = State()        # Ожидание имени
    waiting_for_phone = State()       # Ожидание телефона
    waiting_for_service = State()     # Ожидание выбора услуги
    waiting_for_payment = State()     # Ожидание оплаты
    waiting_for_screenshot = State()  # Ожидание скриншота чека
    waiting_for_slot = State()        # Ожидание выбора времени

class AdminStates(StatesGroup):
    """
    Состояния FSM для администратора
    """
    waiting_for_slots_input = State()  # Ожидание ввода слотов
    waiting_for_price_change = State() # Ожидание изменения цены
    waiting_for_message = State()      # Ожидание текста сообщения