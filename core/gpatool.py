"""حاسبة GPA — حساب حتمي 100% بدون LLM (دقة مضمونة) — ثنائي اللغة (عربي/إنجليزي)."""
from __future__ import annotations

SCALES: dict[str, dict[str, float]] = {
    "egypt5": {"ممتاز": 5.0, "جيد جدا": 4.0, "جيد جداً": 4.0, "جيد": 3.0, "مقبول": 2.0, "ضعيف": 1.0, "راسب": 0.0},
    "standard4": {"A": 4.0, "A-": 3.7, "A+": 4.0, "B+": 3.3, "B": 3.0, "B-": 2.7,
                  "C+": 2.3, "C": 2.0, "C-": 1.7, "D+": 1.3, "D": 1.0, "F": 0.0},
}

_SCALE_ALIASES = {"egypt5": "سلّم 5 نقاط (ممتاز..راسب)", "standard4": "سلّم 4 نقاط (A..F)"}
_SCALE_ALIASES_EN = {"egypt5": "5-point scale (Excellent..Fail)", "standard4": "4-point scale (A..F)"}
_MAX_POINTS = {"egypt5": 5.0, "standard4": 4.0}

_T = {
    "ar": {
        "title": "نتيجة حساب المعدل", "gpa": "معدل الترم", "of": "من", "hours_total": "إجمالي ساعات الترم",
        "cum": "المعدل التراكمي بعد الترم", "on": "على", "hours_w": "ساعة", "notes": "ملاحظات",
        "th": ["المادة", "الساعات", "التقدير", "النقاط"],
        "err_hours": "الساعات يجب أن تكون أكبر من صفر.",
        "err_grade": "تقدير غير معروف «{g}» — استخدم التقديرات المتاحة.",
        "err_prev": "المعدل السابق «{p}» غير منطقي لسلّم {m:g} نقاط — تم تجاهل حساب التراكمي.",
        "course_n": "مادة {i}",
        "err_empty": "لا توجد مواد صالحة للحساب — أدخل الساعات والتقديرات.",
    },
    "en": {
        "title": "GPA Result", "gpa": "Term GPA", "of": "out of", "hours_total": "Total term hours",
        "cum": "Cumulative GPA after this term", "on": "over", "hours_w": "hours", "notes": "Notes",
        "th": ["Course", "Hours", "Grade", "Points"],
        "err_hours": "Hours must be greater than zero.",
        "err_grade": "Unknown grade “{g}” — use the available grades.",
        "err_prev": "Previous GPA “{p}” is not valid for a {m:g}-point scale — cumulative ignored.",
        "course_n": "Course {i}",
        "err_empty": "No valid courses — enter hours and grades.",
    },
}


def _grade_points(grade: str, points, scale: str) -> float | None:
    if points is not None and str(points).strip() != "":
        try:
            p = float(points)
            if 0 <= p <= _MAX_POINTS[scale]:
                return p
        except Exception:
            pass
    if not grade:
        return None
    g = str(grade).strip()
    table = SCALES[scale]
    if g in table:
        return table[g]
    gu = g.upper()
    if gu in table:
        return table[gu]
    try:
        p = float(g)
        if 0 <= p <= _MAX_POINTS[scale]:
            return p
    except Exception:
        pass
    return None


def _label(pct: float, lang: str = "ar") -> str:
    if lang == "en":
        if pct >= 85:
            return "Excellent 🏆"
        if pct >= 75:
            return "Very Good 🌟"
        if pct >= 65:
            return "Good 👍"
        if pct >= 50:
            return "Pass ✅"
        return "Weak — urgent study plan needed 📌"
    if pct >= 85:
        return "ممتاز 🏆"
    if pct >= 75:
        return "جيد جداً 🌟"
    if pct >= 65:
        return "جيد 👍"
    if pct >= 50:
        return "مقبول ✅"
    return "ضعيف — يحتاج خطة مذاكرة عاجلة 📌"


