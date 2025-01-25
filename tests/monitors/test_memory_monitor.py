import pytest
from python_system_monitor.monitors.memory_monitor import MemoryMonitor

def test_memory_monitor_init():
    monitor = MemoryMonitor()
    assert monitor.bars == 50

def test_get_memory_percentage(mock_psutil):
    monitor = MemoryMonitor()
    assert monitor.get_memory_percentage() == 75.0

def test_get_swap_percentage(mock_psutil):
    monitor = MemoryMonitor()
    assert monitor.get_swap_percentage() == 25.0

def test_format_usage():
    monitor = MemoryMonitor(bars=10)
    formatted = monitor._format_usage(50.0)
    assert '[#####-----]' in formatted
    assert '50.00%' in formatted

@pytest.mark.parametrize("memory_value,expected_hashes", [
    (0, 0),
    (50, 5),
    (100, 10),
])
def test_format_usage_values(memory_value, expected_hashes):
    monitor = MemoryMonitor(bars=10)
    formatted = monitor._format_usage(memory_value)
    assert formatted.count('#') == expected_hashes
