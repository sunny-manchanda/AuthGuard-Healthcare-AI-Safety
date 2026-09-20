from __future__ import annotations

import html
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"


def svg_text(text: str) -> str:
    return html.escape(str(text), quote=True)


def containment_chart(metrics: dict) -> str:
    width, height = 1000, 560
    baseline = metrics["baseline_attack_containment_rate"]
    protected = metrics["protected_attack_containment_rate"]
    bars = [("Baseline workflow", baseline, "#C9534A"), ("Protected AuthGuard", protected, "#147D64")]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#F7F4EC"/>',
        '<text x="60" y="70" font-family="Arial" font-size="34" font-weight="700" fill="#16324F">Attack containment before and after controls</text>',
        f'<text x="60" y="108" font-family="Arial" font-size="18" fill="#4D5B66">{metrics["malicious_tests"]} synthetic adversarial tests; same suite used for both workflows</text>',
    ]
    chart_x, chart_y, chart_w = 315, 185, 600
    for index, (label, value, color) in enumerate(bars):
        y = chart_y + index * 145
        parts.append(f'<text x="60" y="{y + 37}" font-family="Arial" font-size="22" fill="#16324F">{svg_text(label)}</text>')
        parts.append(f'<rect x="{chart_x}" y="{y}" width="{chart_w}" height="58" rx="8" fill="#DFE6E9"/>')
        parts.append(f'<rect x="{chart_x}" y="{y}" width="{chart_w * value:.1f}" height="58" rx="8" fill="{color}"/>')
        parts.append(f'<text x="{chart_x + chart_w - 12}" y="{y + 39}" text-anchor="end" font-family="Arial" font-size="24" font-weight="700" fill="#16324F">{value:.1%}</text>')
    parts.extend(
        [
            '<line x1="315" y1="480" x2="915" y2="480" stroke="#8A969E" stroke-width="2"/>',
            '<text x="315" y="515" font-family="Arial" font-size="16" fill="#4D5B66">0%</text>',
            '<text x="915" y="515" text-anchor="end" font-family="Arial" font-size="16" fill="#4D5B66">100%</text>',
            '<text x="60" y="545" font-family="Arial" font-size="14" fill="#66747D">Synthetic evaluation results do not establish production security.</text>',
            '</svg>',
        ]
    )
    return "".join(parts)


def family_heatmap(metrics: dict) -> str:
    families = list(metrics["by_family"].items())
    row_h = 48
    width = 1100
    height = 175 + len(families) * row_h
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#F7F4EC"/>',
        '<text x="45" y="55" font-family="Arial" font-size="32" font-weight="700" fill="#16324F">Red-team results by attack family</text>',
        '<text x="45" y="92" font-family="Arial" font-size="17" fill="#4D5B66">PASS means the observed queue matched the defined safe outcome.</text>',
        '<text x="510" y="138" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700" fill="#16324F">Tests</text>',
        '<text x="700" y="138" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700" fill="#16324F">Baseline</text>',
        '<text x="900" y="138" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700" fill="#16324F">Protected</text>',
    ]
    y = 158
    for family, stat in families:
        count = stat["count"]
        baseline = stat["baseline_pass"] / count
        protected = stat["protected_pass"] / count
        parts.append(f'<rect x="35" y="{y}" width="1030" height="{row_h - 5}" rx="6" fill="#FFFFFF" stroke="#D8DEE2"/>')
        parts.append(f'<text x="55" y="{y + 29}" font-family="Arial" font-size="17" fill="#16324F">{svg_text(family)}</text>')
        parts.append(f'<text x="510" y="{y + 29}" text-anchor="middle" font-family="Arial" font-size="17" fill="#4D5B66">{count}</text>')
        for x, value in ((700, baseline), (900, protected)):
            color = "#147D64" if value == 1 else "#E0A12B" if value >= 0.5 else "#C9534A"
            parts.append(f'<rect x="{x - 65}" y="{y + 7}" width="130" height="29" rx="14" fill="{color}"/>')
            parts.append(f'<text x="{x}" y="{y + 28}" text-anchor="middle" font-family="Arial" font-size="16" font-weight="700" fill="#FFFFFF">{value:.0%}</text>')
        y += row_h
    parts.append('</svg>')
    return "".join(parts)


