"""Скрипт для создания красивой структуры Google Sheets для курса.

Создаёт все вкладки с заголовками, формулами, выпадающими списками,
цветовой схемой, чередующимися строками, границами и защитой.

Usage:
    uv run python scripts/setup_sheets.py --spreadsheet-id <ID> --groups ИВТ-1,ИВТ-2
"""

import argparse
import asyncio
import json
import os

from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

ROLES = ["SA/PO", "AI Engineer", "MLOps", "Fullstack"]

# Цветовая палитра
C_WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}
C_LIGHT_GRAY = {"red": 0.95, "green": 0.95, "blue": 0.95}

# Синяя палитра (студенческие вкладки)
C_BLUE_TAB = {"red": 0.26, "green": 0.52, "blue": 0.96}
C_BLUE_HEADER = {"red": 0.81, "green": 0.89, "blue": 0.95}
C_BLUE_BAND = {"red": 0.93, "green": 0.96, "blue": 0.99}

# Оранжевая палитра (преподавательские вкладки)
C_ORANGE_TAB = {"red": 0.96, "green": 0.59, "blue": 0.18}
C_ORANGE_HEADER = {"red": 0.99, "green": 0.91, "blue": 0.79}
C_ORANGE_BAND = {"red": 1.0, "green": 0.96, "blue": 0.91}

# Зелёная палитра (roster)
C_GREEN_TAB = {"red": 0.20, "green": 0.66, "blue": 0.33}
C_GREEN_HEADER = {"red": 0.85, "green": 0.94, "blue": 0.87}
C_GREEN_BAND = {"red": 0.93, "green": 0.98, "blue": 0.94}

# Фиолетовая палитра (results)
C_PURPLE_TAB = {"red": 0.61, "green": 0.28, "blue": 0.85}
C_PURPLE_HEADER = {"red": 0.90, "green": 0.83, "blue": 0.96}
C_PURPLE_BAND = {"red": 0.95, "green": 0.93, "blue": 0.99}

# Золотая палитра (leaderboard)
C_GOLD_TAB = {"red": 0.91, "green": 0.73, "blue": 0.15}
C_GOLD_HEADER = {"red": 0.99, "green": 0.95, "blue": 0.80}
C_GOLD_BAND = {"red": 1.0, "green": 0.98, "blue": 0.91}

