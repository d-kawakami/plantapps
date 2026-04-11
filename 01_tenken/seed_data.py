# 点検項目マスタデータ
# Excelファイル（日常点検表2024.xlsm）が入手できたら import_excel.py で上書きしてください
#
# データ構造:
#   code        : 点検番号 (例: "1-1")
#   building    : 建物名   (building_day_map.json の表示名を使用)
#   location    : 点検場所 (例: "エレベーター機械室")
#   description : 点検内容 (詳細、空欄可)
#   day_of_week : 曜日     (1=月 2=火 3=水 4=木 5=金)
#   week_filter : 週番号   (None=毎週 1=第1週 2=第2週 3=第3週 4=第4週)
#   sort_order  : 表示順

import json
from pathlib import Path

def _load_building_name_map() -> dict:
    """building_day_map.default.json の元施設名を building_day_map.json の表示名にマッピングする。
    building_day_map.json が存在しない場合は default.json の名前をそのまま使う。
    両ファイルは同じ順序で施設が並んでいることを前提とする。"""
    base = Path(__file__).parent
    default_path = base / "building_day_map.default.json"
    current_path = base / "building_day_map.json"

    with open(default_path, encoding="utf-8") as f:
        default = json.load(f)
    original_names = list(default["buildings"].keys())

    if current_path.exists():
        with open(current_path, encoding="utf-8") as f:
            current = json.load(f)
        display_names = list(current["buildings"].keys())
    else:
        display_names = original_names  # フォールバック: 元の名前をそのまま使用

    return dict(zip(original_names, display_names))

_BUILDING_NAME_MAP = _load_building_name_map()

def _b(original_name: str) -> str:
    """元施設名 → building_day_map.json の表示名に変換する。"""
    return _BUILDING_NAME_MAP.get(original_name, original_name)

