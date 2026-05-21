from io import BytesIO
from zipfile import ZipFile

from openpyxl import Workbook

from tests.test_exams_rosters import seed_base
from tests.test_scores import create_exam_sheet


def score_workbook(student_no, subject_name, value):
    wb = Workbook()
    ws = wb.active
    ws.append(["student_no", "student_name", "class_name", subject_name])
    ws.append([student_no, "张三", "一班", value])
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream


def malformed_xlsx_zip_bytes():
    stream = BytesIO()
    with ZipFile(stream, "w") as archive:
        archive.writestr("dummy.txt", "not an Excel workbook")
    stream.seek(0)
    return stream


def malformed_workbook_xml_xlsx_bytes():
    base = score_workbook("S001", "数学", "88")
    stream = BytesIO()
    with ZipFile(base) as source, ZipFile(stream, "w") as target:
        for item in source.infolist():
            data = b"<workbook><broken></workbook>" if item.filename == "xl/workbook.xml" else source.read(item.filename)
            target.writestr(item, data)
    stream.seek(0)
    return stream


def score_workbook_with_headers(headers, rows):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream


def create_two_subject_exam_sheet(client):
    headers, class_id, math_id, _ = seed_base(client)
    chinese_id = client.post(
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
            "subjects": [
                {
                    "course_id": math_id,
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                },
                {
                    "course_id": chinese_id,
                    "full_score": "100",
                    "pass_score": "60",
                    "excellent_score": "90",
                },
            ],
        },
    ).json()
    sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    return headers, exam, sheet


