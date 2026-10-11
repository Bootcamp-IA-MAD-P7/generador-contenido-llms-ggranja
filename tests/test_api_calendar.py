from datetime import date

from fastapi.testclient import TestClient

from apps.api.editorial_planning import EditorialPlan, PlannedItem
from apps.api.main import app, editorial_plan_store


client = TestClient(app)


def stored_plan() -> str:
    plan_id = editorial_plan_store.create_id()
    plan = EditorialPlan(
        strategy_id="eighty_twenty",
        strategy_version="1.0.0",
        total_slots=1,
        starts_on=date(2026, 10, 1),
        ends_on=date(2026, 10, 31),
        targets={"VALUE": 1},
        items=(PlannedItem(
            source_ref="content:synthetic-1",
            source_kind="editorial_content",
            strategy_version="1.0.0",
            bucket_key="VALUE",
            platform="instagram",
            format="single_image",
        ),),
    )
    editorial_plan_store.save(plan_id, plan)
    return plan_id


def test_calendar_day_update_persists_a_valid_day() -> None:
    plan_id = stored_plan()
    response = client.patch(
        f"/plans/{plan_id}/items/0/day", json={"day": "2026-10-15"}
    )
    assert response.status_code == 200
    assert response.json()["plan"]["items"][0]["scheduled_on"] == "2026-10-15"
    reloaded = client.get(f"/plans/{plan_id}")
    assert reloaded.json()["plan"]["items"][0]["scheduled_on"] == "2026-10-15"


def test_calendar_day_update_rejects_out_of_range_days_and_missing_items() -> None:
    plan_id = stored_plan()
    outside = client.patch(
        f"/plans/{plan_id}/items/0/day", json={"day": "2026-11-01"}
    )
    assert outside.status_code == 422
    absent = client.patch(
        f"/plans/{plan_id}/items/1/day", json={"day": "2026-10-15"}
    )
    assert absent.status_code == 404
    current = client.get(f"/plans/{plan_id}")
    assert current.json()["plan"]["items"][0]["scheduled_on"] is None
