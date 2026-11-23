MODES = {
    "Программирование / ПК": {
        "max_torso_angle": 20,
        "max_neck_angle": 35,
        "description": "Комфортный контроль спины и шеи при работе за компьютером"
    },
    "Чтение": {
        "max_torso_angle": 26,
        "max_neck_angle": 45,
        "description": "Мягкий порог для шеи при чтении"
    },
    "Письмо": {
        "max_torso_angle": 34,
        "max_neck_angle": 50,
        "description": "Контроль только при сильном скручивании спины"
    }
}

BAD_POSTURE_DELAY = 5    # Через сколько секунд сутулости сработает напоминание
NOTIFY_COOLDOWN = 15     # Пауза (КД) между напоминаниями — 15 секунд