def evidence_summary(metrics: dict) -> str:
    return f"""# AuthGuard evaluation snapshot

- Total tests: **{metrics['total_tests']}**
- Malicious/adversarial tests: **{metrics['malicious_tests']}**
- Clean and privacy-preserving controls: **{metrics['clean_controls']}**
- Baseline attack containment: **{metrics['baseline_attack_containment_rate']:.1%}**
- Protected attack containment: **{metrics['protected_attack_containment_rate']:.1%}**
- Protected clean-case accuracy: **{metrics['protected_clean_accuracy']:.1%}**

These are deterministic results on a synthetic, deliberately constructed test set. They demonstrate the controls in this prototype; they are not a production-security or clinical-performance claim.
"""


def _font(size: int, bold: bool = False):
    filename = "arialbd.ttf" if bold else "arial.ttf"
    candidates = [Path("C:/Windows/Fonts") / filename, Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def containment_png(metrics: dict) -> Image.Image:
    image = Image.new("RGB", (1400, 800), "#F7F4EC")
    draw = ImageDraw.Draw(image)
    draw.text((70, 65), "Attack containment before and after controls", font=_font(44, True), fill="#16324F")
    draw.text((70, 125), f"{metrics['malicious_tests']} synthetic adversarial tests; identical suite used for both workflows", font=_font(24), fill="#4D5B66")
    bars = [
        ("Baseline workflow", metrics["baseline_attack_containment_rate"], "#C9534A"),
        ("Protected AuthGuard", metrics["protected_attack_containment_rate"], "#147D64"),
    ]
    bar_x, bar_w = 445, 820
    for index, (label, value, color) in enumerate(bars):
        y = 275 + index * 190
        draw.text((70, y + 18), label, font=_font(30, True), fill="#16324F")
        draw.rounded_rectangle((bar_x, y, bar_x + bar_w, y + 82), radius=14, fill="#DFE6E9")
        draw.rounded_rectangle((bar_x, y, bar_x + int(bar_w * value), y + 82), radius=14, fill=color)
        draw.text((bar_x + bar_w - 15, y + 20), f"{value:.1%}", anchor="ra", font=_font(30, True), fill="#16324F")
    draw.text((70, 735), "Synthetic evaluation results do not establish production security.", font=_font(20), fill="#66747D")
    return image


def heatmap_png(metrics: dict) -> Image.Image:
    families = list(metrics["by_family"].items())
    image = Image.new("RGB", (1450, 220 + 68 * len(families)), "#F7F4EC")
    draw = ImageDraw.Draw(image)
    draw.text((55, 45), "Red-team results by attack family", font=_font(42, True), fill="#16324F")
    draw.text((55, 105), "PASS means the observed queue matched the defined safe outcome.", font=_font(23), fill="#4D5B66")
    columns = {"tests": 725, "baseline": 980, "protected": 1260}
    for title, x in (("Tests", columns["tests"]), ("Baseline", columns["baseline"]), ("Protected", columns["protected"])):
        draw.text((x, 165), title, anchor="ma", font=_font(24, True), fill="#16324F")
    y = 200
    for family, stat in families:
        count = stat["count"]
        baseline = stat["baseline_pass"] / count
        protected = stat["protected_pass"] / count
        draw.rounded_rectangle((45, y, 1405, y + 55), radius=8, fill="#FFFFFF", outline="#D8DEE2")
        draw.text((65, y + 14), family, font=_font(22), fill="#16324F")
        draw.text((columns["tests"], y + 28), str(count), anchor="mm", font=_font(22), fill="#4D5B66")
        for x, value in ((columns["baseline"], baseline), (columns["protected"], protected)):
            color = "#147D64" if value == 1 else "#E0A12B" if value >= 0.5 else "#C9534A"
            draw.rounded_rectangle((x - 78, y + 9, x + 78, y + 46), radius=18, fill=color)
            draw.text((x, y + 28), f"{value:.0%}", anchor="mm", font=_font(20, True), fill="#FFFFFF")
        y += 68
    return image


def main() -> None:
    with (OUTPUTS / "red_team_metrics.json").open("r", encoding="utf-8") as handle:
        metrics = json.load(handle)
    (OUTPUTS / "attack_containment.svg").write_text(containment_chart(metrics), encoding="utf-8")
    (OUTPUTS / "attack_family_heatmap.svg").write_text(family_heatmap(metrics), encoding="utf-8")
    (OUTPUTS / "EVALUATION_SNAPSHOT.md").write_text(evidence_summary(metrics), encoding="utf-8")
    containment_png(metrics).save(OUTPUTS / "attack_containment.png")
    heatmap_png(metrics).save(OUTPUTS / "attack_family_heatmap.png")
    print("Generated SVG/PNG charts and EVALUATION_SNAPSHOT.md")


if __name__ == "__main__":
    main()
