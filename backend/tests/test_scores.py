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
