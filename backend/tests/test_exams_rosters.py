from tests.test_classes_students_courses_schedules import auth_headers


def seed_base(client):
    headers = auth_headers(client, "teacher1")
    class_id = client.post(
        "/api/v1/classes",
        headers=headers,
        json={"name": "一班", "grade": "七年级", "academic_year": "2026-2027"},
    ).json()["id"]
    course_id = client.post(
        "/api/v1/courses",
        headers=headers,
        json={"course_name": "数学"},
    ).json()["id"]
    student_id = client.post(
        "/api/v1/students",
        headers=headers,
        json={"class_id": class_id, "student_no": "S001", "name": "张三"},
    ).json()["id"]
    return headers, class_id, course_id, student_id


def test_create_exam_with_classes_subjects_and_snapshot(client):
    headers, class_id, course_id, student_id = seed_base(client)
    response = client.post(
        "/api/v1/exams",
        headers=headers,
        json={
            "name": "期中考试",
            "exam_type": "school",
            "term": "2026-2027-1",
            "remark": "",
            "class_ids": [class_id],
            "subjects": [
                {
                    "course_id": course_id,
                    "full_score": "100.00",
                    "pass_score": "60.00",
                    "excellent_score": "90.00",
                    "exam_date": "2026-10-20",
                    "remark": "",
                }
            ],
        },
    )
    assert response.status_code == 201
    exam = response.json()
    assert exam["name"] == "期中考试"
    assert exam["classes"][0]["id"] == class_id
    assert exam["subjects"][0]["course_id"] == course_id

    sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers)
    assert sheet.status_code == 200
    assert sheet.json()["students"][0]["student_id"] == student_id


def test_list_exams_and_patch_exam_setup_updates(client):
    headers, class_id, course_id, _ = seed_base(client)
    second_class_id = client.post(
        "/api/v1/classes",
        headers=headers,
        json={"name": "二班", "grade": "七年级", "academic_year": "2026-2027"},
    ).json()["id"]
    second_course_id = client.post(
        "/api/v1/courses",
        headers=headers,
        json={"course_name": "语文"},
    ).json()["id"]
    exam = client.post(
        "/api/v1/exams",
        headers=headers,
        json={
            "name": "期中考试",
            "exam_type": "school",
            "term": "2026-2027-1",
            "class_ids": [class_id],
            "subjects": [{"course_id": course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"}],
        },
    ).json()

    exam_list = client.get("/api/v1/exams", headers=headers)
    assert exam_list.status_code == 200
    assert exam_list.json()["total"] == 1
    assert exam_list.json()["items"][0]["id"] == exam["id"]

    classes = client.patch(
        f"/api/v1/exams/{exam['id']}/classes",
        headers=headers,
        json={"class_ids": [class_id, second_class_id]},
    )
    assert classes.status_code == 200
    assert {item["id"] for item in classes.json()["classes"]} == {class_id, second_class_id}

    subjects = client.patch(
        f"/api/v1/exams/{exam['id']}/subjects",
        headers=headers,
        json={
            "subjects": [
                {"id": exam["subjects"][0]["id"], "course_id": course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"},
                {"course_id": second_course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"},
            ]
        },
    )
    assert subjects.status_code == 200
    assert {item["course_id"] for item in subjects.json()["subjects"]} == {course_id, second_course_id}

    deleted = client.delete(f"/api/v1/exams/{exam['id']}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "inactive"

    active_list = client.get("/api/v1/exams", headers=headers)
    assert active_list.status_code == 200
    assert active_list.json()["total"] == 0

    inactive_list = client.get("/api/v1/exams?status=inactive", headers=headers)
    assert inactive_list.status_code == 200
    assert inactive_list.json()["total"] == 1


def test_inactive_exam_score_sheet_does_not_refresh_roster(client):
    headers, class_id, course_id, student_id = seed_base(client)
    exam = client.post(
        "/api/v1/exams",
        headers=headers,
        json={
            "name": "期中考试",
            "exam_type": "school",
            "term": "2026-2027-1",
            "class_ids": [class_id],
            "subjects": [{"course_id": course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"}],
        },
    ).json()
    initial_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers)
    assert initial_sheet.status_code == 200
    assert [row["student_id"] for row in initial_sheet.json()["students"]] == [student_id]

    deleted = client.delete(f"/api/v1/exams/{exam['id']}", headers=headers)
    assert deleted.status_code == 200
    client.post(
        "/api/v1/students",
        headers=headers,
        json={"class_id": class_id, "student_no": "S002", "name": "李四"},
    )

    inactive_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers)
    assert inactive_sheet.status_code == 200
    assert inactive_sheet.json()["exam"]["status"] == "inactive"
    assert [row["student_id"] for row in inactive_sheet.json()["students"]] == [student_id]


def test_exam_rejects_invalid_threshold_order(client):
    headers, class_id, course_id, _ = seed_base(client)
    response = client.post(
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
                    "full_score": "100.00",
                    "pass_score": "95.00",
                    "excellent_score": "90.00",
                }
            ],
        },
    )
    assert response.status_code == 422
    assert response.json()["details"][0]["field"] == "subjects.pass_score"


def test_score_sheet_preserves_created_roster_after_scoring(client):
    headers, class_id, course_id, student_id = seed_base(client)
    exam = client.post(
        "/api/v1/exams",
        headers=headers,
        json={
            "name": "期中考试",
            "exam_type": "school",
            "term": "2026-2027-1",
            "class_ids": [class_id],
            "subjects": [{"course_id": course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"}],
        },
    ).json()
    first_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    exam_student_id = first_sheet["students"][0]["exam_student_id"]
    exam_subject_id = first_sheet["subjects"][0]["exam_subject_id"]

    save = client.put(
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
                }
            ]
        },
    )
    assert save.status_code == 200

    client.post(
        "/api/v1/students",
        headers=headers,
        json={"class_id": class_id, "student_no": "S002", "name": "李四"},
    )
    second_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    assert [row["student_id"] for row in second_sheet["students"]] == [student_id]
    original = second_sheet["students"][0]
    assert original["exam_student_id"] == exam_student_id


def test_score_template_preserves_created_roster_after_scoring(client):
    headers, class_id, course_id, student_id = seed_base(client)
    exam = client.post(
        "/api/v1/exams",
        headers=headers,
        json={
            "name": "期中考试",
            "exam_type": "school",
            "term": "2026-2027-1",
            "class_ids": [class_id],
            "subjects": [{"course_id": course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"}],
        },
    ).json()
    first_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    exam_student_id = first_sheet["students"][0]["exam_student_id"]
    exam_subject_id = first_sheet["subjects"][0]["exam_subject_id"]

    save = client.put(
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
                }
            ]
        },
    )
    assert save.status_code == 200

    client.post(
        "/api/v1/students",
        headers=headers,
        json={"class_id": class_id, "student_no": "S002", "name": "李四"},
    )
    template = client.get(f"/api/v1/exams/{exam['id']}/score-template", headers=headers)
    assert template.status_code == 200

    second_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    assert [row["student_id"] for row in second_sheet["students"]] == [student_id]
    assert second_sheet["students"][0]["exam_student_id"] == exam_student_id


