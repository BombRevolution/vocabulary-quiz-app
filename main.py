import json
import os
import sys
import database

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = BASE_DIR

DB_PATH = os.path.join(BASE_DIR, "vocab.db")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
DEFAULT_XLS = "雅思词汇9400词EXCEL词-乱序版.xls"


def resource_path(relative):
    return os.path.join(RESOURCE_DIR, relative)


def load_config():
    defaults = {"daily_new_words": 200, "ignore_case": True, "ignore_punct": False,
                "hint_mode": "reveal", "hint_percent": 30,
                "key_skip": "<Control-d>", "key_hint": "<Control-space>"}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        defaults.update(data)
    else:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(defaults, f, ensure_ascii=False, indent=2)
    return defaults


def ensure_builtin(conn):
    if database.list_books(conn):
        return
    xls = resource_path(DEFAULT_XLS)
    if os.path.exists(xls):
        import importer
        sheet = importer.detect_excel(xls)[0]
        importer.import_book(conn, "雅思词汇9400", xls, sheet, 1, 2)


def main():
    import tkinter as tk
    from ui_theme import enable_dpi_awareness, apply_theme
    from ui_main import MainApp
    enable_dpi_awareness()
    config = load_config()
    conn = database.get_conn(DB_PATH)
    database.init_db(conn)
    ensure_builtin(conn)
    for key, val in config.items():
        database.set_setting(conn, key, val)
    root = tk.Tk()
    apply_theme(root)
    app = MainApp(root, conn, DB_PATH, config)
    root.mainloop()
    conn.close()


if __name__ == "__main__":
    main()