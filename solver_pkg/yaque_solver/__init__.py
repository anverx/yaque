"""Yaque solver — Cython-compiled puzzle solver and kingdom builder."""
from .solver import (
    find_all_solutions,
    count_solutions,
    calculate_difficulty,
    create_kingdoms,
)

__all__ = [
    'find_all_solutions',
    'count_solutions',
    'calculate_difficulty',
    'create_kingdoms',
]
