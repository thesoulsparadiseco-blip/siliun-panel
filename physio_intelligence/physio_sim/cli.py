"""CLI del simulador.

    python -m physio_sim.cli                  # corre los 9 escenarios
    python -m physio_sim.cli hr_high_at_rest   # corre uno solo
"""
from __future__ import annotations

import sys
from datetime import datetime

from .scenarios import SCENARIOS
from .simulator import run_scenario

START = datetime(2026, 1, 1, 7, 0, 0)


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    names = argv or list(SCENARIOS.keys())

    unknown = [n for n in names if n not in SCENARIOS]
    if unknown:
        print(f"Escenario(s) desconocido(s): {', '.join(unknown)}")
        print(f"Disponibles: {', '.join(SCENARIOS.keys())}")
        return 1

    for name in names:
        phases = SCENARIOS[name]()
        result = run_scenario(phases, START)
        print(f"\n=== {name} ===")
        print(result.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
