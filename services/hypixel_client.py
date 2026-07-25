"""
Thin wrapper around the Hypixel Public API (v2).

Used in this project as the "public test server" data source so the client
can see a real, live, fully-populated dashboard before the celebrity's own
private server exists. Endpoints used:

  GET /v2/counts        -> total online players + a breakdown per game/mode
  GET /v2/leaderboards   -> the network's real, live leaderboards per game
                             (each entry has a ranked list of player UUIDs)

Docs: https://api.hypixel.net/  (interactive) and
      https://github.com/HypixelDev/PublicAPI

Auth: every request needs an "API-Key" header. Get a development key for
free at https://developer.hypixel.net/dashboard/ (login with your Minecraft/
Hypixel forum account -> Create Development Key). Development keys are fine
for building and demoing; if this ever needs to run in front of the client
permanently, apply for a personal/production key from the same dashboard.
"""

"""
Mock wrapper for the Hypixel Public API.
هذا الملف تم تعديله لإرجاع بيانات وهمية (Mock Data) 
لتشغيل اللوحة والعرض التجريبي بدون الحاجة لمفتاح API أو حساب ماينكرافت.
"""

import random

# أرقام UUID حقيقية لحسابات ماينكرافت معروفة 
# لكي يعمل ملف mojang_client.py بدون أخطاء ويتمكن من جلب الأسماء والصور
FAMOUS_UUIDS = [
    "069a79f444e94726a5befca90e38aaf5", # Notch
    "853c80ef3c3749fdaa49938b674adae6", # jeb_
    "b876ec32e396476ba1158438d83c67d4", # Technoblade
    "ec70bcaf702f4bb8b48d276fa52a780c", # Dream
    "da06bc2d787040a6b98ea1223e710d02", # Grian
    "198f395c621441bfa98e3b0b5be8b5a0", # DanTDM
    "e4eb30740a654c6ea4d7ffb9f939e144", # Mumbo
    "0b58e2a188ce426fb63102c98d6c7081", # CaptainSparklez
    "12fb9fb6057a419eb20ab7cb90c58f00", # Philza
    "3890fb915e4f4fb0a4b75f822f3e8b0a"  # TommyInnit
]

def get_counts() -> dict:
    """إرجاع أعداد لاعبين وهمية للألعاب الخاصة بسيرفر VeinMC"""
    return {
        "success": True,
        "playerCount": random.randint(500, 650), 
        "games": {
            "SMP": {"players": random.randint(200, 300), "modes": {}},
            "DUELS": {"players": random.randint(100, 150), "modes": {}},
            "MINIGAMES": {"players": random.randint(50, 100), "modes": {}},
            "GENBLOCK": {"players": random.randint(50, 100), "modes": {}},
        }
    }

def get_leaderboards() -> dict:
    """إرجاع لوحة صدارة وهمية لألعاب VeinMC (توب 10)"""
    
    # 1. نغير العدد الافتراضي هنا إلى 10
    def get_random_leaders(count=10):
        # قائمة FAMOUS_UUIDS تحتوي أصلاً على 10 لاعبين، فسيقوم بعرضهم جميعاً بترتيب عشوائي
        return random.sample(FAMOUS_UUIDS, count)

    return {
        "success": True,
        "leaderboards": {
            "SMP": [
                # 2. نغير قيمة "count" في كل سطر إلى 10
                {"path": "playtime", "prefix": "SMP", "title": "Playtime", "count": 10, "leaders": get_random_leaders()},
                {"path": "wealth", "prefix": "SMP", "title": "Top Money", "count": 10, "leaders": get_random_leaders()}
            ],
            "DUELS": [
                {"path": "kills", "prefix": "Duels", "title": "Kills", "count": 10, "leaders": get_random_leaders()},
                {"path": "wins", "prefix": "Duels", "title": "Wins", "count": 10, "leaders": get_random_leaders()}
            ],
            "MINIGAMES": [
                {"path": "wins", "prefix": "Minigames", "title": "Wins", "count": 10, "leaders": get_random_leaders()},
            ],
            "GENBLOCK": [
                {"path": "level", "prefix": "Genblock", "title": "Island Level", "count": 10, "leaders": get_random_leaders()},
            ]
        }
    }