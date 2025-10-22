import re

def clean_rut(rut: str) -> str:
    if not rut:
        return ""
    rut = rut.strip().lower().replace(".", "").replace(" ", "")
    if "-" not in rut and len(rut) > 1:
        rut = f"{rut[:-1]}-{rut[-1]}"
    return rut

def is_valid_rut(rut: str) -> bool:
    rut = clean_rut(rut)
    m = re.match(r"^(\d+)-([\dk])$", rut)
    if not m:
        return False
    num, dv = m.groups()
    s, mul = 0, 2
    for c in reversed(num):
        s += int(c) * mul
        mul = 2 if mul == 7 else mul + 1
    res = 11 - (s % 11)
    dv_calc = "0" if res == 11 else "k" if res == 10 else str(res)
    return dv == dv_calc
