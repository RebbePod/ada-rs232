"""Package the supplied ADA artwork for Home Assistant's branding formats."""

from pathlib import Path

from PIL import Image, ImageOps


def main() -> None:
    """Export square marks and full wordmarks in light/dark and 1x/2x sizes."""
    root = Path(__file__).resolve().parents[1]
    output = root / "custom_components" / "ada_rs232" / "brand"
    output.mkdir(parents=True, exist_ok=True)
    with Image.open(root / "assets" / "ada-logo-source.png") as image:
        source = image.convert("RGBA")
    bounds = source.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError("The source artwork is empty")

    # The supplied wordmark has a clear gap at x=800..827 separating the ADA
    # mark from the company name. Retain the original letterforms and alpha.
    mark = source.crop((bounds[0], bounds[1], 800, bounds[3]))
    logo = source.crop(bounds)

    for prefix, dark in (("", False), ("dark_", True)):
        for scale, suffix in ((1, ""), (2, "@2x")):
            icon_size = 256 * scale
            icon = Image.new("RGBA", (icon_size, icon_size))
            fitted = ImageOps.contain(
                mark, (icon_size, icon_size), Image.Resampling.LANCZOS
            )
            icon.alpha_composite(
                fitted,
                ((icon_size - fitted.width) // 2, (icon_size - fitted.height) // 2),
            )
            height = 256 * scale
            wordmark = logo.resize(
                (round(logo.width * height / logo.height), height),
                Image.Resampling.LANCZOS,
            )
            for name, asset in (("icon", icon), ("logo", wordmark)):
                if dark:
                    alpha = asset.getchannel("A")
                    asset = Image.new("RGBA", asset.size, "white")
                    asset.putalpha(alpha)
                asset.save(output / f"{prefix}{name}{suffix}.png", optimize=True)


if __name__ == "__main__":
    main()
