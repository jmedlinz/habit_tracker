# Daily Habit Tracker PDF Generator

Generate customizable daily habit tracker PDF forms with daily tracking grids and graphing sections.

## Features

- **Daily Habits**: Track daily habits with checkboxes organized by day of the week
- **Graphing Habits**: Track metrics with customizable Y-axis scales for manual graphing
- **Flexible Configuration**: Customize fonts, colors, spacing, and layout via YAML config
- **Per-Habit Y-Axis Scale**: Specify different Y-axis divisions for each graphing habit
- **Weekend Separators**: Visual separation between weekdays and weekends
- **Automatic Date Calculation**: Correct calendar generation for any month/year

## Installation

Requires Python 3.11+

```bash
poetry install
```

## Usage

### Interactive Mode
```bash
poetry run python habit_tracker.py
```
Then enter the month and year when prompted (e.g., `11/2025`)

### Command Line
```bash
poetry run python habit_tracker.py --month 11/2025 --habits habits.txt --config config.yaml
```

### Options
- `--month`, `-m`: Month and year in MM/YYYY format (e.g., `11/2025`)
- `--habits`, `-f`: Path to habits configuration file (default: from config.yaml)
- `--config`, `-c`: Path to configuration file (default: `config.yaml`)

## Habits File Format

Create a `habits.txt` file with the following structure:

```
# Daily Habits
Habit 1
Habit 2
Habit 3

# Graphing Habits
Weight, 140, 180, 10
Work Start Time, 6, 9, 1
```

### Daily Habits
- Simple list of habit names (one per line)
- Will appear as rows in the daily tracking grid

### Graphing Habits
- Format: `name, min_value, max_value, [division_interval]`
- `name`: Habit name
- `min_value`: Minimum value for Y-axis
- `max_value`: Maximum value for Y-axis
- `division_interval` (optional): Interval between Y-axis divisions (e.g., 10, 1, 0.5)
  - If omitted, uses `y_axis_divisions` from config.yaml

## Configuration

Edit `config.yaml` to customize:

- **Page Setup**: Size, orientation, margins
- **Fonts**: Family, sizes for title, headers, labels
- **Colors**: Grid lines, dots, text (RGB values)
- **Daily Habits**: Row height, weekend separator width
- **Graphing Habits**: Dot spacing, dot radius
- **Output**: Directory and filename format
- **Input**: Default habits file path

Example custom spacing:
```yaml
daily_habits:
  row_height: 0.25  # Smaller rows
graphing_habits:
  dot_radius: 0.025  # Larger dots
```

## Output

Generates a PDF file named `habit_tracker_YYYY_MM.pdf` (e.g., `habit_tracker_2025_11.pdf`)

## Example

With `habits_sample.txt`:
- Daily Habits: Wake Up At 6am, Take Vitamins, Morning Review, Reading Goal, Devotional, Make Bed, Exercise, Weekly Review
- Graphing Habits: Weight (140-180 by 10s), Work Start Time (6-9 by 1s)

Run:
```bash
poetry run python habit_tracker.py --month 12/2025 --habits habits_sample.txt
```

This generates a portrait letter-size PDF with:
- Daily habits grid with weekend separators
- Weight graph with divisions at 180, 170, 160, 150, 140
- Work Start Time graph with divisions at 9, 8, 7, 6

## License

See LICENSE file
