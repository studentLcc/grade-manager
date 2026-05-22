from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from sqlalchemy.dialects import mysql

from app.core.config import get_settings
from app.modules.dashboard.service import get_recent_exams
from tests.test_exams_rosters import seed_base
from tests.test_scores import create_exam_sheet


def test_dashboard_summary_and_recent_exams(client):
    headers, exam, _ = create_exam_sheet(client)
    summary = client.get("/api/v1/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["class_count"] == 1
    assert summary.json()["student_count"] == 1
    assert summary.json()["course_count"] == 1
    assert summary.json()["pending_score_count"] >= 1

    recent = client.get("/api/v1/dashboard/recent-exams", headers=headers)
    assert recent.status_code == 200
    assert recent.json()["items"][0]["id"] == exam["id"]


def test_recent_exams_order_by_subject_exam_date(client):
    headers, class_id, course_id, _ = seed_base(client)
    future_exam = client.post(
        "/api/v1/exams",
        headers=headers,
        json={
            "name": "期末考试",
            "exam_type": "school",
            "term": "2026-2027-1",
            "class_ids": [class_id],
            "subjects": [
                {
                    "course_id": course_id,
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                    "exam_date": "2026-12-31",
                }
            ],
        },
    ).json()
    client.post(
        "/api/v1/exams",
        headers=headers,
        json={
            "name": "单元测验",
            "exam_type": "quiz",
            "term": "2026-2027-1",
            "class_ids": [class_id],
            "subjects": [
                {
                    "course_id": course_id,
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                    "exam_date": "2026-01-01",
                }
            ],
        },
    )

    recent = client.get("/api/v1/dashboard/recent-exams", headers=headers)

    assert recent.status_code == 200
    assert recent.json()["items"][0]["id"] == future_exam["id"]


def test_recent_exams_query_compiles_without_mysql_nulls_last():
    captured = {}

    class FakeResult:
        def all(self):
            return []

    class FakeSession:
        def execute(self, statement):
            captured["statement"] = statement
            return FakeResult()

    get_recent_exams(FakeSession(), SimpleNamespace(id=1))

    compiled = str(captured["statement"].compile(dialect=mysql.dialect()))
    assert "NULLS LAST" not in compiled


def test_dashboard_today_schedule_uses_configured_timezone(client):
    headers, _, sheet = create_exam_sheet(client)
    weekday = datetime.now(ZoneInfo(get_settings().app_timezone)).isoweekday()
    schedule = client.post(
        "/api/v1/schedules",
        headers=headers,
        json={
            "class_id": sheet["classes"][0]["id"],
            "course_id": sheet["subjects"][0]["course_id"],
            "weekday": weekday,
            "period_no": 1,
            "start_time": "08:00",
            "end_time": "08:45",
        },
    )
    assert schedule.status_code == 201

    response = client.get("/api/v1/dashboard/today-schedule", headers=headers)

    assert response.status_code == 200
    assert response.json()["items"][0]["weekday"] == weekday


def test_dashboard_score_overview_and_class_average_trend(client):
    headers, exam, sheet = create_exam_sheet(client)
    student = sheet["students"][0]
    subject = sheet["subjects"][0]
    client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": student["exam_student_id"],
                    "exam_subject_id": subject["exam_subject_id"],
                    "score": "88",
                    "score_status": "normal",
                }
            ]
        },
    )

    overview = client.get("/api/v1/dashboard/score-overview", headers=headers)
    assert overview.status_code == 200
    assert overview.json()["latest_exam"]["id"] == exam["id"]
    assert overview.json()["average_score"] == "88.00"
    assert overview.json()["abnormal_count"] == 0

    trend = client.get("/api/v1/dashboard/class-average-trend", headers=headers)
    assert trend.status_code == 200
    assert trend.json()["items"][0]["exam_id"] == exam["id"]
    assert trend.json()["items"][0]["class_id"] == student["class_id"]
    assert trend.json()["items"][0]["average_score"] == "88.00"


def test_dashboard_score_overview_excludes_inactive_subject_scores(client):
    headers, exam, sheet = create_exam_sheet(client)
    student = sheet["students"][0]
    subject = sheet["subjects"][0]
    client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": student["exam_student_id"],
                    "exam_subject_id": subject["exam_subject_id"],
                    "score": "88",
                    "score_status": "normal",
                }
            ]
        },
    )
    inactivate = client.put(
        f"/api/v1/exams/{exam['id']}/subjects",
        headers=headers,
        json={
            "subjects": [
                {
                    "id": subject["exam_subject_id"],
                    "course_id": subject["course_id"],
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                    "status": "inactive",
                }
            ]
        },
    )
    assert inactivate.status_code == 200

    overview = client.get("/api/v1/dashboard/score-overview", headers=headers)

    assert overview.status_code == 200
    assert overview.json()["latest_exam"]["id"] == exam["id"]
    assert overview.json()["average_score"] == "0.00"
    assert overview.json()["failing_count"] == 0
