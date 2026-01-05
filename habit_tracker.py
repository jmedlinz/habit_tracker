#!/usr/bin/env python3
"""
Daily Habit Tracker PDF Generator

Generates a daily habit tracker PDF form based on a customizable habits list.
"""

import argparse
import calendar
import sys
from pathlib import Path
from typing import List, Tuple

import yaml
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


class HabitTrackerConfig:
    """Configuration for the daily habit tracker PDF generator."""

    def __init__(self, config_path: str = "config.yaml"):
        """Load configuration from YAML file."""
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def get(self, *keys, default=None):
        """Get nested configuration value."""
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value


class Habit:
    """Base class for habits."""

    def __init__(self, name: str):
        self.name = name


class DailyHabit(Habit):
    """Represents a daily tracking habit."""


class GraphingHabit(Habit):
    """Represents a habit that requires graphing."""

    def __init__(self, name: str, min_value: float, max_value: float, division_interval: float = None):
        super().__init__(name)
        self.min_value = min_value
        self.max_value = max_value
        self.division_interval = division_interval


def parse_date_input(date_str: str) -> Tuple[int, int]:
    """
    Parse MM/YYYY format date string.

    Args:
        date_str: Date string in MM/YYYY format

    Returns:
        Tuple of (month, year)

    Raises:
        ValueError: If date format is invalid
    """
    try:
        month, year = date_str.split("/")
        month = int(month)
        year = int(year)

        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")

        return month, year
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid date format. Expected MM/YYYY, got: {date_str}") from e


def load_habits(habits_file: str) -> Tuple[List[DailyHabit], List[GraphingHabit]]:
    """
    Load habits from configuration file.

    Args:
        habits_file: Path to habits file

    Returns:
        Tuple of (daily_habits, graphing_habits)

    Raises:
        FileNotFoundError: If habits file doesn't exist
        ValueError: If habits file format is invalid
    """
    if not Path(habits_file).exists():
        raise FileNotFoundError(f"Habits file not found: {habits_file}")

    daily_habits = []
    graphing_habits = []
    current_section = None

    with open(habits_file) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Check for section headers
            if line.lower() == "# daily habits":
                current_section = "daily"
                continue
            elif line.lower() == "# graphing habits":
                current_section = "graphing"
                continue

            # Skip other comments
            if line.startswith("#"):
                continue

            # Parse habits based on current section
            if current_section == "daily":
                daily_habits.append(DailyHabit(line))
            elif current_section == "graphing":
                try:
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) < 3:
                        raise ValueError(
                            f"Line {line_num}: Graphing habit must have format: name, min, max[, division_interval]"
                        )
                    name, min_val, max_val = parts[0], parts[1], parts[2]
                    division_interval = float(parts[3]) if len(parts) > 3 else None
                    graphing_habits.append(GraphingHabit(name, float(min_val), float(max_val), division_interval))
                except (ValueError, IndexError) as e:
                    raise ValueError(f"Line {line_num}: Invalid graphing habit format: {line}") from e

    return daily_habits, graphing_habits


def _calculate_y_axis_labels(min_val: float, max_val: float, divisions: int) -> List[float]:
    """
    Calculate evenly-spaced Y-axis label values.

    Args:
        min_val: Minimum value
        max_val: Maximum value
        divisions: Number of divisions (including min and max)

    Returns:
        List of label values
    """
    if divisions < 2:
        divisions = 2

    step = (max_val - min_val) / (divisions - 1)
    return [min_val + i * step for i in range(divisions)]


def _draw_title(
    c: canvas.Canvas, month: int, year: int, config: HabitTrackerConfig, page_width: float, page_height: float
):
    """Draw the title section."""
    month_name = calendar.month_name[month]
    title = f"Daily Habit Tracker, {month_name} {year}"

    title_size = config.get("fonts", "title_size", default=14)
    margin_top = config.get("page", "margins", "top", default=0.5) * inch

    c.setFont("Helvetica-Bold", title_size)
    title_width = c.stringWidth(title, "Helvetica-Bold", title_size)
    x = (page_width - title_width) / 2
    y = page_height - margin_top

    c.drawString(x, y, title)
    return y - 0.225 * inch  # Return Y position for next section


