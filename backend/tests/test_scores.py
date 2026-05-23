from tests.test_exams_rosters import seed_base


def create_exam_sheet(client):
    headers, class_id, course_id, _ = seed_base(client)
    exam = client.post(
        "/api/v1/exams",
        headers=headers,
        json={
            "name": "期中考试",
            "exam_type": "school",
            "term": "2026-2027-1",
            "class_ids": [class_id],
            "subjects": [
                {
                    "course_id": course_id,
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                }
            ],
        },
    ).json()
    sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    return headers, exam, sheet


def test_bulk_score_save_returns_item_failures(client):
    headers, exam, sheet = create_exam_sheet(client)
    exam_student_id = sheet["students"][0]["exam_student_id"]
    exam_subject_id = sheet["subjects"][0]["exam_subject_id"]

    response = client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": exam_student_id,
                    "exam_subject_id": exam_subject_id,
                    "score": "88",
                    "score_status": "normal",
                    "remark": "",
                },
                {
                    "exam_student_id": exam_student_id,
                    "exam_subject_id": exam_subject_id,
                    "score": "108",
                    "score_status": "normal",
                    "remark": "",
                },
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success_count"] == 1
    assert body["failure_count"] == 1
    assert body["failed_items"][0]["reason"] == "分数不能超过满分 100.00"


def test_list_score_records_returns_student_subject_rows(client):
    headers, class_id, course_id, _ = seed_base(client)
    english_course_id = client.post(
        "/api/v1/courses",
        headers=headers,
        json={"course_name": "英语"},
    ).json()["id"]
    exam = client.post(
        "/api/v1/exams",
        headers=headers,
        json={
            "name": "期中考试",
            "exam_type": "school",
            "term": "2026-2027-1",
            "class_ids": [class_id],
            "subjects": [
                {"course_id": course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"},
                {"course_id": english_course_id, "full_score": "120", "pass_score": "72", "excellent_score": "108"},
            ],
        },
    ).json()
    sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    student = sheet["students"][0]
    math_subject = [subject for subject in sheet["subjects"] if subject["course_id"] == course_id][0]

    save = client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": student["exam_student_id"],
                    "exam_subject_id": math_subject["exam_subject_id"],
                    "score": "88",
                    "score_status": "normal",
                    "remark": "进步明显",
                }
            ]
        },
    )
    assert save.status_code == 200

    response = client.get("/api/v1/scores", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["page_size"] == 20
    rows = {(row["course_id"], row["student_no"]): row for row in body["items"]}
    saved_row = rows[(course_id, "S001")]
    assert saved_row["exam_id"] == exam["id"]
    assert saved_row["exam_name"] == "期中考试"
    assert saved_row["class_id"] == class_id
    assert saved_row["class_name"] == "一班"
    assert saved_row["student_name"] == "张三"
    assert saved_row["exam_student_id"] == student["exam_student_id"]
    assert saved_row["exam_subject_id"] == math_subject["exam_subject_id"]
    assert saved_row["course_name"] == "数学"
    assert saved_row["full_score"] == "100.00"
    assert saved_row["score"] == "88.00"
    assert saved_row["score_status"] == "normal"
    assert saved_row["remark"] == "进步明显"

    empty_row = rows[(english_course_id, "S001")]
    assert empty_row["course_name"] == "英语"
    assert empty_row["score"] is None
    assert empty_row["score_status"] == "normal"
    assert empty_row["remark"] == ""


def test_list_score_records_filters_by_class_course_status_and_keyword(client):
    headers, class_id, course_id, _ = seed_base(client)
    second_class_id = client.post(
        "/api/v1/classes",
        headers=headers,
        json={"name": "二班", "grade": "七年级", "academic_year": "2026-2027"},
    ).json()["id"]
    client.post(
        "/api/v1/students",
        headers=headers,
        json={"class_id": second_class_id, "student_no": "S002", "name": "李四"},
    )
    exam = client.post(
        "/api/v1/exams",
        headers=headers,
        json={
            "name": "期末考试",
            "exam_type": "school",
            "term": "2026-2027-1",
            "class_ids": [class_id, second_class_id],
            "subjects": [{"course_id": course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"}],
        },
    ).json()
    sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    second_student = [student for student in sheet["students"] if student["class_id"] == second_class_id][0]
    subject = sheet["subjects"][0]
    client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": second_student["exam_student_id"],
                    "exam_subject_id": subject["exam_subject_id"],
                    "score": None,
                    "score_status": "absent",
                    "remark": "病假",
                }
            ]
        },
    )

    response = client.get(
        f"/api/v1/scores?class_id={second_class_id}&course_id={course_id}&score_status=absent&keyword=李四",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["student_name"] == "李四"
    assert body["items"][0]["score_status"] == "absent"
    assert body["items"][0]["remark"] == "病假"


def test_abnormal_score_status_requires_null_score(client):
    headers, exam, sheet = create_exam_sheet(client)
    response = client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": sheet["students"][0]["exam_student_id"],
                    "exam_subject_id": sheet["subjects"][0]["exam_subject_id"],
                    "score": "60",
                    "score_status": "absent",
                }
            ]
        },
    )
    assert response.json()["success_count"] == 0
    assert response.json()["failed_items"][0]["reason"] == "异常状态不能填写数字成绩"


