import sys
import os
import pytest
import asyncio
from cyclone import Cyclone

@pytest.fixture
def cyclone_instance():
    return Cyclone(poll_interval=5)

def test_run_market_updates(cyclone_instance):
    asyncio.run(cyclone_instance.run_market_updates())

def test_run_position_updates(cyclone_instance):
    asyncio.run(cyclone_instance.run_position_updates())

def test_run_enrich_positions(cyclone_instance):
    asyncio.run(cyclone_instance.run_enrich_positions())

def test_run_update_hedges(cyclone_instance):
    asyncio.run(cyclone_instance.run_update_hedges())

def test_run_alert_updates(cyclone_instance):
    asyncio.run(cyclone_instance.run_alert_updates())

def test_run_system_updates(cyclone_instance):
    asyncio.run(cyclone_instance.run_system_updates())
