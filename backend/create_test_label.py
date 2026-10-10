from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

WIDTH = 1400
HEIGHT = 1800

image = Image.new("RGB", (WIDTH, HEIGHT), "white")
draw = ImageDraw.Draw(image)

font_candidates = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
]

bold_candidates = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
]

def find_font(candidates, size):
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()

title = find_font(bold_candidates, 72)
large = find_font(bold_candidates, 50)
medium = find_font(font_candidates, 40)
warning_heading = find_font(bold_candidates, 34)
warning_font = find_font(font_candidates, 30)

y = 100

draw.text((100, y), "OLD TOM DISTILLERY", font=title, fill="black")
y += 140

draw.text(
    (100, y),
    "Kentucky Straight Bourbon Whiskey",
    font=large,
    fill="black",
)
y += 120

draw.text(
    (100, y),
    "45% Alc./Vol. (90 Proof)",
    font=medium,
    fill="black",
)
y += 80

draw.text(
    (100, y),
    "750 mL",
    font=medium,
    fill="black",
)
y += 90

draw.text(
    (100, y),
    "Produced and Bottled by Old Tom Distillery",
    font=medium,
    fill="black",
)
y += 65

draw.text(
    (100, y),
    "Louisville, Kentucky, United States",
    font=medium,
    fill="black",
)
y += 150

draw.text(
    (100, y),
    "GOVERNMENT WARNING:",
    font=warning_heading,
    fill="black",
)
y += 60

warning_lines = [
    "(1) According to the Surgeon General, women should not",
    "drink alcoholic beverages during pregnancy because of",
    "the risk of birth defects.",
    "",
    "(2) Consumption of alcoholic beverages impairs your",
    "ability to drive a car or operate machinery, and may",
    "cause health problems.",
]

for line in warning_lines:
    draw.text((100, y), line, font=warning_font, fill="black")
    y += 48

image.save("old_tom_test_label.png")

print("Created:", Path("old_tom_test_label.png").resolve())