# Конфигурация вкладок
SHEETS_CONFIG = {
    "students": {
        "headers": ["ФИО", "GitHub Username", "Группа"],
        "col_widths": [280, 200, 120],
        "note": "Студенты заполняют самостоятельно",
        "tab_color": C_BLUE_TAB,
        "header_bg": C_BLUE_HEADER,
        "band_color": C_BLUE_BAND,
        "editable": True,
    },
    "teams": {
        "headers": [
            "Команда",
            "Тема",
            "Участник 1",
            "Роль 1",
            "Участник 2",
            "Роль 2",
            "Участник 3",
            "Роль 3",
            "Участник 4",
            "Роль 4",
            "Участник 5",
            "Роль 5",
        ],
        "col_widths": [180, 280, 150, 120, 150, 120, 150, 120, 150, 120, 150, 120],
        "note": "Участник — GitHub username из students, Роль — из выпадающего списка",
        "tab_color": C_BLUE_TAB,
        "header_bg": C_BLUE_HEADER,
        "band_color": C_BLUE_BAND,
        "editable": True,
    },
    "topics": {
        "headers": ["ID темы", "Название", "Описание", "Кол-во команд"],
        "col_widths": [100, 300, 450, 100],
        "note": "Каталог тем проектов",
        "tab_color": C_BLUE_TAB,
        "header_bg": C_BLUE_HEADER,
        "band_color": C_BLUE_BAND,
        "editable": True,
    },
    "deadlines": {
        "headers": ["Лаба", "Группа", "Дедлайн"],
        "col_widths": [80, 120, 200],
        "note": "Преподаватель устанавливает дедлайны",
        "tab_color": C_ORANGE_TAB,
        "header_bg": C_ORANGE_HEADER,
        "band_color": C_ORANGE_BAND,
        "editable": False,
    },
    "rubrics": {
        "headers": ["Лаба", "Deliverable", "Роль", "Критерий", "Макс. балл", "Вес"],
        "col_widths": [80, 150, 130, 350, 100, 80],
        "note": "Критерии оценки (заполняет преподаватель)",
        "tab_color": C_ORANGE_TAB,
        "header_bg": C_ORANGE_HEADER,
        "band_color": C_ORANGE_BAND,
        "editable": False,
    },
    "roster": {
        "headers": ["GitHub Username", "ФИО", "Группа", "Команда", "Роль", "Тема"],
        "col_widths": [200, 280, 120, 200, 150, 350],
        "note": "Автосборка из students + teams. НЕ РЕДАКТИРОВАТЬ!",
        "tab_color": C_GREEN_TAB,
        "header_bg": C_GREEN_HEADER,
        "band_color": C_GREEN_BAND,
        "editable": False,
    },
    "results": {
        "headers": [
            "GitHub",
            "Лаба",
            "Deliverable",
            "Критерий",
            "Балл",
            "Макс",
            "Штраф",
            "Итого",
            "PR",
            "Комментарий",
            "Флаги",
            "Проверено",
        ],
        "col_widths": [130, 50, 110, 200, 50, 50, 60, 60, 200, 200, 120, 150],
        "note": "Заполняется агентом. НЕ РЕДАКТИРОВАТЬ!",
        "tab_color": C_PURPLE_TAB,
        "header_bg": C_PURPLE_HEADER,
        "band_color": C_PURPLE_BAND,
        "editable": False,
    },
    "leaderboard": {
        "headers": ["#", "Команда", "Участники", "Лабы сдано", "Суммарный балл"],
        "col_widths": [50, 250, 100, 100, 130],
        "note": "Обновляется автоматически после каждой проверки. НЕ РЕДАКТИРОВАТЬ!",
        "tab_color": C_GOLD_TAB,
        "header_bg": C_GOLD_HEADER,
        "band_color": C_GOLD_BAND,
        "editable": False,
    },
}


def get_creds(sa_json_path: str) -> ServiceAccountCreds:
    with open(sa_json_path) as f:
        key = json.load(f)
    return ServiceAccountCreds(scopes=SCOPES, **key)


