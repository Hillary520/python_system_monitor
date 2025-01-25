import pytest
import psutil
from unittest.mock import MagicMock

@pytest.fixture
def mock_psutil(monkeypatch):
    """Mock psutil for consistent testing"""
    mock = MagicMock(spec=psutil)
    monkeypatch.setattr('psutil.cpu_percent', lambda interval=None, percpu=False: 50.0)
    monkeypatch.setattr('psutil.virtual_memory', 
        lambda: MagicMock(percent=75.0, total=16*1024**3, available=4*1024**3))
    monkeypatch.setattr('psutil.swap_memory',
        lambda: MagicMock(percent=25.0))
    return mock

@pytest.fixture
def mock_curses():
    """Mock curses for UI testing"""
    curses_mock = MagicMock()
    curses_mock.LINES = 24
    curses_mock.COLS = 80
    curses_mock.color_pair = lambda x: x
    curses_mock.A_BOLD = 1
    curses_mock.A_REVERSE = 2
    return curses_mock
