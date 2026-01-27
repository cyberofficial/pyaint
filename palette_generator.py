"""
Color Palette Generator Module

Analyzes images to extract color frequencies and generates GIMP-compatible CSS palettes.
"""

from collections import defaultdict
from typing import List, Tuple, Dict, Set
from PIL import Image


class ColorPaletteGenerator:
    """Generates color palettes from images with frequency-based selection."""
    
    def __init__(self, image_path: str, ignore_white: bool = True):
        """
        Initialize the palette generator.
        
        Args:
            image_path: Path to the image file
            ignore_white: Whether to ignore white pixels (255, 255, 255)
        """
        self.image_path = image_path
        self.ignore_white = ignore_white
        self.color_counts = defaultdict(int)
        self.total_pixels = 0
        self.sorted_colors = []
        
    def analyze_image(self):
        """Analyze the image and count color frequencies."""
        try:
            img = Image.open(self.image_path).convert('RGB')
            pixels = img.load()
            w, h = img.size
            
            print(f"[PaletteGen] Analyzing image: {self.image_path}")
            print(f"[PaletteGen] Image size: {w}x{h} ({w*h} pixels)")
            
            # Count each unique color
            for y in range(h):
                for x in range(w):
                    r, g, b = pixels[x, y]
                    color = (r, g, b)
                    
                    # Skip white if configured
                    if self.ignore_white and color == (255, 255, 255):
                        continue
                    
                    self.color_counts[color] += 1
                    self.total_pixels += 1
            
            # Sort colors by frequency (descending)
            self.sorted_colors = sorted(
                self.color_counts.items(),
                key=lambda item: item[1],
                reverse=True
            )
            
            print(f"[PaletteGen] Found {len(self.sorted_colors)} unique colors")
            print(f"[PaletteGen] Total non-white pixels: {self.total_pixels}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to analyze image: {e}")
    
    def get_palette(self, num_colors: int) -> Tuple[List[Tuple[int, int, int]], List[int], Dict[int, int]]:
        """
        Get the top N colors from the image.
        
        Args:
            num_colors: Number of colors to return (1-256)
        
        Returns:
            Tuple of:
            - List of (r, g, b) tuples for selected colors
            - List of pixel counts for each color
            - Dictionary of color_index -> pixel_count
        """
        if not self.sorted_colors:
            self.analyze_image()
        
        # Clamp num_colors to available colors
        num_colors = min(num_colors, len(self.sorted_colors))
        
        # Get top N colors
        selected = self.sorted_colors[:num_colors]
        
        # Extract colors and counts
        colors = [color for color, count in selected]
        counts = [count for color, count in selected]
        color_map = {i: count for i, (color, count) in enumerate(selected)}
        
        return colors, counts, color_map
    
    def find_ties(self, num_colors: int) -> Dict[int, List[Tuple[int, int, int]]]:
        """
        Find colors that are tied at the selection boundary.
        
        Args:
            num_colors: Number of colors being selected
        
        Returns:
            Dictionary mapping tie_index -> list of tied (r, g, b) colors
            tie_index is the position in the selection where the tie occurs
        """
        if not self.sorted_colors:
            self.analyze_image()
        
        # Clamp to available colors
        num_colors = min(num_colors, len(self.sorted_colors))
        
        if num_colors == 0 or num_colors >= len(self.sorted_colors):
            return {}
        
        # Get the count at the boundary
        boundary_count = self.sorted_colors[num_colors - 1][1]
        
        # Find all colors with the same count at and beyond boundary
        ties = {}
        tie_colors = []
        
        for i, (color, count) in enumerate(self.sorted_colors):
            if count == boundary_count:
                tie_colors.append((i, color))
        
        # If there are ties, group them
        if len(tie_colors) > 1:
            # Find the first occurrence of this count
            first_index = min(i for i, color in tie_colors)
            # Check if the boundary is within this tie group
            if first_index < num_colors <= max(i for i, color in tie_colors):
                ties[first_index] = [color for i, color in tie_colors]
                print(f"[PaletteGen] Found tie at index {first_index}: {len(ties[first_index])} colors with {boundary_count} pixels")
        
        return ties
    
    def get_color_percentage(self, count: int) -> float:
        """
        Calculate the percentage of a color in the image.
        
        Args:
            count: Pixel count for the color
        
        Returns:
            Percentage (0.0 to 100.0)
        """
        if self.total_pixels == 0:
            return 0.0
        return (count / self.total_pixels) * 100.0
    
    def export_gimp_css(self, colors: List[Tuple[int, int, int]], output_path: str):
        """
        Export colors as GIMP-compatible CSS file.
        
        Args:
            colors: List of (r, g, b) tuples
            output_path: Path to save the CSS file
        """
        try:
            with open(output_path, 'w') as f:
                f.write("/* Generated with Pyaint Palette Export */\n")
                for i, (r, g, b) in enumerate(colors):
                    f.write(f".{i} {{ color: rgb({r}, {g}, {b}); }}\n")
            
            print(f"[PaletteGen] Exported {len(colors)} colors to: {output_path}")
            return True
        except Exception as e:
            print(f"[PaletteGen] Failed to export: {e}")
            return False
    
    def get_color_stats(self) -> List[Dict]:
        """
        Get statistics about all colors in the image.
        
        Returns:
            List of dictionaries with color info (color, count, percentage)
        """
        if not self.sorted_colors:
            self.analyze_image()
        
        stats = []
        for color, count in self.sorted_colors:
            stats.append({
                'color': color,
                'count': count,
                'percentage': self.get_color_percentage(count)
            })
        
        return stats