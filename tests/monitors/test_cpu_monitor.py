import pytest
from python_system_monitor.monitors.cpu_monitor import CPUMonitor

def test_cpu_monitor_init():
    monitor = CPUMonitor()
    assert monitor.bars == 50
    assert hasattr(monitor, 'last_cpu_percent')

def test_get_detailed_stats(mock_psutil):
    monitor = CPUMonitor()
    stats = monitor.get_detailed_stats()
    assert 'usage' in stats
    assert 'freq_current' in stats
    assert 'cores' in stats
    assert stats['usage'] == 50.0

def test_format_usage():
    monitor = CPUMonitor(bars=10)
    formatted = monitor._format_usage(50.0)
    assert len(formatted) > 0
    assert '[#####-----]' in formatted
    assert '50.00%' in formatted

@pytest.mark.parametrize("cpu_value,expected_hashes", [
    (0, 0),
    (50, 5),
    (100, 10),
])
def test_format_usage_values(cpu_value, expected_hashes):
    monitor = CPUMonitor(bars=10)
    formatted = monitor._format_usage(cpu_value)
    assert formatted.count('#') == expected_hashes
