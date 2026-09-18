from .core import Level


LEVELS = (
    Level(
        name="第一关 · 初窥门径",
        grid=(
            "R.U",
            "...",
            "D.L",
        ),
        max_mistakes=3,
    ),
    Level(
        name="第二关 · 渐入佳境",
        grid=(
            "R..U",
            ".U..",
            "..L.",
            "U..L",
        ),
        max_mistakes=3,
    ),
    Level(
        name="第三关 · 运筹帷幄",
        grid=(
            "R...U",
            ".D...",
            "U...L",
            "...D.",
            "U...L",
        ),
        max_mistakes=4,
    ),
)
