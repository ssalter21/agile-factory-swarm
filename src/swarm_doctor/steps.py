"""The six gate steps, in the constitution's fixed order."""

ORDER: tuple[str, ...] = (
    "tests",
    "coverage",
    "duplication",
    "mutation",
    "crap",
    "acceptance",
)

# Constitution section 2: steps 1 and 2 apply to every project whatever else it declares.
FLOOR: tuple[str, ...] = ORDER[:2]
