# 软件工程第二次个人作业——“一箭又一箭”小游戏

| 项目 | 内容 |
| --- | --- |
| 这个作业属于哪个课程 | [2026-01 软件工程与软件工程实践](https://edu.cnblogs.com/campus/fzu/2026-01SoftwareEngineeringandSoftwareEngineeringPractice) |
| 这个作业要求在哪里 | [第二次个人作业](https://edu.cnblogs.com/campus/fzu/2026-01SoftwareEngineeringandSoftwareEngineeringPractice/homework/16718) |
| 这个作业的目标 | 使用 Python 和 AIGC 完成“一箭又一箭”小游戏 |
| 姓名、学号 | 102401614 林志涛 |
| GitHub 仓库 | [arrow_game](https://github.com/zhitaolin30-blip/arrow_game) |

> 提交前请删除所有“【待填写】”提示，并将截图路径替换成上传到博客或 GitHub 后的公开图片地址。

## 一、项目展示

### 1. 开始界面

![开始界面](screenshots/01_start.png)

### 2. 游戏界面

![游戏界面](screenshots/02_game.png)

### 3. 碰撞反馈

![碰撞反馈](screenshots/03_collision.png)

### 4. 通关与失败界面

![通关界面](screenshots/04_complete.png)

![失败界面](screenshots/05_failed.png)

### 5. 高难度扩展关

![扩展关](screenshots/06_extension.png)

### 6. 提示与星级评分

![黄色高亮提示](screenshots/07_hint.png)

## 二、项目介绍

“一箭又一箭”是一款点击式箭头解谜游戏。棋盘中放置了朝上、下、左、右四个方向的箭头。玩家需要观察箭头的朝向和相互阻挡关系，选择正确的消除顺序，最终清空棋盘。

- 前方没有其他箭头时，被点击的箭头会沿自身方向飞出棋盘。
- 所有正常箭头统一显示为绿色；前方存在其他箭头时，发生碰撞的箭头会变红、前冲抖动并回弹，同时扣除一次失误机会。
- 正确消除使用箭头飞出的短促“嗖”声，错误碰撞使用低沉警示音，玩家无需看文字也能区分操作结果。
- 清空当前关卡即可通关；失误机会耗尽则挑战失败。
- 四个棋盘按难度依次为 5×5、6×6、7×7、8×8，分别包含 8、12、16、20 个箭头。
- 每关有 2 次提示机会，使用后会将一个当前可正确点击的格子显示为黄色。
- 通关后根据完成时间与失误次数获得 1–3 星评价。
- 支持重新开始、返回主页以及 `R`、`Esc` 快捷键。

游戏使用 960×720 窗口和米白色暖色主题，所有图形由 Pygame 直接绘制，两种音效由代码合成，不依赖外部图片或音频素材；音频设备不可用时会静默降级。

## 三、实现思路

项目将代码分为规则层与界面层。`core.py` 只处理棋盘、路径、失误和关卡状态，不依赖 Pygame；`ui.py` 负责绘制、鼠标事件、动画与音效。这样可以直接对核心规则运行自动化测试，而不需要真正打开窗口。

### 1. 方向与关卡的数据表示

关卡使用字符串元组保存，每个字符对应一个格子：`U`、`D`、`L`、`R` 分别代表上、下、左、右，`.` 代表空格。方向枚举同时提供行列增量，四个方向可以共用同一套路径算法。

```python
class Direction(str, Enum):
    UP = "U"
    DOWN = "D"
    LEFT = "L"
    RIGHT = "R"

    @property
    def delta(self) -> tuple[int, int]:
        return {
            Direction.UP: (-1, 0),
            Direction.DOWN: (1, 0),
            Direction.LEFT: (0, -1),
            Direction.RIGHT: (0, 1),
        }[self]


@dataclass(frozen=True)
class Level:
    name: str
    grid: tuple[str, ...]
    max_mistakes: int
    three_star_seconds: float
    two_star_seconds: float
```

例如第一关使用 5×5 布局，共有 8 个箭头：

```python
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
)
```

程序加载关卡时会把不可变字符串复制成二维列表，游戏过程只修改副本，因此重新开始时可以从原始模板完整恢复棋盘。

### 2. 路径检测算法

路径检测是游戏的核心。程序先取得箭头方向，从相邻的下一格开始，沿 `(dr, dc)` 一直扫描到边界。只要途中发现非空格子，就说明路径被挡住；循环自然结束则表示箭头可以飞出。

```python
def has_clear_path(self, row: int, col: int) -> bool:
    direction = self.direction_at(row, col)
    if direction is None:
        return False

    dr, dc = direction.delta
    row += dr
    col += dc

    while self._inside(row, col):
        if self.board[row][col] != ".":
            return False
        row += dr
        col += dc
    return True
```

这里有三个重要细节：

1. 检查的是直到边界的整条路径，而不只是相邻格；隔着多个空格的箭头同样会形成阻挡。
2. 每次访问棋盘前先调用 `_inside` 判断坐标，因此不会出现数组越界。
3. 位于边缘且朝向棋盘外的箭头，第一步就会离开棋盘，循环体不会执行，会直接返回 `True`。

单次检测最多扫描一行或一列，时间复杂度为 `O(max(rows, cols))`，空间复杂度为 `O(1)`。

### 3. 点击处理、失误和状态切换

规则层将一次点击归纳为三种结果：成功消除 `REMOVED`、发生碰撞 `BLOCKED`、无效点击 `IGNORED`。界面层只需要根据返回结果选择动画和音效，不需要重复实现游戏规则。

```python
def attempt_move(self, row: int, col: int) -> MoveResult:
    if self.phase is not GamePhase.PLAYING:
        return MoveResult.IGNORED

    direction = self.direction_at(row, col)
    if direction is None:
        return MoveResult.IGNORED

    if not self.has_clear_path(row, col):
        self.mistakes_remaining -= 1
        if self.mistakes_remaining <= 0:
            self.mistakes_remaining = 0
            self._freeze_timer()
            self.phase = GamePhase.FAILED
        return MoveResult.BLOCKED

    self.board[row][col] = "."
    if self.remaining_arrows == 0:
        self._freeze_timer()
        self.phase = GamePhase.LEVEL_COMPLETE
    return MoveResult.REMOVED
```

成功时直接把对应格子改为 `.`，剩余箭头数通过扫描棋盘实时计算，避免单独维护计数器造成状态不同步。失败或通关时会冻结计时，使结果界面的时间不再继续增加。

游戏流程由状态枚举统一管理：

```python
class GamePhase(str, Enum):
    MENU = "menu"
    PLAYING = "playing"
    LEVEL_COMPLETE = "level_complete"
    FAILED = "failed"
    ALL_COMPLETE = "all_complete"
```

### 4. 动画与连续点击优化

界面层将每个视觉效果保存为独立的 `Animation` 对象，而不是用一个全局动画锁。成功消除后，规则层已经移除了箭头，飞出动画则使用保存的坐标和方向继续绘制，因此玩家可以立刻点击下一个箭头。

```python
def attempt_cell(self, row: int, col: int, *, now: float | None = None) -> MoveResult:
    if self.game.phase is not GamePhase.PLAYING:
        return MoveResult.IGNORED

    # 同一个正在碰撞的箭头不能重复扣除失误次数。
    if any(
        item.kind == "blocked" and item.row == row and item.col == col
        for item in self.animations
    ):
        return MoveResult.IGNORED

    direction = self.game.direction_at(row, col)
    if direction is None:
        return MoveResult.IGNORED

    result = self.game.attempt_move(row, col)
    started_at = time.monotonic() if now is None else now

    if result is MoveResult.REMOVED:
        self.sounds.play_correct()
        self.animations.append(
            Animation("flying", row, col, direction, started_at, 0.42)
        )
    elif result is MoveResult.BLOCKED:
        self.sounds.play_incorrect()
        self.animations.append(
            Animation("blocked", row, col, direction, started_at, 0.48)
        )
    return result
```

每一帧只过滤已经播放完的动画，其余动画可以同时存在：

```python
def update(self, now: float) -> None:
    self.animations = [
        item for item in self.animations
        if item.progress(now) < 1.0
    ]
```

飞出动画使用二次缓动 `progress²`，使箭头逐渐加速离开；碰撞动画使用正弦函数完成前冲与回弹，并叠加高频小幅抖动。正常箭头统一为绿色，碰撞动画中的箭头临时绘制为红色：

```python
if animation.kind == "flying":
    eased = progress * progress
    distance = max(WIDTH, HEIGHT) * eased
    x += dc * distance
    y += dr * distance
    color = DIRECTION_COLORS[animation.direction]
else:
    offset = math.sin(progress * math.pi) * 18
    jitter = math.sin(progress * math.pi * 8) * 3
    x += dc * offset + (jitter if dr else 0)
    y += dr * offset + (jitter if dc else 0)
    color = DANGER

self._draw_arrow((x, y), animation.direction, cell * 0.31, color)
```

### 5. DFS 关卡求解器与难度验证

手工设计的箭头布局可能出现互相阻挡的死局，因此项目实现了 DFS 求解器。每一步枚举当前能够飞出的箭头，模拟移除后递归搜索；如果棋盘清空就返回点击序列，如果某个局面无解则记录到 `failed` 集合，避免重复搜索。

```python
def solve_level(level: Level) -> list[tuple[int, int]] | None:
    start = tuple(level.grid)
    failed: set[tuple[str, ...]] = set()

    def search(board: tuple[str, ...]):
        if all(cell == "." for row in board for cell in row):
            return []
        if board in failed:
            return None

        for row, line in enumerate(board):
            for col, cell in enumerate(line):
                if cell == "." or not _clear_path_on_board(board, row, col):
                    continue

                next_board = [list(value) for value in board]
                next_board[row][col] = "."
                next_board = tuple("".join(value) for value in next_board)
                result = search(next_board)
                if result is not None:
                    return [(row, col), *result]

        failed.add(board)
        return None

    return search(start)
```

自动化测试不仅要求 `solve_level` 返回结果，还会用真实的 `GameState.attempt_move` 逐步回放整条序列。第四关采用 8×8 棋盘和 20 个箭头，开局只有三个合法选择，求解路径中还有多步只存在唯一选择，避免仅靠扩大棋盘制造“伪难度”。

### 6. 提示模块

提示不使用预先写死的坐标，而是根据当前棋盘重新调用路径检测。`available_moves` 遍历所有存活箭头，只保留路径畅通的坐标。`request_hint` 在关卡进行中且剩余次数大于零时，消耗一次机会并返回其中一格。如果没有可用坐标，则不会扣除次数。

```python
def available_moves(self) -> list[tuple[int, int]]:
    if self.phase is not GamePhase.PLAYING:
        return []
    return [
        (row, col)
        for row in range(self.rows)
        for col in range(self.cols)
        if self.direction_at(row, col) is not None
        and self.has_clear_path(row, col)
    ]

def request_hint(self) -> tuple[int, int] | None:
    if self.phase is not GamePhase.PLAYING or self.hints_remaining <= 0:
        return None
    moves = self.available_moves()
    if not moves:
        return None
    self.hints_remaining -= 1
    return moves[0]
```

界面层将返回的 `(row, col)` 保存为 `hinted_cell`，在绘制棋盘时先绘制黄色脉冲底色和粗边框，再绘制箭头，因此高亮不会遮住方向。玩家完成下一次有效点击后会清除高亮，重开或进入下一关时提示次数恢复为 2。

```python
if self.hinted_cell == (row, col):
    pulse = 0.72 + 0.18 * math.sin(now * 7.0)
    highlight = tuple(
        int(value * pulse + 255 * (1.0 - pulse))
        for value in HINT_YELLOW
    )
    pygame.draw.rect(screen, highlight, cell_rect.inflate(-5, -5))
    pygame.draw.rect(screen, HINT_YELLOW, cell_rect.inflate(-4, -4), width=4)
```

### 7. 三星评分模块

每个关卡分别设置“三星时限”和“二星时限”，棋盘越大，允许时间越长。评分同时考虑用时和失误：在三星时限内且零失误得 3 星；在二星时限内且失误不超过 1 次得 2 星；其他通关情况得 1 星。评分在最后一支箭头被消除时立即保存，结算界面不会改变结果。

```python
def calculate_stars(self) -> int:
    if (
        self.mistakes_made == 0
        and self.elapsed <= self.level.three_star_seconds
    ):
        return 3
    if (
        self.mistakes_made <= 1
        and self.elapsed <= self.level.two_star_seconds
    ):
        return 2
    return 1

# 清空棋盘时冻结计时和星级
if self.remaining_arrows == 0:
    self._freeze_timer()
    self.phase = GamePhase.LEVEL_COMPLETE
    self.stars_earned = self.calculate_stars()
```

### 8. 程序合成操作音效

项目没有引用外部音频文件，而是生成 44.1 kHz、16 位单声道 PCM 数据。正确操作使用平滑噪声与由 1500 Hz 降到 600 Hz 的扫频，模拟箭头飞出的“嗖”声；错误操作使用约 175 Hz 的低频振荡和颤音。

```python
if kind == "correct":
    noise_state = (1_103_515_245 * noise_state + 12_345) & 0x7FFFFFFF
    white_noise = noise_state / 0x3FFFFFFF - 1.0
    smoothed_noise = 0.82 * smoothed_noise + 0.18 * white_noise
    frequency = 1_500.0 - 900.0 * progress
    phase += 2.0 * math.pi * frequency / self.SAMPLE_RATE
    value = 0.82 * smoothed_noise + 0.18 * math.sin(phase)
else:
    frequency = 175.0 - 35.0 * progress
    phase += 2.0 * math.pi * frequency / self.SAMPLE_RATE
    tremolo = 0.72 + 0.28 * math.sin(2.0 * math.pi * 18.0 * t)
    value = (math.sin(phase) + 0.42 * math.sin(phase * 0.5)) * tremolo
```

生成的数据写入内存中的 WAV 流，再交给 `pygame.mixer.Sound` 播放。音频初始化或播放失败时会自动将音效系统设为静默状态，不会影响游戏规则和界面运行。

## 四、AIGC 使用过程

请参考仓库中的 `AIGC_RECORD.md`，根据真实开发和修改过程补充。建议至少展示需求分析、架构设计、功能实现、问题修复和测试五个有代表性的阶段。

【待填写：粘贴整理后的真实 AIGC 使用表，并加入必要的对话截图】

## 五、测试结果

测试环境：Windows 11、Python 3.13、Pygame 2.6.1、pytest 8.4.2。

| 编号 | 测试内容 | 预期结果 | 实际结果 | 是否通过 |
| --- | --- | --- | --- | --- |
| T01 | 点击前方无阻挡的箭头 | 飞出棋盘并消失 | 【运行后填写】 | 【待填写】 |
| T02 | 点击前方有阻挡的箭头 | 保持原位，失误减一 | 【运行后填写】 | 【待填写】 |
| T03 | 点击边缘且朝外的箭头 | 正常消除，无越界异常 | 【运行后填写】 | 【待填写】 |
| T04 | 消除本关全部箭头 | 显示通关并可进入下一关 | 【运行后填写】 | 【待填写】 |
| T05 | 失误次数耗尽 | 显示失败并允许重开 | 【运行后填写】 | 【待填写】 |
| T06 | 游戏中重新开始 | 布局、失误和计时恢复 | 【运行后填写】 | 【待填写】 |

【待填写：粘贴 `pytest -v` 和 `scripts/selfcheck.py` 的实际输出或截图】

## 六、PSP 表格

请根据 `PSP_TEMPLATE.md` 填写真实的预估与实际耗时。

【待填写：完整 PSP 表格及差异分析】

## 七、心得体会

这次作业是我第一次比较完整地使用 AIGC 参与一个小游戏从需求分析到测试交付的全过程。刚开始拿到题目时，我对需要实现哪些界面、怎样表示箭头、如何判断阻挡并没有完整思路。AIGC 帮我把任务拆分成规则层、界面层、关卡数据、动画和测试几个部分，并建议把核心逻辑与 Pygame 绘制分开。这个结构让后续修改界面时不需要反复改动游戏规则，也让核心逻辑能够在不打开窗口的情况下直接测试。

在编码过程中，AIGC 对路径检测、状态机、动画和求解器的实现提供了较大帮助。路径检测使用方向向量统一处理上下左右四种情况，从箭头的下一格开始一直扫描到边界，比为四个方向分别编写判断更加简洁。我也理解了其中的边界处理：只有坐标仍在棋盘内时才访问数组，因此边缘朝外的箭头不会产生越界错误。游戏状态则通过 `MENU`、`PLAYING`、`LEVEL_COMPLETE`、`FAILED` 和 `ALL_COMPLETE` 统一管理，界面只根据当前状态绘制相应内容。

AIGC 生成的结果并不是一次就完全符合要求，实际试玩仍然非常重要。最初箭头飞出动画播放时会锁定全部输入，导致我无法立即点击下一个箭头。发现这个问题后，我要求将单一动画改为动画列表，使多个飞出动画能够并行播放，同时只限制同一个正在碰撞的箭头，防止重复扣除失误次数。音效也经过了调整：最初正确操作使用普通上扬提示音，但和箭头飞出的动作不够贴合，后来改成由滤波噪声和扫频合成的“嗖”声。界面颜色同样经历了多次修改，最终使用米白色背景、绿色正常箭头和红色碰撞箭头，使正常状态和错误状态更加直观。这个过程让我认识到，AI 给出的方案只能作为初稿，最终效果必须由人实际体验和判断。

自动化测试和求解器对项目质量帮助很大。项目使用 pytest 覆盖了无阻挡消除、有阻挡扣除失误、边缘处理、通关、失败、重新开始、连续点击、两次提示和三星评分等情况。开发过程中，自检脚本还暴露过直接从 `scripts` 目录运行时找不到项目模块的问题，修正模块搜索路径后才真正做到可以按 README 中的命令运行。关卡方面，单靠肉眼很难保证没有死局，因此我使用 DFS 求解器验证每个关卡，并把求出的点击序列重新交给真实的游戏状态逐步执行。第四关不仅验证可解，还限制开局只有三个合法选择，使难度提升有明确依据，而不是单纯扩大棋盘。

通过阅读和修改代码，我对项目中的关键实现有了更清楚的理解。规则层在点击成功时立即把棋盘位置改为空格，动画层保存原来的坐标和方向继续绘制，所以规则状态与视觉效果不会互相干扰。剩余箭头数量通过扫描当前棋盘计算，而不是额外维护一个容易不同步的计数器。碰撞时先扣除失误次数，再根据剩余次数决定是否进入失败状态；通关或失败后冻结计时，保证结果界面显示的数据稳定。这些实现虽然不复杂，但让我体会到了明确的数据来源和状态边界对程序可靠性的重要性。

完成这次作业后，我对软件工程的认识不再只是“把代码写出来”。一个可以提交的项目还需要需求拆分、结构设计、版本管理、自动化测试、异常降级、文档和真实的运行验证。AIGC 的优势是可以快速提供思路、代码框架和测试用例，提高开发效率；但开发者仍然需要理解代码、发现实际体验中的问题，并判断修改是否真正满足需求。今后使用 AIGC 时，我会继续把它作为协作和检查工具，而不是直接接受所有生成结果，并通过测试、试玩和有意义的 Git Commit 保证每一次修改都可验证、可追踪。

## 八、运行方式

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

运行自动化测试：

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```
