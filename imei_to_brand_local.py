#!/usr/bin/env python3
"""
imei_to_brand_kaggle_full.py

- Entrée : IMEI (15 chiffres)
- Sortie : informations complètes à partir du CSV Kaggle
"""

import csv
import re
import sys
import json

# --- Validation IMEI (Luhn) ---
def luhn_check(imei: str) -> bool:
    if not re.fullmatch(r"\d{14,16}", imei.strip()):
        return False
    digits = [int(d) for d in imei]
    total = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0

# --- Charger CSV Kaggle complet ---
def load_csv_kaggle(csv_path: str):
    mapping = {}
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tac = row.get("TAC", "").strip()
                if tac:
                    mapping[tac] = {
                        "brand": row.get("manufacturer", "").strip(),
                        "model": row.get("model", "").strip(),
                        "aka": row.get("aka", "").strip(),
                        "os": row.get("os", "").strip(),
                        "year": row.get("year", "").strip(),
                        "lte": row.get("lte", "").strip()
                    }
    except FileNotFoundError:
        print(f"[!] CSV introuvable : {csv_path}")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Erreur lecture CSV : {e}")
        sys.exit(1)
    return mapping

# --- Chercher par TAC ---
def find_info_by_tac(tac: str, mapping: dict):
    for length in range(8, 0, -1):
        key = tac[:length]
        if key in mapping:
            return mapping[key]
    return None

# --- Fonction principale ---
def imei_to_info(imei: str, csv_path: str):
    imei_clean = imei.strip()
    if not luhn_check(imei_clean):
        return {"ok": False, "error": "IMEI invalide (échec Luhn / format)."}
    
    tac = imei_clean[:8]
    mapping = load_csv_kaggle(csv_path)
    result = {"ok": True, "imei": imei_clean, "tac": tac}
    
    info = find_info_by_tac(tac, mapping)
    if info:
        result.update(info)
        result["source"] = "kaggle_csv"
    else:
        result.update({
            "brand": None,
            "model": None,
            "aka": None,
            "os": None,
            "year": None,
            "lte": None,
            "source": "unknown",
            "message": "TAC non trouvé dans la CSV Kaggle."
        })
    
    return result

# --- CLI ---
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python imei_to_brand_kaggle_full.py <IMEI> <path_to_csv>")
        sys.exit(1)

    imei_input = sys.argv[1]
    csv_file = sys.argv[2]

    info = imei_to_info(imei_input, csv_file)
    print(json.dumps(info, indent=2, ensure_ascii=False))