def test_readding_removed_unscored_class_reactivates_existing_roster_rows(client):
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
            "subjects": [{"course_id": course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"}],
        },
    ).json()
    first_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    first_class_student = [row for row in first_sheet["students"] if row["class_id"] == class_id][0]
    second_class_student = [row for row in first_sheet["students"] if row["student_id"] == second_student_id][0]
    second_exam_student_id = second_class_student["exam_student_id"]
    exam_subject_id = first_sheet["subjects"][0]["exam_subject_id"]
    save = client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": first_class_student["exam_student_id"],
                    "exam_subject_id": exam_subject_id,
                    "score": "88",
                    "score_status": "normal",
                    "remark": "",
                }
            ]
        },
    )
    assert save.status_code == 200

    remove = client.put(
        f"/api/v1/exams/{exam['id']}/classes",
        headers=headers,
        json={"class_ids": [class_id]},
    )
    assert remove.status_code == 200
    removed_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    assert {row["class_id"] for row in removed_sheet["students"]} == {class_id}

    readd = client.put(
        f"/api/v1/exams/{exam['id']}/classes",
        headers=headers,
        json={"class_ids": [class_id, second_class_id]},
    )
    assert readd.status_code == 200
    readded_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    restored = [row for row in readded_sheet["students"] if row["student_id"] == second_student_id][0]
    assert restored["exam_student_id"] == second_exam_student_id
    assert len([row for row in readded_sheet["students"] if row["student_id"] == second_student_id]) == 1


def test_removed_class_snapshot_stays_hidden_when_student_moves_to_active_class(client):
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
            "subjects": [{"course_id": course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"}],
        },
    ).json()
    first_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    first_class_student = [row for row in first_sheet["students"] if row["class_id"] == class_id][0]
    second_class_student = [row for row in first_sheet["students"] if row["student_id"] == second_student_id][0]
    exam_subject_id = first_sheet["subjects"][0]["exam_subject_id"]
    save = client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": first_class_student["exam_student_id"],
                    "exam_subject_id": exam_subject_id,
                    "score": "88",
                    "score_status": "normal",
                    "remark": "",
                }
            ]
        },
    )
    assert save.status_code == 200

    remove = client.put(
        f"/api/v1/exams/{exam['id']}/classes",
        headers=headers,
        json={"class_ids": [class_id]},
    )
    assert remove.status_code == 200

    move = client.patch(
        f"/api/v1/students/{second_student_id}",
        headers=headers,
        json={"class_id": class_id},
    )
    assert move.status_code == 200
    refreshed_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()

    assert second_class_student["exam_student_id"] not in {
        row["exam_student_id"] for row in refreshed_sheet["students"]
    }
    assert second_student_id not in {row["student_id"] for row in refreshed_sheet["students"]}


