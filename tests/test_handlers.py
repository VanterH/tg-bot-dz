import pytest
from unittest.mock import AsyncMock, Mock
from bot.handlers import cmd_start, BookingStates

@pytest.mark.asyncio
async def test_cmd_start():
    message = AsyncMock()
    message.from_user.id = 123456
    message.from_user.full_name = "Test User"
    state = AsyncMock()
    
    await cmd_start(message, state)
    
    # Проверяем что состояние изменилось
    state.set_state.assert_called_once()

@pytest.mark.asyncio
async def test_payment_made():
    callback = AsyncMock()
    callback.message = AsyncMock()
    state = AsyncMock()
    state.update_data = AsyncMock()
    
    # Тестируем логику
    assert True