def _draw_calendar_header(
    c: canvas.Canvas,
    month: int,
    year: int,
    config: HabitTrackerConfig,
    start_x: float,
    start_y: float,
    col_width: float,
    num_days: int,
):
    """Draw the calendar header with day abbreviations and dates."""
    day_size = config.get("fonts", "day_label_size", default=8)

    # Get the first day of the month (0=Monday, 6=Sunday in calendar module)
    first_weekday = calendar.monthrange(year, month)[0]
    # Convert to 0=Sunday format
    first_weekday = (first_weekday + 1) % 7

    # Day abbreviations
    day_abbr = ["S", "M", "T", "W", "Th", "F", "S"]

    # Draw day abbreviations
    c.setFont("Helvetica", day_size)
    y_pos = start_y
    for day in range(1, num_days + 1):
        weekday_idx = (first_weekday + day - 1) % 7
        x_pos = start_x + (day - 1) * col_width + col_width / 2
        abbr_width = c.stringWidth(day_abbr[weekday_idx], "Helvetica", day_size)
        c.drawString(x_pos - abbr_width / 2, y_pos, day_abbr[weekday_idx])

    # Draw date numbers
    c.setFont("Helvetica", day_size)
    y_pos -= 0.12 * inch
    for day in range(1, num_days + 1):
        x_pos = start_x + (day - 1) * col_width + col_width / 2
        day_str = str(day)
        day_width = c.stringWidth(day_str, "Helvetica", day_size)
        c.drawString(x_pos - day_width / 2, y_pos, day_str)

    return y_pos - 0.1 * inch  # Return Y position for next section


def _draw_daily_habits_grid(
    c: canvas.Canvas,
    daily_habits: List[DailyHabit],
    month: int,
    year: int,
    config: HabitTrackerConfig,
    start_x: float,
    start_y: float,
    col_width: float,
    num_days: int,
):
    """Draw the daily habits grid with weekend separators."""
    row_height = col_width  # Make boxes square
    habit_size = config.get("fonts", "habit_label_size", default=9)
    weekend_sep_width = config.get("daily_habits", "weekend_separator_width", default=2)

    # Calculate label column width (wider for habit names)
    label_width = 1.5 * inch
    grid_width = col_width * num_days

    # Get first weekday to determine weekend positions
    first_weekday = calendar.monthrange(year, month)[0]
    first_weekday = (first_weekday + 1) % 7  # Convert to Sunday=0

    y_pos = start_y

    # Draw habits
    c.setFont("Helvetica", habit_size)
    for habit in daily_habits:
        # Draw habit label - centered vertically
        label_y = y_pos - row_height / 2 - habit_size / 2
        c.drawString(start_x + 0.1 * inch, label_y, habit.name)

        # Draw horizontal line above
        c.line(start_x, y_pos, start_x + label_width + grid_width, y_pos)

        # Draw vertical lines for each day
        for day in range(num_days + 1):
            x_pos = start_x + label_width + day * col_width
            weekday_idx = (first_weekday + day - 1) % 7

            # Thicker line between Friday/Saturday and Sunday/Monday
            if day > 0 and (weekday_idx == 0 or weekday_idx == 5):
                c.setLineWidth(weekend_sep_width)
                c.line(x_pos, y_pos, x_pos, y_pos - row_height)
                c.setLineWidth(1)
            else:
                c.line(x_pos, y_pos, x_pos, y_pos - row_height)

        # Draw label column separator
        c.line(start_x + label_width, y_pos, start_x + label_width, y_pos - row_height)

        # Draw left edge
        c.line(start_x, y_pos, start_x, y_pos - row_height)

        y_pos -= row_height

    # Draw bottom line
    c.line(start_x, y_pos, start_x + label_width + grid_width, y_pos)

    return y_pos  # Return Y position for next section


