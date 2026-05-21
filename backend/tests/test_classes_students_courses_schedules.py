import pytest


def auth_headers(client, username):
    client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "strong-password", "display_name": username},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "strong-password"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_teacher_scoped_classes_students_courses_and_schedules(client):
    t1 = auth_headers(client, "teacher1")
    t2 = auth_headers(client, "teacher2")

    class_response = client.post(
        "/api/v1/classes",
        headers=t1,
        json={"name": "一班", "grade": "七年级", "academic_year": "2026-2027", "remark": ""},
    )
    assert class_response.status_code == 201
    class_id = class_response.json()["id"]

    assert client.get("/api/v1/classes", headers=t2).json()["total"] == 0

    student = client.post(
        "/api/v1/students",
        headers=t1,
        json={"class_id": class_id, "student_no": "S001", "name": "张三", "gender": "男"},
    )
    assert student.status_code == 201

    duplicate = client.post(
        "/api/v1/students",
        headers=t1,
        json={"class_id": class_id, "student_no": "S001", "name": "李四"},
    )
    assert duplicate.status_code == 409

    course = client.post(
        "/api/v1/courses",
        headers=t1,
        json={"course_name": "数学", "remark": ""},
    )
    assert course.status_code == 201
    course_id = course.json()["id"]

    schedule = client.post(
        "/api/v1/schedules",
        headers=t1,
        json={
            "class_id": class_id,
            "course_id": course_id,
            "weekday": 1,
            "period_no": 1,
            "start_time": "08:00",
            "end_time": "08:45",
            "location": "教学楼 A101",
        },
    )
    assert schedule.status_code == 201


def test_schedule_rejects_invalid_time_order(client):
    headers = auth_headers(client, "teacher1")
    class_id = client.post(
        "/api/v1/classes",
        headers=headers,
        json={"name": "一班", "grade": "七年级", "academic_year": "2026-2027"},
    ).json()["id"]
    course_id = client.post(
        "/api/v1/courses",
        headers=headers,
        json={"course_name": "语文"},
    ).json()["id"]

    response = client.post(
        "/api/v1/schedules",
        headers=headers,
        json={
            "class_id": class_id,
            "course_id": course_id,
            "weekday": 1,
            "period_no": 1,
            "start_time": "09:00",
            "end_time": "08:45",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_update_rejects_explicit_null_for_required_fields(client):
    headers = auth_headers(client, "teacher1")
    class_id = client.post(
        "/api/v1/classes",
        headers=headers,
        json={"name": "一班", "grade": "七年级", "academic_year": "2026-2027"},
    ).json()["id"]
    course_id = client.post(
        "/api/v1/courses",
        headers=headers,
        json={"course_name": "语文"},
    ).json()["id"]
    student_id = client.post(
        "/api/v1/students",
        headers=headers,
        json={"class_id": class_id, "student_no": "S001", "name": "张三"},
    ).json()["id"]
    schedule_id = client.post(
        "/api/v1/schedules",
        headers=headers,
        json={"class_id": class_id, "course_id": course_id, "weekday": 1, "period_no": 1},
    ).json()["id"]

    class_response = client.patch(
        f"/api/v1/classes/{class_id}",
        headers=headers,
        json={"name": None},
    )
    assert class_response.status_code == 422
    assert class_response.json()["code"] == "VALIDATION_ERROR"

    student_response = client.patch(
        f"/api/v1/students/{student_id}",
        headers=headers,
        json={"student_no": None},
    )
    assert student_response.status_code == 422
    assert student_response.json()["code"] == "VALIDATION_ERROR"

    course_response = client.patch(
        f"/api/v1/courses/{course_id}",
        headers=headers,
        json={"course_name": None},
    )
    assert course_response.status_code == 422
    assert course_response.json()["code"] == "VALIDATION_ERROR"

    schedule_response = client.patch(
        f"/api/v1/schedules/{schedule_id}",
        headers=headers,
        json={"weekday": None},
    )
    assert schedule_response.status_code == 422
    assert schedule_response.json()["code"] == "VALIDATION_ERROR"


def test_update_rejects_null_and_invalid_status(client):
    headers = auth_headers(client, "teacher1")
    class_id = client.post(
        "/api/v1/classes",
        headers=headers,
        json={"name": "一班", "grade": "七年级", "academic_year": "2026-2027"},
    ).json()["id"]

    null_status = client.patch(
        f"/api/v1/classes/{class_id}",
        headers=headers,
        json={"status": None},
    )
    assert null_status.status_code == 422
    assert null_status.json()["code"] == "VALIDATION_ERROR"

    invalid_status = client.patch(
        f"/api/v1/classes/{class_id}",
        headers=headers,
        json={"status": "deleted"},
    )
    assert invalid_status.status_code == 422
    assert invalid_status.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/classes",
        "/api/v1/students",
        "/api/v1/courses",
        "/api/v1/schedules",
    ],
)
def test_list_rejects_invalid_status_filter(client, path):
    headers = auth_headers(client, "teacher1")

    response = client.get(f"{path}?status=deleted", headers=headers)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert response.json()["message"] == "请求参数校验失败"
    assert response.json()["details"][0]["field"] == "status"


