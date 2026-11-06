"""Workshop checker: run from the repository root with Python 3.12 or newer.

Students edit order.csv only. Prices are in cents to keep budget checks exact.
No external Python packages are required.
"""
from __future__ import annotations

import csv
import os
import re
import sys
from pathlib import Path

# item ID: display name, category, unit price in cents
MENU = {
    "water": ("Water", "drink", 50),
    "tea": ("Tea", "drink", 80),
    "banana": ("Banana", "snack", 70),
    "curry_puff": ("Curry puff", "snack", 120),
    "sandwich": ("Sandwich", "snack", 200),
    "cookies": ("Cookies", "snack", 100),
}
BUDGET = 500
MINIMUM_ITEMS = 3


def money(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    return f"{sign}${abs(cents) // 100}.{abs(cents) % 100:02d}"


def read_order(path: Path) -> tuple[dict[str, int], list[str]]:
    issues: list[str] = []
    quantities: dict[str, int] = {}
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle, strict=True))
    except (OSError, UnicodeError, csv.Error) as error:
        return {}, [f"Cannot read order.csv: {error}. Keep it at the repository root."]
    if not rows or [cell.strip() for cell in rows[0]] != ["item", "quantity"]:
        return {}, ["The first line must be exactly item,quantity. Use the supplied CSV starter."]
    seen: set[str] = set()
    for number, row in enumerate(rows[1:], start=2):
        if not row or all(not cell.strip() for cell in row):
            continue
        if len(row) != 2:
            issues.append(f"Line {number}: keep two columns, item and quantity.")
            continue
        item, raw_quantity = (cell.strip() for cell in row)
        if item not in MENU:
            issues.append(f"Line {number}: unknown item ID {item!r}. Keep the supplied item IDs.")
            continue
        if item in seen:
            issues.append(f"Line {number}: {item} appears twice. Keep one row for each item.")
            continue
        seen.add(item)
        if not re.fullmatch(r"[0-9]+", raw_quantity):
            issues.append(f"Line {number}: {item} needs a whole-number quantity such as 0, 1 or 2.")
            continue
        try:
            quantities[item] = int(raw_quantity)
        except ValueError:
            issues.append(f"Line {number}: quantity is too long. Enter a small whole number.")
    for item in MENU:
        if item not in seen:
            issues.append(f"Missing {item} row. Keep all six item rows; use 0 for items you do not want.")
    return quantities, issues


def evaluate(quantities: dict[str, int]) -> tuple[dict[str, int], list[str]]:
    total = sum(MENU[item][2] * quantity for item, quantity in quantities.items())
    count = sum(quantities.values())
    drinks = sum(quantity for item, quantity in quantities.items() if MENU[item][1] == "drink")
    issues = []
    if count < MINIMUM_ITEMS:
        issues.append(f"You chose {count} item(s). Choose at least 3 items in total.")
    if drinks < 1:
        issues.append("Your order has no drink. Add at least one water or tea.")
    if total > BUDGET:
        issues.append(f"Your order costs {money(total)}, which is {money(total - BUDGET)} over the $5.00 budget.")
    return {"total": total, "items": count, "drinks": drinks, "remaining": BUDGET - total}, issues


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) > 1:
        print("Usage: python scripts/check_order.py [path/to/order.csv]")
        return 2
    path = Path(args[0]) if args else Path("order.csv")
    quantities, issues = read_order(path)
    summary = ["# Snack Corner order", ""]
    metrics = None
    if not issues:
        metrics, issues = evaluate(quantities)
        summary += ["| Item | Quantity | Unit price | Cost |", "|---|---:|---:|---:|"]
        for item, quantity in quantities.items():
            if quantity:
                label, _, price = MENU[item]
                summary.append(f"| {label} | {quantity} | {money(price)} | {money(price * quantity)} |")
                print(f"{label}: {quantity} x {money(price)} = {money(price * quantity)}")
        summary += ["", f"**Total: {money(metrics['total'])}**", "",
                    f"Items: {metrics['items']}  ", f"Drinks: {metrics['drinks']}  ",
                    f"Budget remaining: {money(metrics['remaining'])}", ""]
        print(f"Total: {money(metrics['total'])}")
        print(f"Items: {metrics['items']} | Drinks: {metrics['drinks']}")
        print(f"Budget remaining: {money(metrics['remaining'])}")
    if issues:
        print("\nResult: NEEDS CHANGES")
        summary += ["## NEEDS CHANGES", ""]
        for issue in issues:
            print("- " + issue)
            summary.append("- " + issue)
        summary += ["", "Edit the quantity values in order.csv, save, commit and push a new attempt."]
    else:
        print("\nResult: PASS - all three rules are met.")
        print("Try getting closer to $5.00 if you still have budget left.")
        summary += ["## PASS", "", "All three rules are met. Your goal is to get as close to $5.00 as possible."]
    summary += ["", "Rules: at least 3 items in total, at least 1 drink, total at most $5.00.",
                "Prices are fixed by the supplied checker. Edit order.csv only."]
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write("\n".join(summary) + "\n")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
