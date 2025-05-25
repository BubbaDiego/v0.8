import pytest

from data.data_locker import DataLocker
from alert_core.alert_core import AlertCore


@pytest.mark.asyncio
async def test_create_all_alerts_raises_typeerror(tmp_path, monkeypatch):
    monkeypatch.setattr(DataLocker, "_seed_modifiers_if_empty", lambda self: None)
    monkeypatch.setattr(DataLocker, "_seed_wallets_if_empty", lambda self: None)
    monkeypatch.setattr(DataLocker, "_seed_thresholds_if_empty", lambda self: None)

    dl = DataLocker(str(tmp_path / "core.db"))
    core = AlertCore(dl)

    with pytest.raises(TypeError):
        await core.create_all_alerts()

    dl.db.close()
