import pytest
from app.ai.matcher import ScheduleMatcher
from app.schemas.matching_schema import ScheduleTask


@pytest.fixture
def mock_schedule():
    return [
        ScheduleTask(
            project_id="PROJECT_001",
            task_id="T01",
            task_name="Site Preparation",
            unit="m2",
            planned_quantity=50000.0,
            previous_completed_quantity=20000.0
        ),
        ScheduleTask(
            project_id="PROJECT_001",
            task_id="T02",
            task_name="Earthwork",
            unit="m3",
            planned_quantity=100000.0,
            previous_completed_quantity=50000.0
        ),
        ScheduleTask(
            project_id="PROJECT_001",
            task_id="T03",
            task_name="Drainage",
            unit="m",
            planned_quantity=15000.0,
            previous_completed_quantity=5000.0
        ),
        ScheduleTask(
            project_id="PROJECT_001",
            task_id="T04",
            task_name="Bituminous Road Work",
            unit="m",
            planned_quantity=6000.0,
            previous_completed_quantity=3780.0,
            aliases=["asphalt laying", "dense bituminous macadam", "DBM", "road paving"]
        ),
        ScheduleTask(
            project_id="PROJECT_001",
            task_id="T05",
            task_name="Road Marking",
            unit="m",
            planned_quantity=6000.0,
            previous_completed_quantity=1000.0
        ),
    ]


@pytest.fixture
def matcher(mock_schedule):
    return ScheduleMatcher(schedule_tasks=mock_schedule)