async def setup_spreadsheet(
    spreadsheet_id: str,
    sa_json_path: str,
    groups: list[str],
    labs: int = 5,
):
    creds = get_creds(sa_json_path)
    with open(sa_json_path) as f:
        sa_email = json.load(f)["client_email"]

    async with Aiogoogle(service_account_creds=creds) as ag:
        sheets = await ag.discover("sheets", "v4")

        # 0. Установить en_US локаль (формулы на английском, разделитель — запятая)
        await ag.as_service_account(
            sheets.spreadsheets.batchUpdate(
                spreadsheetId=spreadsheet_id,
                json={
                    "requests": [
                        {
                            "updateSpreadsheetProperties": {
                                "properties": {"locale": "en_US"},
                                "fields": "locale",
                            }
                        }
                    ]
                },
            )
        )

        # 1. Получить текущие вкладки
        spreadsheet = await ag.as_service_account(
            sheets.spreadsheets.get(spreadsheetId=spreadsheet_id)
        )
        existing = {s["properties"]["title"] for s in spreadsheet["sheets"]}

        # 2. Создать вкладки
        add_requests = []
        for idx, (sheet_name, config) in enumerate(SHEETS_CONFIG.items()):
            if sheet_name not in existing:
                add_requests.append(
                    {
                        "addSheet": {
                            "properties": {
                                "title": sheet_name,
                                "index": idx,
                                "tabColorStyle": {"rgbColor": config["tab_color"]},
                                "gridProperties": {
                                    "frozenRowCount": 1,
                                },
                            }
                        }
                    }
                )

        if add_requests:
            await ag.as_service_account(
                sheets.spreadsheets.batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    json={"requests": add_requests},
                )
            )
            print(f"  + Создано {len(add_requests)} вкладок")

        # Перечитаем
        spreadsheet = await ag.as_service_account(
            sheets.spreadsheets.get(spreadsheetId=spreadsheet_id)
        )
        sheet_ids = {
            s["properties"]["title"]: s["properties"]["sheetId"]
            for s in spreadsheet["sheets"]
        }

        # 3. Заголовки
        batch_data = []
        for sheet_name, config in SHEETS_CONFIG.items():
            batch_data.append(
                {"range": f"{sheet_name}!A1", "values": [config["headers"]]}
            )

        await ag.as_service_account(
            sheets.spreadsheets.values.batchUpdate(
                spreadsheetId=spreadsheet_id,
                json={"valueInputOption": "USER_ENTERED", "data": batch_data},
            )
        )
        print("  + Заголовки заполнены")

        # 4. Deadlines
        deadline_rows = []
        for lab in range(1, labs + 1):
            for group in groups:
                deadline_rows.append([str(lab), group, ""])

        if deadline_rows:
            await ag.as_service_account(
                sheets.spreadsheets.values.update(
                    spreadsheetId=spreadsheet_id,
                    range="deadlines!A2",
                    valueInputOption="USER_ENTERED",
                    json={"values": deadline_rows},
                )
            )
            print(f"  + Deadlines: {len(deadline_rows)} строк")

        # 5. Roster формулы (разворачивает teams в отдельные строки)
        # A: username, D: team, E: role, F: topic — через FILTER + вертикальная конкатенация
        # B: full_name, C: group — через INDEX(MATCH()) от username
        roster_a = (
            '=IFERROR({FILTER(teams!C2:C,teams!C2:C<>"");'
            'FILTER(teams!E2:E,teams!E2:E<>"");'
            'FILTER(teams!G2:G,teams!G2:G<>"");'
            'FILTER(teams!I2:I,teams!I2:I<>"");'
            'IFERROR(FILTER(teams!K2:K,teams!K2:K<>""),{})},"")'
        )
        roster_d = (
            '=IFERROR({FILTER(teams!A2:A,teams!C2:C<>"");'
            'FILTER(teams!A2:A,teams!E2:E<>"");'
            'FILTER(teams!A2:A,teams!G2:G<>"");'
            'FILTER(teams!A2:A,teams!I2:I<>"");'
            'IFERROR(FILTER(teams!A2:A,teams!K2:K<>""),{})},"")'
        )
        roster_e = (
            '=IFERROR({FILTER(teams!D2:D,teams!C2:C<>"");'
            'FILTER(teams!F2:F,teams!E2:E<>"");'
            'FILTER(teams!H2:H,teams!G2:G<>"");'
            'FILTER(teams!J2:J,teams!I2:I<>"");'
            'IFERROR(FILTER(teams!L2:L,teams!K2:K<>""),{})},"")'
        )
        roster_f = (
            '=IFERROR({FILTER(teams!B2:B,teams!C2:C<>"");'
            'FILTER(teams!B2:B,teams!E2:E<>"");'
            'FILTER(teams!B2:B,teams!G2:G<>"");'
            'FILTER(teams!B2:B,teams!I2:I<>"");'
            'IFERROR(FILTER(teams!B2:B,teams!K2:K<>""),{})},"")'
        )
        roster_bc = [
            [
                f'=IF(A{i}="","",IFERROR(INDEX(students!A:A,MATCH(A{i},students!B:B,0)),""))',
                f'=IF(A{i}="","",IFERROR(INDEX(students!C:C,MATCH(A{i},students!B:B,0)),""))',
            ]
            for i in range(2, 102)
        ]

        await ag.as_service_account(
            sheets.spreadsheets.values.batchUpdate(
                spreadsheetId=spreadsheet_id,
                json={
                    "valueInputOption": "USER_ENTERED",
                    "data": [
                        {"range": "roster!A2", "values": [[roster_a]]},
                        {"range": "roster!D2", "values": [[roster_d]]},
                        {"range": "roster!E2", "values": [[roster_e]]},
                        {"range": "roster!F2", "values": [[roster_f]]},
                        {"range": "roster!B2:C101", "values": roster_bc},
                    ],
                },
            )
        )
        print("  + Roster: формулы установлены")

        # 6. Topics is_taken
        is_taken = [[f'=IF(B{i}="","",COUNTIF(teams!B:B,B{i}))'] for i in range(2, 52)]
        await ag.as_service_account(
            sheets.spreadsheets.values.update(
                spreadsheetId=spreadsheet_id,
                range="topics!D2:D51",
                valueInputOption="USER_ENTERED",
                json={"values": is_taken},
            )
        )
        print("  + Topics: is_taken формулы")

        # 7. Форматирование
        fmt = []

        for sheet_name, config in SHEETS_CONFIG.items():
            sid = sheet_ids.get(sheet_name)
            if sid is None:
                continue

            num_cols = len(config["headers"])

            # Заморозка + цвет вкладки
            fmt.append(
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sid,
                            "gridProperties": {"frozenRowCount": 1},
                            "tabColorStyle": {"rgbColor": config["tab_color"]},
                        },
                        "fields": "gridProperties.frozenRowCount,tabColorStyle",
                    }
                }
            )

            # Заголовок: жирный, цвет, центр, высота
            fmt.append(
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sid,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "textFormat": {
                                    "bold": True,
                                    "fontSize": 10,
                                    "foregroundColorStyle": {
                                        "rgbColor": {
                                            "red": 0.2,
                                            "green": 0.2,
                                            "blue": 0.2,
                                        }
                                    },
                                },
                                "backgroundColor": config["header_bg"],
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE",
                                "wrapStrategy": "WRAP",
                                "padding": {
                                    "top": 6,
                                    "bottom": 6,
                                    "left": 8,
                                    "right": 8,
                                },
                            }
                        },
                        "fields": (
                            "userEnteredFormat("
                            "textFormat,backgroundColor,"
                            "horizontalAlignment,verticalAlignment,"
                            "wrapStrategy,padding)"
                        ),
                    }
                }
            )

            # Высота заголовка
            fmt.append(
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sid,
                            "dimension": "ROWS",
                            "startIndex": 0,
                            "endIndex": 1,
                        },
                        "properties": {"pixelSize": 42},
                        "fields": "pixelSize",
                    }
                }
            )

            # Ширина колонок
            for i, width in enumerate(config["col_widths"]):
                fmt.append(
                    {
                        "updateDimensionProperties": {
                            "range": {
                                "sheetId": sid,
                                "dimension": "COLUMNS",
                                "startIndex": i,
                                "endIndex": i + 1,
                            },
                            "properties": {"pixelSize": width},
                            "fields": "pixelSize",
                        }
                    }
                )

            # Граница под заголовком
            fmt.append(
                {
                    "updateBorders": {
                        "range": {
                            "sheetId": sid,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "bottom": {
                            "style": "SOLID_MEDIUM",
                            "width": 2,
                            "colorStyle": {
                                "rgbColor": config["tab_color"],
                            },
                        },
                    }
                }
            )

            # Чередующиеся строки (banded range)
            fmt.append(
                {
                    "addBanding": {
                        "bandedRange": {
                            "range": {
                                "sheetId": sid,
                                "startRowIndex": 1,
                                "startColumnIndex": 0,
                                "endColumnIndex": num_cols,
                            },
                            "rowProperties": {
                                "firstBandColorStyle": {"rgbColor": C_WHITE},
                                "secondBandColorStyle": {
                                    "rgbColor": config["band_color"]
                                },
                            },
                        }
                    }
                }
            )

            # Заметка
            if "note" in config:
                fmt.append(
                    {
                        "updateCells": {
                            "range": {
                                "sheetId": sid,
                                "startRowIndex": 0,
                                "endRowIndex": 1,
                                "startColumnIndex": 0,
                                "endColumnIndex": 1,
                            },
                            "rows": [{"values": [{"note": config["note"]}]}],
                            "fields": "note",
                        }
                    }
                )

            # Шрифт данных
            fmt.append(
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sid,
                            "startRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "textFormat": {"fontSize": 10},
                                "verticalAlignment": "MIDDLE",
                                "padding": {
                                    "top": 4,
                                    "bottom": 4,
                                    "left": 6,
                                    "right": 6,
                                },
                            }
                        },
                        "fields": "userEnteredFormat(textFormat,verticalAlignment,padding)",
                    }
                }
            )

        # Защита roster и results
        for protected_sheet in ["roster", "results"]:
            if protected_sheet in sheet_ids:
                fmt.append(
                    {
                        "addProtectedRange": {
                            "protectedRange": {
                                "range": {"sheetId": sheet_ids[protected_sheet]},
                                "description": f"{protected_sheet} — автозаполнение, не редактировать",
                                "editors": {"users": [sa_email]},
                            }
                        }
                    }
                )

        # Защита deadlines и rubrics (только преподаватель + SA)
        for teacher_sheet in ["deadlines", "rubrics"]:
            if teacher_sheet in sheet_ids:
                fmt.append(
                    {
                        "addProtectedRange": {
                            "protectedRange": {
                                "range": {"sheetId": sheet_ids[teacher_sheet]},
                                "description": f"{teacher_sheet} — заполняет преподаватель",
                                "warningOnly": True,
                            }
                        }
                    }
                )

        # Условное форматирование: results flags не пустое → красноватый
        if "results" in sheet_ids:
            fmt.append(
                {
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [
                                {
                                    "sheetId": sheet_ids["results"],
                                    "startRowIndex": 1,
                                    "startColumnIndex": 10,
                                    "endColumnIndex": 11,
                                }
                            ],
                            "booleanRule": {
                                "condition": {
                                    "type": "NOT_BLANK",
                                },
                                "format": {
                                    "backgroundColor": {
                                        "red": 1.0,
                                        "green": 0.85,
                                        "blue": 0.85,
                                    },
                                    "textFormat": {"bold": True},
                                },
                            },
                        },
                        "index": 0,
                    }
                }
            )

        # Условное форматирование: topics занята → зелёный
        if "topics" in sheet_ids:
            fmt.append(
                {
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [
                                {
                                    "sheetId": sheet_ids["topics"],
                                    "startRowIndex": 1,
                                    "startColumnIndex": 0,
                                    "endColumnIndex": 4,
                                }
                            ],
                            "booleanRule": {
                                "condition": {
                                    "type": "CUSTOM_FORMULA",
                                    "values": [{"userEnteredValue": "=$D2>0"}],
                                },
                                "format": {
                                    "backgroundColor": {
                                        "red": 0.85,
                                        "green": 0.95,
                                        "blue": 0.85,
                                    },
                                },
                            },
                        },
                        "index": 0,
                    }
                }
            )

        # Data validation
        # teams: участники (C, E, G, I, K) → выпадающий из students
        for col in [2, 4, 6, 8, 10]:  # C=2, E=4, G=6, I=8, K=10
            fmt.append(
                {
                    "setDataValidation": {
                        "range": {
                            "sheetId": sheet_ids["teams"],
                            "startRowIndex": 1,
                            "startColumnIndex": col,
                            "endColumnIndex": col + 1,
                        },
                        "rule": {
                            "condition": {
                                "type": "ONE_OF_RANGE",
                                "values": [{"userEnteredValue": "=students!B:B"}],
                            },
                            "showCustomUi": True,
                            "strict": False,
                        },
                    }
                }
            )

        # teams: роли (D, F, H, J, L) → выпадающий из ролей
        for col in [3, 5, 7, 9, 11]:  # D=3, F=5, H=7, J=9, L=11
            fmt.append(
                {
                    "setDataValidation": {
                        "range": {
                            "sheetId": sheet_ids["teams"],
                            "startRowIndex": 1,
                            "startColumnIndex": col,
                            "endColumnIndex": col + 1,
                        },
                        "rule": {
                            "condition": {
                                "type": "ONE_OF_LIST",
                                "values": [{"userEnteredValue": r} for r in ROLES],
                            },
                            "showCustomUi": True,
                            "strict": True,
                        },
                    }
                }
            )

        # teams.topic (B) → из topics
        fmt.append(
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_ids["teams"],
                        "startRowIndex": 1,
                        "startColumnIndex": 1,
                        "endColumnIndex": 2,
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_RANGE",
                            "values": [{"userEnteredValue": "=topics!B:B"}],
                        },
                        "showCustomUi": True,
                        "strict": False,
                    },
                }
            }
        )

        # students.group_id
        fmt.append(
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_ids["students"],
                        "startRowIndex": 1,
                        "startColumnIndex": 2,
                        "endColumnIndex": 3,
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [{"userEnteredValue": g} for g in groups],
                        },
                        "showCustomUi": True,
                        "strict": True,
                    },
                }
            }
        )

        # deadlines.lab_id
        fmt.append(
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_ids["deadlines"],
                        "startRowIndex": 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": 1,
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [
                                {"userEnteredValue": str(i)} for i in range(1, labs + 1)
                            ],
                        },
                        "showCustomUi": True,
                    },
                }
            }
        )

        # deadlines.group_id
        fmt.append(
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_ids["deadlines"],
                        "startRowIndex": 1,
                        "startColumnIndex": 1,
                        "endColumnIndex": 2,
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [{"userEnteredValue": g} for g in groups],
                        },
                        "showCustomUi": True,
                    },
                }
            }
        )

        # deadlines.due_at — формат даты
        fmt.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_ids["deadlines"],
                        "startRowIndex": 1,
                        "startColumnIndex": 2,
                        "endColumnIndex": 3,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {
                                "type": "DATE_TIME",
                                "pattern": "dd.MM.yyyy HH:mm",
                            }
                        }
                    },
                    "fields": "userEnteredFormat.numberFormat",
                }
            }
        )

        # results.checked_at — формат даты
        fmt.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_ids["results"],
                        "startRowIndex": 1,
                        "startColumnIndex": 11,
                        "endColumnIndex": 12,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {
                                "type": "DATE_TIME",
                                "pattern": "dd.MM.yyyy HH:mm",
                            }
                        }
                    },
                    "fields": "userEnteredFormat.numberFormat",
                }
            }
        )

        if fmt:
            await ag.as_service_account(
                sheets.spreadsheets.batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    json={"requests": fmt},
                )
            )
            print("  + Оформление, защита, валидация применены")

        # 8. Удалить дефолтные вкладки
        for name in {"Sheet1", "Лист1", "Лист 1"} & set(sheet_ids.keys()):
            try:
                await ag.as_service_account(
                    sheets.spreadsheets.batchUpdate(
                        spreadsheetId=spreadsheet_id,
                        json={
                            "requests": [{"deleteSheet": {"sheetId": sheet_ids[name]}}]
                        },
                    )
                )
                print(f"  + {name} удалён")
            except Exception:
                pass

        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        print(f"\n{'=' * 60}")
        print(f"  Таблица готова: {url}")
        print(f"  Группы: {', '.join(groups)}")
        print(f"  Лабораторных: {labs}")
        print(f"  SA: {sa_email}")
        print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(
        description="Настройка Google Sheets для курса",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s --spreadsheet-id 1abc... --groups ИВТ-1,ИВТ-2
  %(prog)s --spreadsheet-id 1abc... --groups ПИ-1 --labs 7
        """,
    )
    parser.add_argument("--spreadsheet-id", required=True)
    parser.add_argument(
        "--sa-json",
        default=os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "service-account.json"),
    )
    parser.add_argument("--groups", required=True)
    parser.add_argument("--labs", type=int, default=5)

    args = parser.parse_args()
    groups = [g.strip() for g in args.groups.split(",")]

    print(f"Настройка для: {', '.join(groups)} ({args.labs} лаб)\n")

    asyncio.run(
        setup_spreadsheet(
            spreadsheet_id=args.spreadsheet_id,
            sa_json_path=args.sa_json,
            groups=groups,
            labs=args.labs,
        )
    )


if __name__ == "__main__":
    main()