def test_score_import_uses_exam_snapshot_and_records_invalid_rows(client):
    headers, exam, sheet = create_exam_sheet(client)
    file_obj = score_workbook("S001", sheet["subjects"][0]["course_name"], "108")

    response = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={
            "file": (
                "scores.xlsx",
                file_obj,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success_count"] == 0
    assert body["failed_count"] == 1
    assert body["status"] == "failed"


def test_score_import_rejects_non_finite_score_value(client):
    headers, exam, sheet = create_exam_sheet(client)
    subject_name = sheet["subjects"][0]["course_name"]
    file_obj = score_workbook("S001", subject_name, "NaN")

    response = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={
            "file": (
                "scores.xlsx",
                file_obj,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["success_count"] == 0
    assert body["failed_count"] == 1
    errors = client.get(f"/api/v1/imports/{body['batch_id']}/errors", headers=headers).json()
    assert errors["items"][0]["field"] == subject_name
    assert errors["items"][0]["reason"] == "成绩格式不支持"
    refreshed = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    assert refreshed["scores"] == []


def test_score_import_writes_valid_score_and_rejects_existing_without_overwrite(client):
    headers, exam, sheet = create_exam_sheet(client)
    subject_name = sheet["subjects"][0]["course_name"]
    first_file = score_workbook("S001", subject_name, "88")

    first = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={
            "file": (
                "scores.xlsx",
                first_file,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert first.status_code == 200
    assert first.json()["status"] == "success"

    duplicate_file = score_workbook("S001", subject_name, "91")
    duplicate = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={
            "file": (
                "scores.xlsx",
                duplicate_file,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert duplicate.status_code == 200
    assert duplicate.json()["status"] == "failed"
    refreshed = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    assert refreshed["scores"][0]["score"] == "88.00"


def test_score_import_writes_valid_cell_when_same_row_has_invalid_cell(client):
    headers, exam, sheet = create_two_subject_exam_sheet(client)
    subject_names = [subject["course_name"] for subject in sheet["subjects"]]
    file_obj = score_workbook_with_headers(
        ["student_no", "student_name", "class_name", subject_names[0], subject_names[1]],
        [["S001", "张三", "一班", "88", "108"]],
    )

    response = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={
            "file": (
                "scores.xlsx",
                file_obj,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success_count"] == 1
    assert body["failed_count"] == 1
    assert body["status"] == "partial_success"
    refreshed = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    assert refreshed["scores"] == [
        {
            "exam_student_id": sheet["students"][0]["exam_student_id"],
            "exam_subject_id": sheet["subjects"][0]["exam_subject_id"],
            "score": "88.00",
            "score_status": "normal",
            "remark": "",
        }
    ]


def test_score_import_writes_valid_subject_cell_when_unknown_subject_cell_exists(client):
    headers, exam, sheet = create_exam_sheet(client)
    subject_name = sheet["subjects"][0]["course_name"]
    unknown_subject = "不存在科目"
    file_obj = score_workbook_with_headers(
        ["student_no", "student_name", "class_name", subject_name, unknown_subject],
        [["S001", "张三", "一班", "88", "91"]],
    )

    response = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={
            "file": (
                "scores.xlsx",
                file_obj,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial_success"
    assert body["success_count"] == 1
    assert body["failed_count"] == 1

    refreshed = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    assert refreshed["scores"] == [
        {
            "exam_student_id": sheet["students"][0]["exam_student_id"],
            "exam_subject_id": sheet["subjects"][0]["exam_subject_id"],
            "score": "88.00",
            "score_status": "normal",
            "remark": "",
        }
    ]
    errors = client.get(f"/api/v1/imports/{body['batch_id']}/errors", headers=headers).json()
    assert errors["items"][0]["field"] == unknown_subject


def test_score_import_duplicate_seen_even_when_first_cell_invalid(client):
    headers, exam, sheet = create_exam_sheet(client)
    subject_name = sheet["subjects"][0]["course_name"]
    file_obj = score_workbook_with_headers(
        ["student_no", "student_name", "class_name", subject_name],
        [["S001", "张三", "一班", "108"], ["S001", "张三", "一班", "88"]],
    )

    response = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={
            "file": (
                "scores.xlsx",
                file_obj,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success_count"] == 0
    assert body["failed_count"] == 2
    errors = client.get(f"/api/v1/imports/{body['batch_id']}/errors", headers=headers).json()
    assert [item["reason"] for item in errors["items"]] == [
        "分数不能超过满分 100.00",
        "同一文件中成绩重复",
    ]
    refreshed = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    assert refreshed["scores"] == []


def test_score_import_duplicate_subject_headers_are_reported_per_cell(client):
    headers, exam, sheet = create_exam_sheet(client)
    subject_name = sheet["subjects"][0]["course_name"]
    file_obj = score_workbook_with_headers(
        ["student_no", "student_name", "class_name", subject_name, subject_name],
        [["S001", "张三", "一班", "88", "91"]],
    )

    response = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={
            "file": (
                "scores.xlsx",
                file_obj,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success_count"] == 1
    assert body["failed_count"] == 1
    errors = client.get(f"/api/v1/imports/{body['batch_id']}/errors", headers=headers).json()
    assert errors["items"][0]["field"] == subject_name
    assert errors["items"][0]["reason"] == "同一文件中成绩重复"


def test_score_import_corrupt_upload_returns_failed_batch(client):
    headers, exam, _ = create_exam_sheet(client)

    response = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={
            "file": (
                "scores.xlsx",
                BytesIO(b"not an excel workbook"),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["success_count"] == 0
    assert body["failed_count"] == 1
    errors = client.get(f"/api/v1/imports/{body['batch_id']}/errors", headers=headers).json()
    assert errors["items"][0]["field"] == "file"


def test_score_import_malformed_xlsx_zip_returns_failed_batch(client):
    headers, exam, _ = create_exam_sheet(client)

    response = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={
            "file": (
                "scores.xlsx",
                malformed_xlsx_zip_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["success_count"] == 0
    assert body["failed_count"] == 1
    errors = client.get(f"/api/v1/imports/{body['batch_id']}/errors", headers=headers).json()
    assert errors["items"][0]["field"] == "file"


def test_score_import_malformed_workbook_xml_returns_failed_batch(client):
    headers, exam, _ = create_exam_sheet(client)

    response = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={
            "file": (
                "scores.xlsx",
                malformed_workbook_xml_xlsx_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["success_count"] == 0
    assert body["failed_count"] == 1
    errors = client.get(f"/api/v1/imports/{body['batch_id']}/errors", headers=headers).json()
    assert errors["items"][0]["field"] == "file"


def test_score_import_wrong_extension_returns_failed_batch(client):
    headers, exam, _ = create_exam_sheet(client)

    response = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={"file": ("scores.csv", BytesIO(b"student_no,name\nS001,88"), "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["success_count"] == 0
    assert body["failed_count"] == 1
    errors = client.get(f"/api/v1/imports/{body['batch_id']}/errors", headers=headers).json()
    assert errors["items"][0]["field"] == "file"


def test_score_import_clamps_overlong_upload_filename(client):
    headers, exam, sheet = create_exam_sheet(client)
    subject_name = sheet["subjects"][0]["course_name"]
    long_filename = f"{'scores-' * 45}.xlsx"

    response = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={
            "file": (
                long_filename,
                score_workbook("S001", subject_name, "88"),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    batch = client.get(f"/api/v1/imports/{body['batch_id']}", headers=headers).json()
    assert len(batch["file_name"]) <= 255


def test_score_import_clamps_overlong_unknown_subject_header_field(client):
    headers, exam, _ = create_exam_sheet(client)
    long_header = "未知科目" * 40
    file_obj = score_workbook_with_headers(
        ["student_no", "student_name", "class_name", long_header],
        [["S001", "张三", "一班", "88"]],
    )

    response = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={
            "file": (
                "scores.xlsx",
                file_obj,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    errors = client.get(f"/api/v1/imports/{body['batch_id']}/errors", headers=headers).json()
    assert len(errors["items"][0]["field"]) <= 100


def test_score_import_clamps_overlong_raw_error_payload(client):
    headers, exam, sheet = create_exam_sheet(client)
    subject_name = sheet["subjects"][0]["course_name"]
    long_score = "9" * 20_000

    response = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={
            "file": (
                "scores.xlsx",
                score_workbook("S001", subject_name, long_score),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    errors = client.get(f"/api/v1/imports/{body['batch_id']}/errors", headers=headers).json()
    error = errors["items"][0]
    assert error["field"] == subject_name
    assert len(error["raw_value"]) <= 10_000
    assert len(error["raw_data"]) <= 10_000
