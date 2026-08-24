import pytest
import pytest_asyncio
from app.bot.worker import omni_bot_worker
from app.api.routes_bot import current_bot_settings

@pytest.mark.asyncio
async def test_omni_bot_pipeline_execution_cycle():
    """Verifies that DATA -> BOT -> OMNI AI ENGINE -> RESULT execution loop functions properly."""
    # Ensure bot is active
    current_bot_settings.bot_active = True
    current_bot_settings.min_confidence_score = 50

    await omni_bot_worker.execute_cycle()
    status = omni_bot_worker.get_pipeline_status()

    assert status["scan_count"] >= 1
    assert "nodes" in status
    assert status["nodes"]["data"]["status"] == "STREAMING_LIVE"
    assert status["nodes"]["bot"]["state"] in ["ACTIVE & AUTO-SCANNING", "PAUSED"]
    assert status["nodes"]["omni_engine"]["status"] == "ACTIVE_VISION"
    assert "settings" in status["nodes"]
    assert "telegram" in status["nodes"]
