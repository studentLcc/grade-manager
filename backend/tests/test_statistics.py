from tests.test_exams_rosters import seed_base
from tests.test_scores import create_exam_sheet


def create_two_student_exam_sheet(client):
    headers, class_id, course_id, _ = seed_base(client)
    client.post(
        "/api/v1/students",
        headers=headers,
        json={"class_id": class_id, "student_no": "S002", "name": "李四"},
    )
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


def test_exam_summary_defaults_to_normal_scores_only(client):
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
    response = client.get(f"/api/v1/statistics/exams/{exam['id']}/summary", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["overall"]["average_score"] == "88.00"
    assert body["overall"]["pass_rate"] == "100.00"
    assert body["abnormal_counts"]["absent"] == 0
    assert body["missing_score_count"] == 0


def test_segments_and_rankings_use_backend_included_statuses(client):
    headers, exam, sheet = create_two_student_exam_sheet(client)
    subject = sheet["subjects"][0]
    normal_student = [row for row in sheet["students"] if row["student_no"] == "S001"][0]
    absent_student = [row for row in sheet["students"] if row["student_no"] == "S002"][0]
    client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": normal_student["exam_student_id"],
                    "exam_subject_id": subject["exam_subject_id"],
                    "score": "80",
                    "score_status": "normal",
                },
                {
                    "exam_student_id": absent_student["exam_student_id"],
                    "exam_subject_id": subject["exam_subject_id"],
                    "score": None,
                    "score_status": "absent",
                },
            ]
        },
    )

    default_segments = client.get(
        f"/api/v1/statistics/exams/{exam['id']}/segments?type=total&step=10",
        headers=headers,
    )
    assert default_segments.status_code == 200
    assert sum(item["count"] for item in default_segments.json()["items"]) == 1

    included_segments = client.get(
        f"/api/v1/statistics/exams/{exam['id']}/segments"
        f"?type=total&step=10&included_statuses=normal,absent",
        headers=headers,
    )
    assert included_segments.status_code == 200
    assert included_segments.json()["included_statuses"] == ["normal", "absent"]
    assert sum(item["count"] for item in included_segments.json()["items"]) == 2
    assert included_segments.json()["items"][0]["count"] == 1

    default_ranking = client.get(
        f"/api/v1/statistics/exams/{exam['id']}/rankings?rank_type=subject"
        f"&exam_subject_id={sheet['subjects'][0]['exam_subject_id']}&included_statuses=missing",
        headers=headers,
    )
    assert default_ranking.status_code == 200
    assert default_ranking.json()["items"] == []

    ranking = client.get(
        f"/api/v1/statistics/exams/{exam['id']}/rankings?rank_type=subject"
        f"&exam_subject_id={sheet['subjects'][0]['exam_subject_id']}"
        f"&included_statuses=normal,absent",
        headers=headers,
    )
    assert ranking.status_code == 200
    assert ranking.json()["included_statuses"] == ["normal", "absent"]
    assert [item["score"] for item in ranking.json()["items"]] == ["80.00", "0.00"]


def test_rankings_support_page_parameters(client):
    headers, exam, sheet = create_two_student_exam_sheet(client)
    subject = sheet["subjects"][0]
    first_student = [row for row in sheet["students"] if row["student_no"] == "S001"][0]
    second_student = [row for row in sheet["students"] if row["student_no"] == "S002"][0]
    client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": first_student["exam_student_id"],
                    "exam_subject_id": subject["exam_subject_id"],
                    "score": "90",
                    "score_status": "normal",
                },
                {
                    "exam_student_id": second_student["exam_student_id"],
                    "exam_subject_id": subject["exam_subject_id"],
                    "score": "80",
                    "score_status": "normal",
                },
            ]
        },
    )

    response = client.get(
        f"/api/v1/statistics/exams/{exam['id']}/rankings?rank_type=subject"
        f"&exam_subject_id={subject['exam_subject_id']}&page=2&page_size=1",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["page"] == 2
    assert body["page_size"] == 1
    assert body["items"][0]["rank"] == 2
    assert body["items"][0]["name"] == "李四"


def test_segments_support_page_parameters(client):
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

    response = client.get(
        f"/api/v1/statistics/exams/{exam['id']}/segments?type=total&step=10&page=2&page_size=3",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 9
    assert body["page"] == 2
    assert body["page_size"] == 3
    assert len(body["items"]) == 3
    assert body["items"][0]["label"] == "[30, 40)"


def test_segments_can_be_filtered_by_snapshot_class(client):
    headers, exam, sheet = create_exam_sheet(client)
    first_class_id = sheet["students"][0]["class_id"]
    course_id = sheet["subjects"][0]["course_id"]
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
            "class_ids": [first_class_id, second_class_id],
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
    first_class_student = [row for row in sheet["students"] if row["class_id"] == first_class_id][0]
    second_class_student = [row for row in sheet["students"] if row["class_id"] == second_class_id][0]
    subject = sheet["subjects"][0]
    client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": first_class_student["exam_student_id"],
                    "exam_subject_id": subject["exam_subject_id"],
                    "score": "85",
                    "score_status": "normal",
                },
                {
                    "exam_student_id": second_class_student["exam_student_id"],
                    "exam_subject_id": subject["exam_subject_id"],
                    "score": "95",
                    "score_status": "normal",
                },
            ]
        },
    )

    response = client.get(
        f"/api/v1/statistics/exams/{exam['id']}/segments?type=total&step=10&class_id={first_class_id}",
        headers=headers,
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert sum(item["count"] for item in items) == 1
    assert [item for item in items if item["count"] > 0] == [
        {"label": "[80, 90]", "start": "80", "end": "90", "count": 1}
    ]


def test_segments_do_not_create_extra_bucket_when_score_is_on_boundary(client):
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
                    "score": "100",
                    "score_status": "normal",
                }
            ]
        },
    )

    response = client.get(
        f"/api/v1/statistics/exams/{exam['id']}/segments?type=total&step=10",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["items"][-1]["label"] == "[90, 100]"
    assert response.json()["items"][-1]["count"] == 1
    assert "[100, 110]" not in {item["label"] for item in response.json()["items"]}


def test_segments_returns_zero_bucket_when_only_missing_scores_are_included(client):
    headers, exam, sheet = create_exam_sheet(client)

    response = client.get(
        f"/api/v1/statistics/exams/{exam['id']}/segments?type=total&step=10&included_statuses=missing",
        headers=headers,
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["label"] == "[0, 10]"
    assert items[0]["count"] >= 1


def test_summary_excludes_missing_until_explicitly_included(client):
    headers, exam, sheet = create_two_student_exam_sheet(client)
    subject = sheet["subjects"][0]
    scored = [row for row in sheet["students"] if row["student_no"] == "S001"][0]
    client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": scored["exam_student_id"],
                    "exam_subject_id": subject["exam_subject_id"],
                    "score": "80",
                    "score_status": "normal",
                }
            ]
        },
    )

    default_response = client.get(f"/api/v1/statistics/exams/{exam['id']}/summary", headers=headers)
    assert default_response.status_code == 200
    assert default_response.json()["overall"]["average_score"] == "80.00"
    assert default_response.json()["missing_score_count"] == 1

    included_response = client.get(
        f"/api/v1/statistics/exams/{exam['id']}/summary?included_statuses=normal,missing",
        headers=headers,
    )
    assert included_response.status_code == 200
    assert included_response.json()["overall"]["average_score"] == "40.00"