def calc(rows: list[dict], scale: str = "egypt5",
         previous_gpa: float | None = None, previous_hours: float | None = None,
         lang: str = "ar") -> dict:
    """rows: [{"course": اسم اختياري, "hours": عدد الساعات, "grade": تقدير, "points": نقاط اختيارية}]"""
    t = _T.get(lang, _T["ar"])
    if scale not in SCALES:
        scale = "egypt5"
    table_rows: list[dict] = []
    total_points = 0.0
    total_hours = 0.0
    errors: list[str] = []
    for i, r in enumerate(rows, 1):
        name = str(r.get("course") or t["course_n"].format(i=i))
        try:
            hours = float(r.get("hours") or 0)
        except Exception:
            hours = 0.0
        pts = _grade_points(str(r.get("grade") or ""), r.get("points"), scale)
        if hours <= 0:
            errors.append(f"{name}: {t['err_hours']}")
            continue
        if pts is None:
            errors.append(f"{name}: " + t["err_grade"].format(g=r.get("grade")))
            continue
        total_points += pts * hours
        total_hours += hours
        table_rows.append({"course": name, "hours": hours, "grade": r.get("grade") or f"{pts:g}", "points": pts})
    if total_hours <= 0:
        raise ValueError(t["err_empty"])
    gpa = round(total_points / total_hours, 2)
    percentage = round(gpa / _MAX_POINTS[scale] * 100, 1)
    result: dict = {
        "scale": scale,
        "scale_name": _SCALE_ALIASES[scale] if lang == "ar" else _SCALE_ALIASES_EN[scale],
        "gpa": gpa, "term_hours": total_hours, "percentage": percentage,
        "label": _label(percentage, lang), "table": table_rows, "errors": errors,
    }
    if previous_gpa is not None and previous_hours is not None:
        try:
            pg, ph = float(previous_gpa), float(previous_hours)
            if not (0 <= pg <= _MAX_POINTS[scale]):
                errors.append(t["err_prev"].format(p=pg, m=_MAX_POINTS[scale]))
            elif ph <= 0:
                errors.append(t["err_hours"])
            else:
                cum = (pg * ph + total_points) / (ph + total_hours)
                cum_pct = round(cum / _MAX_POINTS[scale] * 100, 1)
                result["cumulative"] = {
                    "gpa": round(cum, 2),
                    "percentage": cum_pct,
                    "label": _label(cum_pct, lang),
                    "total_hours": ph + total_hours,
                }
        except (ValueError, TypeError):
            errors.append(t["err_prev"].format(p=previous_gpa, m=_MAX_POINTS[scale]))
    return result


def to_markdown(res: dict, lang: str = "ar") -> str:
    t = _T.get(lang, _T["ar"])
    th = t["th"]
    lines = [f"### 🧮 {t['title']} ({res['scale_name']})", "",
             f"| {th[0]} | {th[1]} | {th[2]} | {th[3]} |", "|---|---|---|---|"]
    for r in res["table"]:
        lines.append(f"| {r['course']} | {r['hours']:g} | {r['grade']} | {r['points']:g} |")
    lines += ["", f"**{t['gpa']}: {res['gpa']}** {t['of']} {_MAX_POINTS[res['scale']]:g} "
                  f"≈ **{res['percentage']}%** — {res['label']}",
              f"{t['hours_total']}: {res['term_hours']:g}"]
    if res.get("cumulative"):
        c = res["cumulative"]
        lines.append(f"**{t['cum']}: {c['gpa']}** ≈ {c['percentage']}% — {c['label']} "
                     f"({t['on']} {c['total_hours']:g} {t['hours_w']})")
    if res.get("errors"):
        sep = " ، " if lang == "ar" else ", "
        lines += ["", f"⚠️ {t['notes']}: " + sep.join(res["errors"])]
    return "\n".join(lines)
