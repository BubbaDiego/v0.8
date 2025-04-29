import pytest
import asyncio
from cyclone.cyclone import Cyclone
from utils.console_logger import ConsoleLogger as log

@pytest.fixture
def cyclone_instance():
    """Create a Cyclone instance for testing."""
    return Cyclone(poll_interval=1)  # Short poll interval for faster testing

@pytest.mark.asyncio
async def test_run_market_updates(cyclone_instance):
    """Test that market price updates can run without crashing."""
    log.banner("TEST: Cyclone run_market_updates Start")
    try:
        await cyclone_instance.run_market_updates()
        log.success("✅ Cyclone market price updates ran successfully.", source="TestCycloneMarket")
    except Exception as e:
        log.error(f"Error running market updates: {e}", source="TestCycloneMarket")
        assert False, f"Exception raised during market updates: {e}"
