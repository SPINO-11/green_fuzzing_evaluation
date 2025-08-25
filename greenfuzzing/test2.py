import json
import math
import sys
from typing import Tuple, Iterable, Dict, Any

Number = (int, float)

def load_export(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def iter_functions(doc: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """
    Traversiert das llvm-cov-Export-JSON gezielt entlang:
      data[*] -> files[*] -> functions[*]
    und liefert die Funktionsobjekte.
    """
    data_nodes = doc.get("data", [])
    # Manche Tools packen kein 'data' drum herum – dann so tun, als wäre 'doc' direkt der payload
    if isinstance(data_nodes, dict) and "files" in data_nodes:
        data_nodes = [data_nodes]
    if not data_nodes and "files" in doc:
        data_nodes = [doc]

    for d in data_nodes:
        for f in d.get("files", []):
            for fn in f.get("functions", []):
                yield fn

def count_branch_edges(fn_obj: Dict[str, Any]) -> Tuple[int, int]:
    """
    Zählt Branch-Kanten (edges) innerhalb einer Funktion.
    Es werden NUR Einträge berücksichtigt, die ein numerisches 'count' Feld tragen.
    Das ist das stabile Format von llvm-cov export; so vermeidet man Doppelzählungen.
    """
    total = 0
    covered = 0
    for b in fn_obj.get("branches", []):
        # Jede Kante kommt als Objekt mit 'count'
        if isinstance(b, dict) and isinstance(b.get("count", None), Number):
            total += 1
            # 'count' kann theoretisch float sein (z. B. gewichtete Profile) -> > 0 heißt covered
            if b["count"] > 0:
                covered += 1
        # Andere Formen werden bewusst ignoriert, um keine falschen Heuristiken einzubauen.
    return total, covered

def compute_branches_from_functions(doc: Dict[str, Any]) -> Tuple[int, int, int]:
    total = covered = 0
    for fn in iter_functions(doc):
        t, c = count_branch_edges(fn)
        total += t
        covered += c
    notcovered = total - covered
    return total, covered, notcovered

def read_totals_branches(doc: Dict[str, Any]) -> Tuple[int, int, int]:
    """
    Liest optional die offiziellen Totals/Summary aus, falls vorhanden.
    Rückgabe (count, covered, notcovered) oder (None, None, None), wenn nicht gefunden.
    """
    def pick(obj):
        b = obj.get("branches", {})
        if all(k in b for k in ("count", "covered")):
            cnt = b.get("count")
            cov = b.get("covered")
            notcov = b.get("notcovered", None)
            if isinstance(cnt, Number) and isinstance(cov, Number):
                if notcov is None and isinstance(cnt, Number) and isinstance(cov, Number):
                    notcov = cnt - cov
                return int(cnt), int(cov), int(notcov)
        return (None, None, None)

    # LLVM hat je nach Version 'totals' oder 'summary' an verschiedenen Stellen
    for key in ("totals", "summary"):
        if key in doc:
            r = pick(doc[key])
            if r[0] is not None:
                return r
    # oft liegt totals/summary unter data[*]
    for d in doc.get("data", []):
        for key in ("totals", "summary"):
            if key in d:
                r = pick(d[key])
                if r[0] is not None:
                    return r
    return (None, None, None)

def main(path: str) -> None:
    doc = load_export(path)
    total, covered, notcovered = compute_branches_from_functions(doc)

    print("Rekonstruiert aus functions[*].branches:")
    print(f"  branches.count       = {total}")
    print(f"  branches.covered     = {covered}")
    print(f"  branches.notcovered  = {notcovered}")
    print(f"  branches.percent     = {(covered / total * 100.0) if total else 0:.2f}%")

    t_cnt, t_cov, t_not = read_totals_branches(doc)
    if t_cnt is not None:
        # Vergleich / Plausibilitätscheck
        ok = (t_cnt == total) and (t_cov == covered) and (t_not == notcovered)
        print("\nVergleich mit totals/summary aus der Datei:")
        print(f"  totals.branches.count      = {t_cnt}")
        print(f"  totals.branches.covered    = {t_cov}")
        print(f"  totals.branches.notcovered = {t_not}")
        print(f"\nAbgleich: {'OK ✅' if ok else 'ABWEICHUNG ⚠️'}")
        if not ok:
            print("\nHinweis:")
            print("- Prüfe, ob die Export-Optionen (z. B. -skip-expansions, -region-coverage-gt=...)")
            print("  bei dir die gleichen Filter für Summary und Detaildaten erzeugen.")
            print("- Dieses Skript berücksichtigt bewusst NUR Branch-Objekte mit numerischem 'count'.")
            print("  Falls dein Export ein anderes Branch-Format hat, bitte zeigen – dann passe ich den Parser an.")
    else:
        print("\nKein totals/summary-Branchenblock im JSON gefunden (ok, aber kein Abgleich möglich).")

if __name__ == "__main__":
    main("greenfuzzing/coverage-archive-0000.json")