def test_default_lists_hide_inactive_records(client):
    headers = auth_headers(client, "teacher1")
    class_id = client.post(
        "/api/v1/classes",
        headers=headers,
        json={"name": "一班", "grade": "七年级", "academic_year": "2026-2027"},
    ).json()["id"]
    course_id = client.post(
        "/api/v1/courses",
        headers=headers,
        json={"course_name": "语文"},
    ).json()["id"]
    student_id = client.post(
        "/api/v1/students",
        headers=headers,
        json={"class_id": class_id, "student_no": "S001", "name": "张三"},
    ).json()["id"]
    schedule_id = client.post(
        "/api/v1/schedules",
        headers=headers,
        json={"class_id": class_id, "course_id": course_id, "weekday": 1, "period_no": 1},
    ).json()["id"]

    assert client.delete(f"/api/v1/schedules/{schedule_id}", headers=headers).status_code == 200
    assert client.delete(f"/api/v1/students/{student_id}", headers=headers).status_code == 200
    assert client.delete(f"/api/v1/courses/{course_id}", headers=headers).status_code == 200
    assert client.delete(f"/api/v1/classes/{class_id}", headers=headers).status_code == 200

    assert client.get("/api/v1/classes", headers=headers).json()["total"] == 0
    assert client.get("/api/v1/students", headers=headers).json()["total"] == 0
    assert client.get("/api/v1/courses", headers=headers).json()["total"] == 0
    assert client.get("/api/v1/schedules", headers=headers).json()["total"] == 0

    assert client.get("/api/v1/classes?status=inactive", headers=headers).json()["total"] == 1
    assert client.get("/api/v1/students?status=inactive", headers=headers).json()["total"] == 1
    assert client.get("/api/v1/courses?status=inactive", headers=headers).json()["total"] == 1
    assert client.get("/api/v1/schedules?status=inactive", headers=headers).json()["total"] == 1


def test_deleted_schedule_slot_can_be_recreated(client):
    headers = auth_headers(client, "teacher1")
    class_id = client.post(
        "/api/v1/classes",
        headers=headers,
        json={"name": "一班", "grade": "七年级", "academic_year": "2026-2027"},
    ).json()["id"]
    course_id = client.post(
        "/api/v1/courses",
        headers=headers,
        json={"course_name": "语文"},
    ).json()["id"]
    first = client.post(
        "/api/v1/schedules",
        headers=headers,
        json={
            "class_id": class_id,
            "course_id": course_id,
            "weekday": 1,
            "period_no": 1,
            "location": "旧教室",
        },
    )
    assert first.status_code == 201

    delete = client.delete(f"/api/v1/schedules/{first.json()['id']}", headers=headers)
    assert delete.status_code == 200
    assert delete.json()["status"] == "inactive"

    recreated = client.post(
        "/api/v1/schedules",
        headers=headers,
        json={
            "class_id": class_id,
            "course_id": course_id,
            "weekday": 1,
            "period_no": 1,
            "location": "新教室",
        },
    )
    assert recreated.status_code == 201
    assert recreated.json()["id"] == first.json()["id"]
    assert recreated.json()["status"] == "active"
    assert recreated.json()["location"] == "新教室"
