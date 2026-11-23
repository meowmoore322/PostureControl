import os
import json
from datetime import date


class StatsManager:
    def __init__(self, filename="posture_stats.json"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.filepath = os.path.join(base_dir, filename)
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def _get_today_record(self):
        today = str(date.today())
        if today not in self.data:
            self.data[today] = {
                "good_seconds": 0,
                "bad_seconds": 0,
                "notifications": 0,
                "modes": {}
            }
        return self.data[today]

    def record_second(self, is_bad_posture, mode_name):
        rec = self._get_today_record()
        if is_bad_posture:
            rec["bad_seconds"] += 1
        else:
            rec["good_seconds"] += 1

        rec["modes"][mode_name] = rec["modes"].get(mode_name, 0) + 1

    def record_notification(self):
        rec = self._get_today_record()
        rec["notifications"] += 1
        self.save()

    def get_today_summary(self):
        rec = self._get_today_record()
        good = rec["good_seconds"]
        bad = rec["bad_seconds"]
        total = good + bad
        good_percent = round((good / total) * 100) if total > 0 else 0

        return {
            "total_sec": total,
            "good_sec": good,
            "bad_sec": bad,
            "good_percent": good_percent,
            "notifications": rec["notifications"],
            "modes": rec["modes"]
        }

    def reset_today(self):
        today = str(date.today())
        if today in self.data:
            del self.data[today]
            self.save()
