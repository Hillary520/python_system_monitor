import pytest
import asyncio
from python_system_monitor.monitors.system_info import SystemInfo

@pytest.mark.asyncio
async def test_system_info_init():
    info = SystemInfo()
    assert info.executor is not None
    assert info.cached_ip is None
    assert info.cached_hostname is None

@pytest.mark.asyncio
async def test_get_system_info():
    info = SystemInfo()
    result = await info.get_system_info()
    assert isinstance(result, str)
    assert "OS:" in result
    assert "CPU:" in result

@pytest.mark.asyncio
async def test_get_os_info(mock_psutil):
    info = SystemInfo()
    result = await info._get_os_info(asyncio.get_event_loop())
    assert isinstance(result, dict)
    assert "OS" in result
    assert "Host" in result
    assert "IP" in result

@pytest.mark.asyncio
async def test_format_uptime():
    info = SystemInfo()
    uptime = info._format_uptime(90061)  # 1 day, 1 hour, 1 minute
    assert "1d" in uptime
    assert "1h" in uptime
    assert "1m" in uptime