INSPECTION_ITEMS = [

    # ─────────────────────────────────────────
    # 月曜日 (day_of_week=1)
    # ─────────────────────────────────────────

    # 沈砂池棟 (1-1 〜 1-26)
    {"code": "1-1",  "building": _b("沈砂池棟"), "location": "エレベーター機械室",   "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 1},
    {"code": "1-2",  "building": _b("沈砂池棟"), "location": "沈砂池（1系）",        "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 2},
    {"code": "1-3",  "building": _b("沈砂池棟"), "location": "沈砂池（2系）",        "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 3},
    {"code": "1-4",  "building": _b("沈砂池棟"), "location": "スクリーン（1系）",    "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 4},
    {"code": "1-5",  "building": _b("沈砂池棟"), "location": "スクリーン（2系）",    "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 5},
    {"code": "1-6",  "building": _b("沈砂池棟"), "location": "除塵機（1号）",        "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 6},
    {"code": "1-7",  "building": _b("沈砂池棟"), "location": "除塵機（2号）",        "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 7},
    {"code": "1-8",  "building": _b("沈砂池棟"), "location": "沈砂除去ポンプ（1号）","description": "", "day_of_week": 1, "week_filter": None, "sort_order": 8},
    {"code": "1-9",  "building": _b("沈砂池棟"), "location": "沈砂除去ポンプ（2号）","description": "", "day_of_week": 1, "week_filter": None, "sort_order": 9},
    {"code": "1-10", "building": _b("沈砂池棟"), "location": "砂洗浄機",             "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 10},
    {"code": "1-11", "building": _b("沈砂池棟"), "location": "グリットコンベア",     "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 11},
    {"code": "1-12", "building": _b("沈砂池棟"), "location": "流量計（流入）",       "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 12},
    {"code": "1-13", "building": _b("沈砂池棟"), "location": "流量計（越流）",       "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 13},
    {"code": "1-14", "building": _b("沈砂池棟"), "location": "水位計",               "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 14},
    {"code": "1-15", "building": _b("沈砂池棟"), "location": "ポンプ制御盤",         "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 15},
    {"code": "1-16", "building": _b("沈砂池棟"), "location": "受変電設備",           "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 16},
    {"code": "1-17", "building": _b("沈砂池棟"), "location": "コンプレッサー室",     "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 17},
    {"code": "1-18", "building": _b("沈砂池棟"), "location": "換気設備",             "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 18},
    {"code": "1-19", "building": _b("沈砂池棟"), "location": "排水ポンプ",           "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 19},
    {"code": "1-20", "building": _b("沈砂池棟"), "location": "越流堰",               "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 20},
    {"code": "1-21", "building": _b("沈砂池棟"), "location": "ゲート（1号）",        "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 21},
    {"code": "1-22", "building": _b("沈砂池棟"), "location": "ゲート（2号）",        "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 22},
    {"code": "1-23", "building": _b("沈砂池棟"), "location": "消火設備",             "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 23},
    {"code": "1-24", "building": _b("沈砂池棟"), "location": "建物外部（東側）",     "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 24},
    {"code": "1-25", "building": _b("沈砂池棟"), "location": "建物外部（西側）",     "description": "", "day_of_week": 1, "week_filter": None, "sort_order": 25},
    {"code": "1-26", "building": _b("沈砂池棟"), "location": "その他（特記事項確認）","description": "", "day_of_week": 1, "week_filter": None, "sort_order": 26},

    # ─────────────────────────────────────────
    # 火曜日 (day_of_week=2)
    # ─────────────────────────────────────────

    # 処理水再利用設備 (2-1 〜 2-18)
    {"code": "2-1",  "building": _b("処理水再利用設備"), "location": "再利用ポンプ（1号）",    "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 1},
    {"code": "2-2",  "building": _b("処理水再利用設備"), "location": "再利用ポンプ（2号）",    "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 2},
    {"code": "2-3",  "building": _b("処理水再利用設備"), "location": "再利用ポンプ（3号）",    "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 3},
    {"code": "2-4",  "building": _b("処理水再利用設備"), "location": "流量計",                 "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 4},
    {"code": "2-5",  "building": _b("処理水再利用設備"), "location": "逆洗用ポンプ",           "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 5},
    {"code": "2-6",  "building": _b("処理水再利用設備"), "location": "ろ過池（1系）",          "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 6},
    {"code": "2-7",  "building": _b("処理水再利用設備"), "location": "ろ過池（2系）",          "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 7},
    {"code": "2-8",  "building": _b("処理水再利用設備"), "location": "ろ過池（3系）",          "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 8},
    {"code": "2-9",  "building": _b("処理水再利用設備"), "location": "水質計器室",             "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 9},
    {"code": "2-10", "building": _b("処理水再利用設備"), "location": "制御盤",                 "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 10},
    {"code": "2-11", "building": _b("処理水再利用設備"), "location": "受水槽",                 "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 11},
    {"code": "2-12", "building": _b("処理水再利用設備"), "location": "高架水槽",               "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 12},
    {"code": "2-13", "building": _b("処理水再利用設備"), "location": "逆浸透膜設備",           "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 13},
    {"code": "2-14", "building": _b("処理水再利用設備"), "location": "薬品注入設備（防錆剤）", "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 14},
    {"code": "2-15", "building": _b("処理水再利用設備"), "location": "UV殺菌装置",            "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 15},
    {"code": "2-16", "building": _b("処理水再利用設備"), "location": "配管・バルブ類",         "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 16},
    {"code": "2-17", "building": _b("処理水再利用設備"), "location": "排水設備",               "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 17},
    {"code": "2-18", "building": _b("処理水再利用設備"), "location": "建物外部・周辺",         "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 18},

    # 塩素接触棟 (3-1 〜 3-9)
    {"code": "3-1", "building": _b("塩素接触棟"), "location": "塩素接触池（1系）",     "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 1},
    {"code": "3-2", "building": _b("塩素接触棟"), "location": "塩素接触池（2系）",     "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 2},
    {"code": "3-3", "building": _b("塩素接触棟"), "location": "次亜塩素酸注入設備",   "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 3},
    {"code": "3-4", "building": _b("塩素接触棟"), "location": "注入ポンプ（1号）",     "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 4},
    {"code": "3-5", "building": _b("塩素接触棟"), "location": "注入ポンプ（2号）",     "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 5},
    {"code": "3-6", "building": _b("塩素接触棟"), "location": "残塩計",               "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 6},
    {"code": "3-7", "building": _b("塩素接触棟"), "location": "流量計",               "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 7},
    {"code": "3-8", "building": _b("塩素接触棟"), "location": "制御盤・計器類",       "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 8},
    {"code": "3-9", "building": _b("塩素接触棟"), "location": "建物外部",             "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 9},

    # 汚泥調整層 (4-1 〜 4-14)
    {"code": "4-1",  "building": _b("汚泥調整槽"), "location": "制御室 汚泥調整槽10・20",      "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 1},
    {"code": "4-2",  "building": _b("汚泥調整槽"), "location": "空調  汚泥調整槽10・20",      "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 2},
    {"code": "4-3",  "building": _b("汚泥調整槽"), "location": "脱臭機室  汚泥調整槽10・20",  "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 3},
    {"code": "4-4",  "building": _b("汚泥調整槽"), "location": "汚泥ポンプ室  汚泥調整槽10・20",  "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 4},
    {"code": "4-5",  "building": _b("汚泥調整槽"), "location": "かき寄せ機  汚泥調整槽10・20",  "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 5},
    {"code": "4-6",  "building": _b("汚泥調整槽"), "location": "その他  汚泥調整槽10・20",          "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 6},
    {"code": "4-7",  "building": _b("汚泥調整槽"), "location": "制御室 汚泥調整層30-60",          "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 7},
    {"code": "4-8",  "building": _b("汚泥調整槽"), "location": "電気室  汚泥調整層30-60",          "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 8},
    {"code": "4-9",  "building": _b("汚泥調整槽"), "location": "空調・換気ファン  汚泥調整層30-60", "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 9},
    {"code": "4-10", "building": _b("汚泥調整槽"), "location": "脱臭機室  汚泥調整層30-60",         "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 10},
    {"code": "4-11", "building": _b("汚泥調整槽"), "location": "汚泥ポンプ室  汚泥調整層30-60",     "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 11},
    {"code": "4-12", "building": _b("汚泥調整槽"), "location": "かき寄せ機  汚泥調整層30-60",       "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 12},
    {"code": "4-13", "building": _b("汚泥調整槽"), "location": "脱臭機室  汚泥調整層30-60",         "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 13},
    {"code": "4-14", "building": _b("汚泥調整槽"), "location": "その他  汚泥調整層30-60",           "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 14},

    # 管廊（雑排水ポンプ） (5-1 〜 5-3)
    {"code": "5-1", "building": _b("管廊（雑排水ポンプ）"), "location": "管理棟～二次処理棟(No.71・81)", "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 1},
    {"code": "5-2", "building": _b("管廊（雑排水ポンプ）"), "location": "二次処理棟管廊(No.61)", "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 2},
    {"code": "5-3", "building": _b("管廊（雑排水ポンプ）"), "location": "二次処理棟～原水ポンプ室(No.A1・A2)",         "description": "", "day_of_week": 2, "week_filter": None, "sort_order": 3},

    # ─────────────────────────────────────────
    # 水曜日 (day_of_week=3)  ※週フィルタあり
    # ─────────────────────────────────────────

    # 第三ポンプ施設（第1週）
    {"code": "6-1",  "building": _b("第三ポンプ施設"), "location": "高圧電気室",   "description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 1},
    {"code": "6-2",  "building": _b("第三ポンプ施設"), "location": "換気機械室",   "description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 2},
    {"code": "6-3",  "building": _b("第三ポンプ施設"), "location": "消音器室",   "description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 3},
    {"code": "6-4",  "building": _b("第三ポンプ施設"), "location": "発電機室",        "description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 4},
    {"code": "6-5",  "building": _b("第三ポンプ施設"), "location": "ガスタービン点検",     "description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 5},
    {"code": "6-6",  "building": _b("第三ポンプ施設"), "location": "燃料サービスタンク室",  "description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 6},
    {"code": "6-7",  "building": _b("第三ポンプ施設"), "location": "制御室",            "description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 7},
    {"code": "6-8",  "building": _b("第三ポンプ施設"), "location": "消火栓ポンプ室",        "description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 8},
    {"code": "6-9",  "building": _b("第三ポンプ施設"), "location": "ボンベ室","description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 9},
    {"code": "6-10",  "building": _b("第三ポンプ施設"), "location": "脱臭機室","description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 10},
    {"code": "6-11",  "building": _b("第三ポンプ施設"), "location": "低圧電気室","description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 11},
    {"code": "6-12",  "building": _b("第三ポンプ施設"), "location": "換気機械室","description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 12},
    {"code": "6-13",  "building": _b("第三ポンプ施設"), "location": "ろ過水自動給水装置","description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 13},
    {"code": "6-14",  "building": _b("第三ポンプ施設"), "location": "流量計室","description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 14},
    {"code": "6-15",  "building": _b("第三ポンプ施設"), "location": "電動機室","description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 15},
    {"code": "6-16",  "building": _b("第三ポンプ施設"), "location": "汚水ポンプ","description": "", "day_of_week": 3, "week_filter": 1, "sort_order": 16},
    {"code": "6-17",  "building": _b("第三ポンプ施設"),	"location": "床排水ポンプ","description":"","day_of_week" :3,"week_filter" :1,"sort_order" :17},
    {"code": "6-18",  "building": _b("第三ポンプ施設"), "location": "燃料タンク","description":"","day_of_week" :3,"week_filter" :1,"sort_order" :18},
    {"code": "6-19",  "building": _b("第三ポンプ施設"), "location": "各ゲート","description":"","day_of_week" :3,"week_filter" :1,"sort_order" :19},
    {"code": "6-20",  "building": _b("第三ポンプ施設"), "location": "吐出井流量計ピット","description":"","day_of_week" :3,"week_filter" :1,"sort_order" :20},
    {"code": "6-21",  "building": _b("第三ポンプ施設"), "location": "PCB倉庫","description":"","day_of_week" :3,"week_filter" :1,"sort_order" :21},

    # 第二ポンプ施設（第2週）
    {"code": "7-1",  "building": _b("第二ポンプ施設"), "location": "制御室",   "description": "", "day_of_week": 3, "week_filter": 2, "sort_order": 1},
    {"code": "7-2",  "building": _b("第二ポンプ施設"), "location": "電気室",   "description": "", "day_of_week": 3, "week_filter": 2, "sort_order": 2},
    {"code": "7-3",  "building": _b("第二ポンプ施設"), "location": "消火栓ポンプ室", "description": "", "day_of_week": 3, "week_filter": 2, "sort_order": 3},
    {"code": "7-4",  "building": _b("第二ポンプ施設"), "location": "ポンプ室",    "description": "", "day_of_week": 3, "week_filter": 2, "sort_order": 4},
    {"code": "7-5",  "building": _b("第二ポンプ施設"), "location": "エンジン",    "description": "", "day_of_week": 3, "week_filter": 2, "sort_order": 5},
    {"code": "7-6",  "building": _b("第二ポンプ施設"), "location": "ポンプ",      "description": "", "day_of_week": 3, "week_filter": 2, "sort_order": 6},
    {"code": "7-7",  "building": _b("第二ポンプ施設"), "location": "換気機械室",  "description": "", "day_of_week": 3, "week_filter": 2, "sort_order": 7},
    {"code": "7-8",  "building": _b("第二ポンプ施設"), "location": "スクリーン",  "description": "", "day_of_week": 3, "week_filter": 2, "sort_order": 8},
    {"code": "7-9",  "building": _b("第二ポンプ施設"), "location": "燃料タンク", "description": "", "day_of_week": 3, "week_filter": 2, "sort_order": 9},
    {"code": "7-10", "building": _b("第二ポンプ施設"), "location": "その他",     "description": "", "day_of_week": 3, "week_filter": 2, "sort_order": 10},

    # 特高棟（第3週）
    {"code": "8-1",  "building": _b("特高棟"), "location": "換気機械室",        "description": "", "day_of_week": 3, "week_filter": 3, "sort_order": 1},
    {"code": "8-2",  "building": _b("特高棟"), "location": "屋上補機",          "description": "", "day_of_week": 3, "week_filter": 3, "sort_order": 2},
    {"code": "8-3",  "building": _b("特高棟"), "location": "制御室",            "description": "", "day_of_week": 3, "week_filter": 3, "sort_order": 3},
    {"code": "8-4",  "building": _b("特高棟"), "location": "変圧器室",           "description": "", "day_of_week": 3, "week_filter": 3, "sort_order": 4},
    {"code": "8-5",  "building": _b("特高棟"), "location": "高圧盤室",           "description": "", "day_of_week": 3, "week_filter": 3, "sort_order": 5},
    {"code": "8-6",  "building": _b("特高棟"), "location": "ハロンボンベ室",     "description": "", "day_of_week": 3, "week_filter": 3, "sort_order": 6},
    {"code": "8-7",  "building": _b("特高棟"), "location": "空調機械室",         "description": "", "day_of_week": 3, "week_filter": 3, "sort_order": 7},
    {"code": "8-8",  "building": _b("特高棟"), "location": "ケーブルピット室",    "description": "", "day_of_week": 3, "week_filter": 3, "sort_order": 8},
    {"code": "8-9",  "building": _b("特高棟"), "location": "その他",             "description": "", "day_of_week": 3, "week_filter": 3, "sort_order": 9},

    # 滞水池（第3週）
    {"code": "9-1",  "building": _b("滞水池"), "location": "ゲート設備",         "description": "", "day_of_week": 3, "week_filter": 3, "sort_order": 1},
    {"code": "9-2",  "building": _b("滞水池"), "location": "換気・脱臭ファン室",  "description": "", "day_of_week": 3, "week_filter": 3, "sort_order": 2},
    {"code": "9-3",  "building": _b("滞水池"), "location": "返送水ポンプ室",      "description": "", "day_of_week": 3, "week_filter": 3, "sort_order": 3},

    # 第二ポンプ施設（第3週）
    {"code": "7-11",  "building": _b("第二ポンプ施設"), "location": "管理運転",    "description": "", "day_of_week": 3, "week_filter": 3, "sort_order": 1},

    # 中央管理棟（第4週）
    {"code": "10-1",  "building": _b("中央管理棟"), "location": "空調機械室",         "description": "", "day_of_week": 3, "week_filter": 4, "sort_order": 1},
    {"code": "10-2",  "building": _b("中央管理棟"), "location": "スクラバー室",       "description": "", "day_of_week": 3, "week_filter": 4, "sort_order": 2},
    {"code": "10-3",  "building": _b("中央管理棟"), "location": "屋上補機",           "description": "", "day_of_week": 3, "week_filter": 4, "sort_order": 3},
    {"code": "10-4",  "building": _b("中央管理棟"), "location": "中央操作室",         "description": "", "day_of_week": 3, "week_filter": 4, "sort_order": 4},
    {"code": "10-5",  "building": _b("中央管理棟"), "location": "空調機械室",        "description": "", "day_of_week": 3, "week_filter": 4, "sort_order": 5},
    {"code": "10-6",  "building": _b("中央管理棟"), "location": "電気室",            "description": "", "day_of_week": 3, "week_filter": 4, "sort_order": 6},
    {"code": "10-7",  "building": _b("中央管理棟"), "location": "ボイラー室",         "description": "", "day_of_week": 3, "week_filter": 4, "sort_order": 7},
    {"code": "10-8",  "building": _b("中央管理棟"), "location": "旧受水槽室",         "description": "", "day_of_week": 3, "week_filter": 4, "sort_order": 8},
    {"code": "10-9",  "building": _b("中央管理棟"), "location": "空調機械室",         "description": "", "day_of_week": 3, "week_filter": 4, "sort_order": 9},
    {"code": "10-10",  "building": _b("中央管理棟"), "location": "工作室",            "description": "", "day_of_week": 3, "week_filter": 4, "sort_order": 10},
    {"code": "10-11",  "building": _b("中央管理棟"), "location": "水質薬品室",        "description": "", "day_of_week" :3, "week_filter" :4, "sort_order" :11},

    # ホッパー棟（第4週）
    {"code": "11-1",  "building": _b("ホッパー棟"), "location": "沈砂設備（沈砂池棟）", "description": "", "day_of_week": 3, "week_filter": 4, "sort_order": 1},
    {"code": "11-2",  "building": _b("ホッパー棟"), "location": "ホッパー室",          "description": "", "day_of_week": 3, "week_filter": 4, "sort_order": 2},
    {"code": "11-3",  "building": _b("ホッパー棟"), "location": "換気機械室",          "description": "", "day_of_week": 3, "week_filter": 4, "sort_order": 3},
    {"code": "11-4",  "building": _b("ホッパー棟"), "location": "倉庫（換気ファン）",   "description": "", "day_of_week": 3, "week_filter": 4, "sort_order": 4},
    {"code": "11-5",  "building": _b("ホッパー棟"), "location": "屋上補機",            "description": "", "day_of_week": 3, "week_filter": 4, "sort_order": 5},

    # ─────────────────────────────────────────
    # 木曜日 (day_of_week=4)
    # ─────────────────────────────────────────

    # 二次処理棟
    {"code": "12-1",  "building": _b("二次処理棟"), "location": "屋上補機",         "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 1},
    {"code": "12-2",  "building": _b("二次処理棟"), "location": "太陽光パネル",     "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 2},
    {"code": "12-3",  "building": _b("二次処理棟"), "location": "電気室",           "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 3},
    {"code": "12-4",  "building": _b("二次処理棟"), "location": "換気ファン室",     "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 4},
    {"code": "12-5",  "building": _b("二次処理棟"), "location": "制御室",           "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 5},
    {"code": "12-6",  "building": _b("二次処理棟"), "location": "電気室",           "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 6},
    {"code": "12-7",  "building": _b("二次処理棟"), "location": "送風機室",         "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 7},
    {"code": "12-8",  "building": _b("二次処理棟"), "location": "コンプレッサー室",  "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 8},
    {"code": "12-9",  "building": _b("二次処理棟"), "location": "空調機械室",        "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 9},
    {"code": "12-10", "building": _b("二次処理棟"), "location": "ブロワ配管",        "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 10},
    {"code": "12-11", "building": _b("二次処理棟"), "location": "冷却水ポンプ",      "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 11},
    {"code": "12-12", "building": _b("二次処理棟"), "location": "給水ユニット",      "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 12},
    {"code": "12-13", "building": _b("二次処理棟"), "location": "フィルター室",      "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 13},
    {"code": "12-14", "building": _b("二次処理棟"), "location": "その他",           "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 14},

    # 第5系列水処理施設
    {"code": "13-1",  "building": _b("第5系列水処理施設"), "location": "電気室",            "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 1},
    {"code": "13-2",  "building": _b("第5系列水処理施設"), "location": "制御室",            "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 2},
    {"code": "13-3",  "building": _b("第5系列水処理施設"), "location": "ろ過機配管室",      "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 3},
    {"code": "13-4",  "building": _b("第5系列水処理施設"), "location": "換気機械室",        "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 4},
    {"code": "13-5",  "building": _b("第5系列水処理施設"), "location": "凝集剤ポンプ室",    "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 5},
    {"code": "13-6",  "building": _b("第5系列水処理施設"), "location": "循環ポンプ室",      "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 6},
    {"code": "13-7",  "building": _b("第5系列水処理施設"), "location": "返送汚泥ポンプ室",  "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 7},
    {"code": "13-8",  "building": _b("第5系列水処理施設"), "location": "反応タンク",        "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 8},
    {"code": "13-9",  "building": _b("第5系列水処理施設"), "location": "最終沈殿池",        "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 9},
    {"code": "13-10",  "building": _b("第5系列水処理施設"), "location": "汚泥かき寄せ機",    "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 10},
    {"code": "13-11",  "building": _b("第5系列水処理施設"), "location": "砂ろ過分配配水路",  "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 11},
    {"code": "13-12",  "building": _b("第5系列水処理施設"), "location": "PAC注入管流量確認", "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 12},
    {"code": "13-13",  "building": _b("第5系列水処理施設"),	"location":"その他",             "description":"","day_of_week" :4,"week_filter" :None,"sort_order" :13},

    # 1〜4系水処理施設
    {"code": "14-1",  "building": _b("1～4系水処理施設"), "location": "初沈汚泥引抜弁",     "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 1},
    {"code": "14-2",  "building": _b("1～4系水処理施設"), "location": "初沈汚泥ポンプ",     "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 2},
    {"code": "14-3",  "building": _b("1～4系水処理施設"), "location": "返送汚泥ポンプ",     "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 3},
    {"code": "14-4",  "building": _b("1～4系水処理施設"), "location": "余剰汚泥ポンプ",     "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 4},
    {"code": "14-5",  "building": _b("1～4系水処理施設"), "location": "循環ポンプ",         "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 5},
    {"code": "14-6",  "building": _b("1～4系水処理施設"), "location": "管廊（PAC設備含む）", "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 6},
    {"code": "14-7",  "building": _b("1～4系水処理施設"), "location": "最初沈殿池",          "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 7},
    {"code": "14-8",  "building": _b("1～4系水処理施設"), "location": "初沈汚泥かき寄せ機",  "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 8},
    {"code": "14-9",  "building": _b("1～4系水処理施設"), "location": "反応タンク",         "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 9},
    {"code": "14-10",  "building": _b("1～4系水処理施設"), "location": "最終沈殿池",        "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 10},
    {"code": "14-11",  "building": _b("1～4系水処理施設"), "location": "終沈汚泥かき寄せ機", "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 11},
    {"code": "14-12",  "building": _b("1～4系水処理施設"), "location": "集中給油装置",      "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 12},
    {"code": "14-13",  "building": _b("1～4系水処理施設"),	"location":"脱臭装置",   	    "description":"","day_of_week" :4,"week_filter" :None,"sort_order" :13},
    {"code": "14-14", 	"building":"1～4系水処理施設","location":"りん酸計",            "description":"","day_of_week" :4,"week_filter" :None,"sort_order" :14},
    {"code": "14-15",  "building": _b("1～4系水処理施設"), "location": "PAC注入量流量確認",  "description": "", "day_of_week": 4, "week_filter": None, "sort_order": 15},

    # ─────────────────────────────────────────
    # 金曜日 (day_of_week=5)
    # ─────────────────────────────────────────

    # 7・8系水処理棟
    {"code": "15-1",  "building": _b("7・8系水処理棟"), "location": "制御室",           "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 1},
    {"code": "15-2",  "building": _b("7・8系水処理棟"), "location": "低圧電気室",        "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 2},
    {"code": "15-3",  "building": _b("7・8系水処理棟"), "location": "高圧電気室",        "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 3},
    {"code": "15-4",  "building": _b("7・8系水処理棟"), "location": "脱臭機室",          "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 4},
    {"code": "15-5",  "building": _b("7・8系水処理棟"), "location": "最初沈殿池",        "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 5},
    {"code": "15-6",  "building": _b("7・8系水処理棟"), "location": "反応タンク",        "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 6},
    {"code": "15-7",  "building": _b("7・8系水処理棟"), "location": "最終沈殿池",          "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 7},
    {"code": "15-8",  "building": _b("7・8系水処理棟"), "location": "7系りん酸濃度計",      "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 8},
    {"code": "15-9",  "building": _b("7・8系水処理棟"), "location": "初沈スカム移送ポンプ",  "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 9},
    {"code": "15-10",  "building": _b("7・8系水処理棟"), "location": "初沈汚泥ポンプ",       "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 10},
    {"code": "15-11",  "building": _b("7・8系水処理棟"), "location": "初沈池排水ポンプ",     "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 11},
    {"code": "15-12",  "building": _b("7・8系水処理棟"), "location": "反応タンク空気圧縮機", "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 12},
    {"code": "15-13",  "building": _b("7・8系水処理棟"), "location": "PAC設備",            "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 13},
    {"code": "15-14",  "building": _b("7・8系水処理棟"), "location": "循環ポンプ",         "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 14},
    {"code": "15-15",  "building": _b("7・8系水処理棟"), "location": "終沈空気圧縮機",      "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 15},
    {"code": "15-16",  "building": _b("7・8系水処理棟"), "location": "終沈スカム移送ポンプ", "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 16},
    {"code": "15-17",  "building": _b("7・8系水処理棟"), "location": "消泡水ポンプ",       "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 17},
    {"code": "15-18",  "building": _b("7・8系水処理棟"), "location": "汚泥調整弁",         "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 18},
    {"code": "15-19",  "building": _b("7・8系水処理棟"), "location": "床排水ポンプ",       "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 19},
    {"code": "15-20",  "building": _b("7・8系水処理棟"), "location": "初沈床排水ポンプ",   "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 20},
    {"code": "15-21",  "building": _b("7・8系水処理棟"), "location": "返水ポンプ",         "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 21},
    {"code": "15-22",  "building":"7・8系水処理棟","location":"返送汚泥ポンプ",        "description":"","day_of_week" :5,"week_filter" :None,"sort_order" :22},
    {"code": "15-23",  "building":"7・8系水処理棟","location":"余剰汚泥ポンプ",        "description":"","day_of_week" :5,"week_filter" :None,"sort_order" :23},
    {"code": "15-24",  "building":"7・8系水処理棟","location":"反応タンク・終沈池排水ポンプ","description":"","day_of_week" :5,"week_filter" :None,"sort_order" :24},
    {"code": "15-25",  "building":"7・8系水処理棟","location":"送風機連絡管廊床排水ポンプ","description":"","day_of_week" :5,"week_filter" :None,"sort_order" :25},
    {"code": "15-26",  "building": _b("7・8系水処理棟"), "location":"終沈床排水ポンプ",    "description":"","day_of_week" :5,"week_filter" :None,"sort_order" :26},
    {"code": "15-27",  "building": _b("7・8系水処理棟"), "location":"その他",            "description":"","day_of_week" :5,"week_filter" :None,"sort_order" :27},

    # 7・8系送風機棟
    {"code": "16-1",  "building": _b("7・8系送風機棟"), "location": "冷却塔",          "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 1},
    {"code": "16-2",  "building": _b("7・8系送風機棟"), "location": "ブロワ",          "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 2},
    {"code": "16-3",  "building": _b("7・8系送風機棟"), "location": "電気室",          "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 3},
    {"code": "16-4",  "building": _b("7・8系送風機棟"), "location": "制御室",          "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 4},
    {"code": "16-5",  "building": _b("7・8系送風機棟"), "location": "換気機械室（1）", "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 5},
    {"code": "16-6",  "building": _b("7・8系送風機棟"), "location": "換気機械室（2）",  "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 6},
    {"code": "16-7",  "building": _b("7・8系送風機棟"), "location": "消火栓ポンプ室",   "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 7},
    {"code": "16-8",  "building": _b("7・8系送風機棟"), "location": "冷却水ポンプ",     "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 8},
    {"code": "16-9",  "building": _b("7・8系送風機棟"), "location": "床排水ポンプ",     "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 9},
    {"code": "16-10", "building": _b("7・8系送風機棟"), "location": "エアフィルター",   "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 10},

    # 7・8系管廊・流量計室
    {"code": "17-1",  "building": _b("7・8系管廊・流量計室"), "location": "流量計室",  "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 1},
    {"code": "17-2",  "building": _b("7・8系管廊・流量計室"), "location": "7系管廊床排水ポンプ", "description": "", "day_of_week": 5, "week_filter": None, "sort_order": 2},
]