def test_summary_total_thresholds_use_only_included_subject_entries(client):
    headers, exam, sheet = create_exam_sheet(client)
    student = sheet["students"][0]
    math = sheet["subjects"][0]
    english_course_id = client.post(
        "/api/v1/courses",
        headers=headers,
        json={"course_name": "英语"},
    ).json()["id"]
    update_subjects = client.put(
        f"/api/v1/exams/{exam['id']}/subjects",
        headers=headers,
        json={
            "subjects": [
                {
                    "id": math["exam_subject_id"],
                    "course_id": math["course_id"],
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                    "status": "active",
                },
                {
                    "course_id": english_course_id,
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                    "status": "active",
                },
            ]
        },
    )
    assert update_subjects.status_code == 200
    sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    student = sheet["students"][0]
    math = [subject for subject in sheet["subjects"] if subject["course_id"] == math["course_id"]][0]
    client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": student["exam_student_id"],
                    "exam_subject_id": math["exam_subject_id"],
                    "score": "70",
                    "score_status": "normal",
                }
            ]
        },
    )

    response = client.get(f"/api/v1/statistics/exams/{exam['id']}/summary", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["overall"]["pass_rate"] == "100.00"
    assert body["class_comparison"][0]["pass_rate"] == "100.00"


def test_summary_total_thresholds_count_explicitly_included_missing_subjects(client):
    headers, exam, sheet = create_exam_sheet(client)
    student = sheet["students"][0]
    math = sheet["subjects"][0]
    english_course_id = client.post(
        "/api/v1/courses",
        headers=headers,
        json={"course_name": "英语"},
    ).json()["id"]
    update_subjects = client.put(
        f"/api/v1/exams/{exam['id']}/subjects",
        headers=headers,
        json={
            "subjects": [
                {
                    "id": math["exam_subject_id"],
                    "course_id": math["course_id"],
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                    "status": "active",
                },
                {
                    "course_id": english_course_id,
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                    "status": "active",
                },
            ]
        },
    )
    assert update_subjects.status_code == 200
    sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    student = sheet["students"][0]
    math = [subject for subject in sheet["subjects"] if subject["course_id"] == math["course_id"]][0]
    client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": student["exam_student_id"],
                    "exam_subject_id": math["exam_subject_id"],
                    "score": "70",
                    "score_status": "normal",
                }
            ]
        },
    )

    response = client.get(
        f"/api/v1/statistics/exams/{exam['id']}/summary?included_statuses=normal,missing",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["overall"]["pass_rate"] == "0.00"
    assert body["class_comparison"][0]["pass_rate"] == "0.00"


def test_student_history_and_class_overview_use_exam_snapshot_class(client):
    headers, exam, sheet = create_exam_sheet(client)
    original_class_id = sheet["students"][0]["class_id"]
    student_id = sheet["students"][0]["student_id"]
    subject = sheet["subjects"][0]
    second_class_id = client.post(
        "/api/v1/classes",
        headers=headers,
        json={"name": "二班", "grade": "七年级", "academic_year": "2026-2027"},
    ).json()["id"]
    move = client.patch(
        f"/api/v1/students/{student_id}",
        headers=headers,
        json={"class_id": second_class_id},
    )
    assert move.status_code == 200
    client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": sheet["students"][0]["exam_student_id"],
                    "exam_subject_id": subject["exam_subject_id"],
                    "score": "77",
                    "score_status": "normal",
                }
            ]
        },
    )

    history = client.get(f"/api/v1/statistics/students/{student_id}/history", headers=headers)
    assert history.status_code == 200
    assert history.json()["items"][0]["class_id"] == original_class_id

    original_overview = client.get(
        f"/api/v1/statistics/classes/{original_class_id}/overview",
        headers=headers,
    )
    assert original_overview.status_code == 200
    assert original_overview.json()["items"][0]["average_score"] == "77.00"

    moved_overview = client.get(
        f"/api/v1/statistics/classes/{second_class_id}/overview",
        headers=headers,
    )
    assert moved_overview.status_code == 200
    assert moved_overview.json()["items"] == []
