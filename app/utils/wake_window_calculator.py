def get_wake_window_minutes(age_in_days: int) -> int:
    if age_in_days < 30:          # 0–4 semanas
        return 50                 # 45–60 ➜ usei 50 como meio-termo
    elif age_in_days < 90:        # 1–3 meses
        return 60
    elif age_in_days < 150:       # 3–5 meses
        return 75
    elif age_in_days < 210:       # 5–7 meses
        return 90
    elif age_in_days < 270:       # 7–9 meses
        return 105
    elif age_in_days < 360:       # 9–12 meses
        return 120
    else:                         # >1 ano (ajuste conforme necessidade)
        return 150