def test_inactive_exam_rejects_score_save(client):
    headers, exam, sheet = create_exam_sheet(client)
    deleted = client.delete(f"/api/v1/exams/{exam['id']}", headers=headers)
    assert deleted.status_code == 200
    inactive_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers)
    assert inactive_sheet.status_code == 200
    assert inactive_sheet.json()["exam"]["status"] == "inactive"

    response = client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": sheet["students"][0]["exam_student_id"],
                    "exam_subject_id": sheet["subjects"][0]["exam_subject_id"],
                    "score": "88",
                    "score_status": "normal",
                    "remark": "",
                }
            ]
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_mixed_batch_inactive_student_failure_does_not_block_valid_score(client):
    headers, class_id, course_id, _ = seed_base(client)
    second_class_id = client.post(
        "/api/v1/classes",
        headers=headers,
        json={"name": "二班", "grade": "七年级", "academic_year": "2026-2027"},
    ).json()["id"]
    second_student_id = client.post(
        "/api/v1/students",
        headers=headers,
        json={"class_id": second_class_id, "student_no": "S002", "name": "李四"},
    ).json()["id"]
    exam = client.post(
        "/api/v1/exams",
        headers=headers,
        json={
            "name": "期中考试",
            "exam_type": "school",
            "term": "2026-2027-1",
            "class_ids": [class_id, second_class_id],
            "subjects": [
                {
                    "course_id": course_id,
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                }
            ],
        },
    ).json()
    sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    active_student = [row for row in sheet["students"] if row["class_id"] == class_id][0]
    inactive_student = [row for row in sheet["students"] if row["student_id"] == second_student_id][0]
    exam_subject_id = sheet["subjects"][0]["exam_subject_id"]

    initial_score = client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": active_student["exam_student_id"],
                    "exam_subject_id": exam_subject_id,
                    "score": "70",
                    "score_status": "normal",
                }
            ]
        },
    )
    assert initial_score.status_code == 200
    remove_class = client.put(
        f"/api/v1/exams/{exam['id']}/classes",
        headers=headers,
        json={"class_ids": [class_id]},
    )
    assert remove_class.status_code == 200

    response = client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": active_student["exam_student_id"],
                    "exam_subject_id": exam_subject_id,
                    "score": "91",
                    "score_status": "normal",
                },
                {
                    "exam_student_id": inactive_student["exam_student_id"],
                    "exam_subject_id": exam_subject_id,
                    "score": "77",
                    "score_status": "normal",
                },
            ]
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success_count"] == 1
    assert body["failure_count"] == 1
    assert body["failed_items"][0]["reason"] == "考试学生或科目已停用"
    refreshed = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    assert refreshed["scores"] == [
        {
            "exam_student_id": active_student["exam_student_id"],
            "exam_subject_id": exam_subject_id,
            "score": "91.00",
            "score_status": "normal",
            "remark": "",
        }
    ]
