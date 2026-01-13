from PIL import Image, ImageDraw, ImageFont
import os


def process_thumbnail(
    source_path: str, target_path: str, text: str = "Korean Translation"
):
    """
    Copies the thumbnail from source to target and adds a text overlay.
    """
    try:
        # Check if source thumbnail exists (usually thumbnail.png)
        possible_names = [
            "thumbnail.png",
            "thumbnail.jpg",
            "preview.png",
            "preview.jpg",
        ]
        source_file = None
        for name in possible_names:
            p = os.path.join(source_path, name)
            if os.path.exists(p):
                source_file = p
                break

        if not source_file:
            return False

        img = Image.open(source_file).convert("RGBA")
        width, height = img.size

        # Draw Overlay
        draw = ImageDraw.Draw(img)

        # Calculate font size (10% of height)
        font_size = int(height * 0.15)
        try:
            # Try to load a font, fallback to default
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Text Metrics
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Position: Center Bottom
        x = (width - text_width) / 2
        y = height - text_height - 20

        # Draw Shadow/Outline
        shadow_color = "black"
        for adj in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
            draw.text((x + adj[0], y + adj[1]), text, font=font, fill=shadow_color)

        # Draw Main Text
        draw.text((x, y), text, font=font, fill="white")

        # Save to target
        target_file = os.path.join(target_path, "thumbnail.png")
        img.save(target_file)
        return True

    except Exception as e:
        print(f"Thumbnail processing failed: {e}")
        return False