def _draw_graphing_habits_section(
    c: canvas.Canvas,
    graphing_habits: List[GraphingHabit],
    config: HabitTrackerConfig,
    start_x: float,
    start_y: float,
    col_width: float,
    num_days: int,
):
    """Draw the graphing habits section with dot grids."""
    dot_radius = config.get("graphing_habits", "dot_radius", default=0.02) * inch
    y_divisions = config.get("graphing_habits", "y_axis_divisions", default=5)
    habit_size = config.get("fonts", "habit_label_size", default=9)
    dot_color = config.get("colors", "dot", default=[200, 200, 200])

    label_width = 1.5 * inch
    grid_width = col_width * num_days

    # Calculate section height based on divisions
    # Number of rows = divisions + (divisions - 1) gaps = 2 * divisions - 1
    num_rows = y_divisions * 2 - 1
    # Use col_width for vertical spacing to match horizontal spacing
    section_height = num_rows * col_width

    y_pos = start_y
    c.setFont("Helvetica", habit_size)

    for habit in graphing_habits:
        # Use per-habit division_interval if specified, otherwise calculate from y_divisions
        if habit.division_interval is not None:
            y_divisions_for_habit = int((habit.max_value - habit.min_value) / habit.division_interval) + 1
        else:
            y_divisions_for_habit = y_divisions

        # Calculate section height based on divisions for this habit
        # Number of rows = divisions + (divisions - 1) gaps = 2 * divisions - 1
        num_rows = y_divisions_for_habit * 2 - 1
        # Use col_width for vertical spacing to match horizontal spacing
        section_height = num_rows * col_width

        # Draw habit name (only if not blank)
        if habit.name:
            c.drawString(start_x + 0.1 * inch, y_pos - 0.2 * inch, habit.name)

        # Draw dots in grid area setup
        grid_start_x = start_x + label_width
        # Center the dots vertically within the section
        # Dots span (num_rows - 1) * col_width, so center with col_width margin
        grid_start_y = y_pos - section_height + col_width / 2

        # Draw Y-axis labels - positioned to the left of the dots, within the label box (only if habit has a name)
        if habit.name:
            y_labels = _calculate_y_axis_labels(habit.min_value, habit.max_value, y_divisions_for_habit)
            for label_val in y_labels:
                # Position label based on its value between min and max
                normalized_pos = (label_val - habit.min_value) / (habit.max_value - habit.min_value)
                label_y = grid_start_y + normalized_pos * (num_rows - 1) * col_width
                label_text = f"{label_val:.0f}" if label_val == int(label_val) else f"{label_val:.1f}"
                # Right-align within the label column
                label_width_px = c.stringWidth(label_text, "Helvetica", habit_size)
                c.drawString(
                    start_x + label_width - label_width_px - 0.1 * inch, label_y - 0.05 * inch, label_text
                )

        # Draw dots in grid area
        c.setFillColorRGB(dot_color[0] / 255, dot_color[1] / 255, dot_color[2] / 255)

        # Draw all dots - one per day column, all rows
        for row in range(0, num_rows):
            for col in range(num_days):
                dot_x = grid_start_x + (col + 0.5) * col_width
                dot_y = grid_start_y + row * col_width
                c.circle(dot_x, dot_y, dot_radius, fill=1, stroke=0)

        # Reset to black
        c.setFillColorRGB(0, 0, 0)

        # Draw borders
        c.line(start_x, y_pos, start_x, y_pos - section_height)  # Left edge
        c.line(start_x + label_width, y_pos, start_x + label_width, y_pos - section_height)  # Label separator
        c.line(
            start_x + label_width + grid_width, y_pos, start_x + label_width + grid_width, y_pos - section_height
        )  # Right edge
        c.line(
            start_x, y_pos - section_height, start_x + label_width + grid_width, y_pos - section_height
        )  # Bottom

        y_pos -= section_height

    return y_pos