def test_minimal_score_save_rejects_inactive_roster_and_subject_rows(client):
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
            "subjects": [{"course_id": course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"}],
        },
    ).json()
    sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    first_class_student = [row for row in sheet["students"] if row["class_id"] == class_id][0]
    second_class_student = [row for row in sheet["students"] if row["student_id"] == second_student_id][0]
    exam_subject_id = sheet["subjects"][0]["exam_subject_id"]

    save = client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": first_class_student["exam_student_id"],
                    "exam_subject_id": exam_subject_id,
                    "score": "88",
                    "score_status": "normal",
                }
            ]
        },
    )
    assert save.status_code == 200

    remove_class = client.put(
        f"/api/v1/exams/{exam['id']}/classes",
        headers=headers,
        json={"class_ids": [class_id]},
    )
    assert remove_class.status_code == 200
    inactive_student_save = client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": second_class_student["exam_student_id"],
                    "exam_subject_id": exam_subject_id,
                    "score": "77",
                    "score_status": "normal",
                }
            ]
        },
    )
    assert inactive_student_save.status_code == 200
    assert inactive_student_save.json()["success_count"] == 0
    assert inactive_student_save.json()["failure_count"] == 1
    assert inactive_student_save.json()["failed_items"][0]["reason"] == "考试学生或科目已停用"

    readd_class = client.put(
        f"/api/v1/exams/{exam['id']}/classes",
        headers=headers,
        json={"class_ids": [class_id, second_class_id]},
    )
    assert readd_class.status_code == 200
    readded_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    assert not [
        score
        for score in readded_sheet["scores"]
        if score["exam_student_id"] == second_class_student["exam_student_id"]
    ]

    inactivate_subject = client.put(
        f"/api/v1/exams/{exam['id']}/subjects",
        headers=headers,
        json={
            "subjects": [
                {
                    "id": exam_subject_id,
                    "course_id": course_id,
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                    "status": "inactive",
                }
            ]
        },
    )
    assert inactivate_subject.status_code == 200
    inactive_subject_save = client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": first_class_student["exam_student_id"],
                    "exam_subject_id": exam_subject_id,
                    "score": "89",
                    "score_status": "normal",
                }
            ]
        },
    )
    assert inactive_subject_save.status_code == 200
    assert inactive_subject_save.json()["success_count"] == 0
    assert inactive_subject_save.json()["failure_count"] == 1
    assert inactive_subject_save.json()["failed_items"][0]["reason"] == "考试学生或科目已停用"

    reactivate_subject = client.put(
        f"/api/v1/exams/{exam['id']}/subjects",
        headers=headers,
        json={
            "subjects": [
                {
                    "id": exam_subject_id,
                    "course_id": course_id,
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                    "status": "active",
                }
            ]
        },
    )
    assert reactivate_subject.status_code == 200
    reactivated_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    assert reactivated_sheet["scores"][0]["score"] == "88.00"


def test_subject_update_can_add_new_unscored_subject(client):
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
            "subjects": [{"course_id": course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"}],
        },
    ).json()
    sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    existing_subject = sheet["subjects"][0]

    response = client.put(
        f"/api/v1/exams/{exam['id']}/subjects",
        headers=headers,
        json={
            "subjects": [
                {
                    "id": existing_subject["exam_subject_id"],
                    "course_id": existing_subject["course_id"],
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                },
                {
                    "course_id": english_course_id,
                    "full_score": "120",
                    "pass_score": "72",
                    "excellent_score": "108",
                },
            ]
        },
    )

    assert response.status_code == 200
    assert {subject["course_id"] for subject in response.json()["subjects"]} == {
        course_id,
        english_course_id,
    }


def test_subject_update_rejects_removing_scored_subject(client):
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
                {"course_id": english_course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"},
            ],
        },
    ).json()
    sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    exam_student_id = sheet["students"][0]["exam_student_id"]
    scored_subject = [subject for subject in sheet["subjects"] if subject["course_id"] == course_id][0]
    kept_subject = [subject for subject in sheet["subjects"] if subject["course_id"] == english_course_id][0]
    save = client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": exam_student_id,
                    "exam_subject_id": scored_subject["exam_subject_id"],
                    "score": "88",
                    "score_status": "normal",
                    "remark": "",
                }
            ]
        },
    )
    assert save.status_code == 200

    response = client.put(
        f"/api/v1/exams/{exam['id']}/subjects",
        headers=headers,
        json={
            "subjects": [
                {
                    "id": kept_subject["exam_subject_id"],
                    "course_id": kept_subject["course_id"],
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                }
            ]
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    refreshed = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    assert scored_subject["exam_subject_id"] in {subject["exam_subject_id"] for subject in refreshed["subjects"]}


def test_subject_update_rejects_course_change_after_scoring(client):
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
            "subjects": [{"course_id": course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"}],
        },
    ).json()
    sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    exam_student_id = sheet["students"][0]["exam_student_id"]
    exam_subject_id = sheet["subjects"][0]["exam_subject_id"]
    save = client.put(
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
                }
            ]
        },
    )
    assert save.status_code == 200

    response = client.put(
        f"/api/v1/exams/{exam['id']}/subjects",
        headers=headers,
        json={
            "subjects": [
                {
                    "id": exam_subject_id,
                    "course_id": english_course_id,
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                }
            ]
        },
    )

    assert response.status_code == 422
    refreshed = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    assert refreshed["subjects"][0]["course_id"] == course_id
