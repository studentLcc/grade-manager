from io import BytesIO

from openpyxl import Workbook

STUDENT_TEMPLATE_HEADERS = ["student_no", "name", "gender", "status", "remark"]


def build_student_import_template() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "students"
    sheet.append(STUDENT_TEMPLATE_HEADERS)

    for column, width in {"A": 16, "B": 14, "C": 10, "D": 14, "E": 24}.items():
        sheet.column_dimensions[column].width = width

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
