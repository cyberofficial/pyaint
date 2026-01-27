"""
Color Palette Generator Module

Analyzes images to extract color frequencies and generates GIMP-compatible CSS palettes.
"""

from collections import defaultdict
from typing import List, Tuple, Dict, Set, Optional
from PIL import Image
import math


class ColorPaletteGenerator:
    """Generates color palettes from images with multiple selection algorithms."""
    
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
        self.algorithm = "frequency"  # Default algorithm
        
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
            
            # Sort colors by frequency (descending) as default
            self.sorted_colors = sorted(
                self.color_counts.items(),
                key=lambda item: item[1],
                reverse=True
            )
            
            print(f"[PaletteGen] Found {len(self.sorted_colors)} unique colors")
            print(f"[PaletteGen] Total non-white pixels: {self.total_pixels}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to analyze image: {e}")
    
    def rgb_to_hsv(self, rgb: Tuple[int, int, int]) -> Optional[Tuple[float, float, float]]:
        """
        Convert RGB color to HSV.
        
        Args:
            rgb: (r, g, b) tuple
        
        Returns:
            (h, s, v) tuple where h in [0, 360), s in [0, 1], v in [0, 1]
            Returns None if conversion fails
        """
        try:
            r, g, b = [x / 255.0 for x in rgb]
            
            cmax = max(r, g, b)
            cmin = min(r, g, b)
            delta = cmax - cmin
            
            # Hue
            if delta == 0:
                h = 0
            elif cmax == r:
                h = 60 * (((g - b) / delta) % 6)
            elif cmax == g:
                h = 60 * (((b - r) / delta) + 2)
            else:  # cmax == b
                h = 60 * (((r - g) / delta) + 4)
            
            # Saturation
            if cmax == 0:
                s = 0
            else:
                s = delta / cmax
            
            # Value
            v = cmax
            
            return (h, s, v)
        except:
            return None
    
    def group_colors_by_hue(self, num_bins: int = 16) -> Dict[int, List[Tuple[Tuple[int, int, int], int]]]:
        """
        Group colors by hue ranges.
        
        Args:
            num_bins: Number of hue bins (default 16)
        
        Returns:
            Dictionary mapping hue_bin -> list of (color, count) tuples
        """
        if not self.sorted_colors:
            self.analyze_image()
        
        groups = defaultdict(list)
        bin_size = 360.0 / num_bins
        
        for color, count in self.sorted_colors:
            hsv = self.rgb_to_hsv(color)
            if hsv:
                h = hsv[0]
                bin_index = int(h / bin_size) % num_bins
                groups[bin_index].append((color, count))
        
        return groups
    
    def get_palette(self, num_colors: int, algorithm: str = "frequency") -> Tuple[List[Tuple[int, int, int]], List[int], Dict[int, int]]:
        """
        Get the top N colors from the image using specified algorithm.
        
        Args:
            num_colors: Number of colors to return (1-256)
            algorithm: Selection algorithm ('frequency', 'dominant_shades', 'rare_shades')
        
        Returns:
            Tuple of:
            - List of (r, g, b) tuples for selected colors
            - List of pixel counts for each color
            - Dictionary of color_index -> pixel_count
        """
        self.algorithm = algorithm
        
        if not self.sorted_colors:
            self.analyze_image()
        
        # Apply algorithm
        if algorithm == "frequency":
            return self._get_by_frequency(num_colors)
        elif algorithm == "dominant_shades":
            return self._get_by_dominant_shades(num_colors)
        elif algorithm == "rare_shades":
            return self._get_by_rare_shades(num_colors)
        else:
            return self._get_by_frequency(num_colors)
    
    def _get_by_frequency(self, num_colors: int) -> Tuple[List[Tuple[int, int, int]], List[int], Dict[int, int]]:
        """
        Get top N colors by frequency (default algorithm).
        """
        # Clamp num_colors to available colors
        num_colors = min(num_colors, len(self.sorted_colors))
        
        # Get top N colors
        selected = self.sorted_colors[:num_colors]
        
        # Extract colors and counts
        colors = [color for color, count in selected]
        counts = [count for color, count in selected]
        color_map = {i: count for i, (color, count) in enumerate(selected)}
        
        return colors, counts, color_map
    
    def _get_by_dominant_shades(self, num_colors: int) -> Tuple[List[Tuple[int, int, int]], List[int], Dict[int, int]]:
        """
        Get top N colors by selecting the most dominant color from each hue group.
        Colors are sorted by frequency within each hue group.
        """
        # Group colors by hue
        hue_groups = self.group_colors_by_hue(num_bins=max(16, num_colors))
        
        # Sort each group by frequency and get the most dominant color
        selected_colors = []
        for bin_index in sorted(hue_groups.keys()):
            group = sorted(hue_groups[bin_index], key=lambda x: x[1], reverse=True)
            if group:
                selected_colors.append(group[0])  # Most dominant in this hue
        
        # Sort all selected colors by frequency to get top N
        selected_colors.sort(key=lambda x: x[1], reverse=True)
        selected_colors = selected_colors[:num_colors]
        
        # Extract colors and counts
        colors = [color for color, count in selected_colors]
        counts = [count for color, count in selected_colors]
        color_map = {i: count for i, (color, count) in enumerate(selected_colors)}
        
        return colors, counts, color_map
    
    def _get_by_rare_shades(self, num_colors: int) -> Tuple[List[Tuple[int, int, int]], List[int], Dict[int, int]]:
        """
        Get top N colors by selecting the least dominant color from each hue group.
        Colors are sorted by frequency within each hue group (ascending).
        """
        # Group colors by hue
        hue_groups = self.group_colors_by_hue(num_bins=max(16, num_colors))
        
        # Sort each group by frequency (ascending) and get the least dominant color
        selected_colors = []
        for bin_index in sorted(hue_groups.keys()):
            group = sorted(hue_groups[bin_index], key=lambda x: x[1])
            if group:
                selected_colors.append(group[0])  # Least dominant in this hue
        
        # Sort all selected colors by frequency to get top N (still least dominant overall)
        selected_colors.sort(key=lambda x: x[1])
        selected_colors = selected_colors[:num_colors]
        
        # Extract colors and counts
        colors = [color for color, count in selected_colors]
        counts = [count for color, count in selected_colors]
        color_map = {i: count for i, (color, count) in enumerate(selected_colors)}
        
        return colors, counts, color_map
    
    def find_ties(self, num_colors: int) -> Dict[int, List[Tuple[int, int, int]]]:
        """
        Find colors that are tied at the selection boundary.
        Only applicable to frequency-based algorithm.
        
        Args:
            num_colors: Number of colors being selected
        
        Returns:
            Dictionary mapping tie_index -> list of tied (r, g, b) colors
            tie_index is the position in the selection where the tie occurs
        """
        if not self.sorted_colors:
            self.analyze_image()
        
        # Ties only relevant for frequency-based algorithm
        if self.algorithm != "frequency":
            return {}
        
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