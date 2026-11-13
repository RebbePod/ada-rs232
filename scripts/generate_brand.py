"""Render the project's simple amplifier icon from native drawing primitives."""

from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    """Generate transparent 256px and 512px icons for Home Assistant and HACS."""
    output = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "ada_rs232"
        / "brand"
    )
    output.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (1024, 1024))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((48, 224, 976, 800), radius=76, fill="#15283f")
    draw.rounded_rectangle((80, 256, 944, 768), radius=48, outline="#73c8f5", width=16)
    for y in (336, 400, 464):
        draw.rounded_rectangle((160, y, 864, y + 20), radius=10, fill="#73c8f5")
    for zone in range(8):
        x = 176 + zone * 96
        draw.ellipse((x - 22, 592, x + 22, 636), fill="#65e5ae")
    draw.rounded_rectangle((160, 816, 304, 856), radius=12, fill="#15283f")
    draw.rounded_rectangle((720, 816, 864, 856), radius=12, fill="#15283f")
    for size, name in ((256, "icon.png"), (512, "icon@2x.png")):
        image.resize((size, size), Image.Resampling.LANCZOS).save(output / name)


if __name__ == "__main__":
    main()