def generate_habit_tracker_pdf(month: int, year: int, habits_file: str, config_file: str = "config.yaml"):
    """
    Generate a daily habit tracker PDF for the specified month and year.

    Args:
        month: Month (1-12)
        year: Year (e.g., 2025)
        habits_file: Path to habits configuration file
        config_file: Path to configuration YAML file
    """
    # Load configuration
    config = HabitTrackerConfig(config_file)

    # Load habits
    daily_habits, graphing_habits = load_habits(habits_file)

    # Get number of days in month
    num_days = calendar.monthrange(year, month)[1]

    # Setup page
    orientation = config.get("page", "orientation", default="portrait")
    if orientation.lower() == "landscape":
        page_width, page_height = letter[1], letter[0]  # Swap dimensions for landscape
    else:
        page_width, page_height = letter

    margin_left = config.get("page", "margins", "left", default=0.5) * inch
    margin_right = config.get("page", "margins", "right", default=0.5) * inch

    # Calculate column width for days
    label_width = 1.5 * inch
    available_width = page_width - margin_left - margin_right - label_width
    col_width = available_width / num_days

    # Create output filename
    output_dir = config.get("output", "directory", default=".")
    filename_format = config.get("output", "filename_format", default="habit_tracker_{year}_{month:02d}.pdf")
    output_filename = filename_format.format(year=year, month=month)
    output_path = Path(output_dir) / output_filename

    # Create PDF with the correct page size
    c = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))

    # Draw title
    y_pos = _draw_title(c, month, year, config, page_width, page_height)

    # Draw calendar header
    y_pos = _draw_calendar_header(c, month, year, config, margin_left + label_width, y_pos, col_width, num_days)

    # Draw daily habits grid
    if daily_habits:
        y_pos = _draw_daily_habits_grid(
            c, daily_habits, month, year, config, margin_left, y_pos, col_width, num_days
        )

    # Calculate space needed for graphing habits
    margin_bottom = config.get("page", "margins", "bottom", default=0.5) * inch
    y_divisions_config = config.get("graphing_habits", "y_axis_divisions", default=5)

    graphing_space_needed = 0
    for habit in graphing_habits:
        if habit.division_interval is not None:
            y_divs = int((habit.max_value - habit.min_value) / habit.division_interval) + 1
        else:
            y_divs = y_divisions_config
        num_rows = y_divs * 2 - 1
        section_height = num_rows * col_width
        graphing_space_needed += section_height

    # Calculate remaining space for blank rows (up to 4)
    available_space = y_pos - margin_bottom - graphing_space_needed
    blank_rows_to_add = min(4, int(available_space / col_width))

    # Add blank daily habit rows if there's room
    if blank_rows_to_add > 0:
        blank_habits = [DailyHabit("") for _ in range(blank_rows_to_add)]
        y_pos = _draw_daily_habits_grid(
            c, blank_habits, month, year, config, margin_left, y_pos, col_width, num_days
        )

    # Check if there's room for a blank graphing habit (1-3 by 1s)
    blank_graphing_divs = 3  # 1, 2, 3
    blank_graphing_rows = blank_graphing_divs * 2 - 1
    blank_graphing_height = blank_graphing_rows * col_width
    remaining_space = y_pos - margin_bottom - graphing_space_needed

    if remaining_space >= blank_graphing_height:
        # Add blank graphing habit at the end
        graphing_habits = list(graphing_habits) + [GraphingHabit("", 1, 3, 1)]

    # Draw graphing habits section
    if graphing_habits:
        _draw_graphing_habits_section(c, graphing_habits, config, margin_left, y_pos, col_width, num_days)

    # Save PDF
    c.save()

    print(f"Generated habit tracker PDF: {output_path}")


def main():
    """Main entry point for the daily habit tracker generator."""
    parser = argparse.ArgumentParser(
        description="Generate a daily habit tracker PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --month 11/2025
  %(prog)s --month 11/2025 --habits my_habits.txt
  %(prog)s  # Interactive mode
        """,
    )

    parser.add_argument(
        "--month",
        "-m",
        help="Month and year in MM/YYYY format (e.g., 11/2025)",
    )

    parser.add_argument(
        "--habits",
        "-f",
        help="Path to habits configuration file (default: from config.yaml)",
    )

    parser.add_argument(
        "--config",
        "-c",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    # Load config to get default habits file
    try:
        config = HabitTrackerConfig(args.config)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {args.config}")
        print("Please create a config.yaml file or specify a different config file with --config")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # Get month/year
    if args.month:
        date_input = args.month
    else:
        date_input = input("Enter month and year (MM/YYYY): ")

    try:
        month, year = parse_date_input(date_input)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Get habits file
    habits_file = args.habits or config.get("input", "habits_file", default="habits.txt")

    # Generate PDF
    try:
        generate_habit_tracker_pdf(month, year, habits_file, args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
