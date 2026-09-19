from .core import Level


LEVELS = (
    Level(
        name="第一关 · 初窥门径",
        grid=(
            ".U...",
            "R.D..",
            "..L..",
            "..D..",
            ".U.DL",
        ),
        max_mistakes=3,
        three_star_seconds=25,
        two_star_seconds=45,
    ),
    Level(
        name="第二关 · 渐入佳境",
        grid=(
            "....R.",
            ".RD...",
            "..L..L",
            "U..L..",
            "...U.L",
            "U...LU",
        ),
        max_mistakes=4,
        three_star_seconds=40,
        two_star_seconds=70,
    ),
    Level(
        name="第三关 · 运筹帷幄",
        grid=(
            ".......",
            ".UD.L..",
            "R.R..RD",
            "..D...L",
            "UU.L..D",
            "....U..",
            "....RU.",
        ),
        max_mistakes=5,
        three_star_seconds=60,
        two_star_seconds=100,
    ),
    Level(
        name="第四关 · 环环相扣",
        grid=(
            ".......L",
            "D.L.DL..",
            ".R.D....",
            "L..L..L.",
            "...D..U.",
            "...RRD..",
            ".R....U.",
            ".....RRR",
        ),
        max_mistakes=6,
        three_star_seconds=85,
        two_star_seconds=140,
    ),
)
