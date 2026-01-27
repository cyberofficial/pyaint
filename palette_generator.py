"""
Color Palette Generator Module

Analyzes images to extract color frequencies and generates GIMP-compatible CSS palettes.
"""

from collections import defaultdict
from typing import List, Tuple, Dict, Set, Optional
from PIL import Image
import math
import random
from concurrent.futures import ThreadPoolExecutor, as_completed


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
    
    def get_palette(self, num_colors: int, algorithm: str = "frequency", progress_callback=None) -> Tuple[List[Tuple[int, int, int]], List[int], Dict[int, int]]:
        """
        Get top N colors from image using specified algorithm.
        
        Args:
            num_colors: Number of colors to return (1-256)
            algorithm: Selection algorithm ('frequency', 'dominant_shades', 'rare_shades', 'kmeans')
            progress_callback: Optional callback function(progress_percent) for K-Means progress
        
        Returns:
            Tuple of:
            - List of (r, g, b) tuples for selected colors
            - List of pixel counts for each color
            - Dictionary of color_index -> pixel_count
        """
        self.algorithm = algorithm
        self.progress_callback = progress_callback
        
        if not self.sorted_colors:
            self.analyze_image()
        
        # Apply algorithm
        if algorithm == "frequency":
            return self._get_by_frequency(num_colors)
        elif algorithm == "dominant_shades":
            return self._get_by_dominant_shades(num_colors)
        elif algorithm == "rare_shades":
            return self._get_by_rare_shades(num_colors)
        elif algorithm == "kmeans":
            return self._get_by_kmeans(num_colors)
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
    
    def _get_by_kmeans(self, num_colors: int) -> Tuple[List[Tuple[int, int, int]], List[int], Dict[int, int]]:
        """
        Get palette using K-Means clustering algorithm (multi-threaded).
        
        This algorithm groups similar colors into clusters and calculates
        their averages (centroids), providing a more representative palette.
        
        Args:
            num_colors: Number of clusters (1-256)
        
        Returns:
            Tuple of:
            - List of (r, g, b) tuples for cluster centroids
            - List of pixel counts for each centroid
            - Dictionary of color_index -> pixel_count
        """
        # Clamp num_colors to available colors
        num_colors = min(num_colors, len(self.sorted_colors))
        
        if num_colors == 0:
            return [], [], {}
        
        print(f"[PaletteGen] Running K-Means with k={num_colors} (multi-threaded)")
        
        # Report progress
        if self.progress_callback:
            self.progress_callback(5)  # Starting initialization
        print(f"[PaletteGen] Progress: 5% - Starting initialization")
        
        # Prepare data: list of (color, count) for weighting
        data = []
        for color, count in self.sorted_colors:
            # Replicate colors based on count for weighted sampling
            # But limit to avoid memory issues with large images
            weight = min(count, 100)  # Cap weight at 100
            for _ in range(weight):
                data.append(color)
        
        # Report progress
        if self.progress_callback:
            self.progress_callback(10)  # Data prepared
        print(f"[PaletteGen] Progress: 10% - Data prepared and weighted sampling complete")
        
        # Initialize centroids using k-means++ initialization
        centroids = self._kmeans_plus_plus_init(data, num_colors)
        
        # Report progress
        if self.progress_callback:
            self.progress_callback(15)  # Centroids initialized
        print(f"[PaletteGen] Progress: 15% - Centroids initialized (K-Means++)")
        
        # Determine number of threads to use
        num_threads = min(4, max(1, num_colors))  # Use up to 4 threads
        
        # Run K-Means iterations
        self._current_centroids = centroids  # Store for thread access
        max_iterations = 20
        iteration_start_progress = 15
        iteration_end_progress = 90
        
        for iteration in range(max_iterations):
            # Calculate progress for this iteration
            iteration_progress = iteration_start_progress + (iteration / max_iterations) * (iteration_end_progress - iteration_start_progress)
            print(f"[PaletteGen] Progress: {int(iteration_progress)}% - Iteration {iteration + 1}/{max_iterations}")
            
            # Assign each point to nearest centroid (parallelized)
            clusters = [[] for _ in range(num_colors)]
            
            # Use ThreadPoolExecutor for parallel distance calculations
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                # Submit distance calculation tasks
                future_to_color = {
                    executor.submit(self._find_nearest_centroid, color, centroids): color
                    for color in data
                }
                
                # Collect results and update progress
                completed = 0
                total_tasks = len(future_to_color)
                for future in as_completed(future_to_color.keys()):
                    color = future_to_color[future]
                    nearest_idx = future.result()
                    clusters[nearest_idx].append(color)
                    completed += 1
                    
                    # Report incremental progress during assignment
                    if completed % (total_tasks // 10) == 0 or completed == total_tasks:
                        assign_progress = iteration_progress + (completed / total_tasks) * 0.3
                        if self.progress_callback:
                            self.progress_callback(int(assign_progress))
            
            # Calculate new centroids as average of assigned colors (parallelized)
            new_centroids = []
            
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                # Submit centroid calculation tasks
                future_to_cluster = {
                    executor.submit(self._calculate_weighted_average, cluster): cluster
                    for cluster in clusters
                }
                
                # Collect results in order
                for cluster in clusters:
                    if cluster:
                        future = list(future_to_cluster.keys())[clusters.index(cluster)]
                        new_centroids.append(future.result())
                    else:
                        # Empty cluster, keep old centroid or reinitialize
                        new_centroids.append(centroids[len(new_centroids)])
            
            # Check for convergence
            if self._centroids_converged(centroids, new_centroids):
                print(f"[PaletteGen] K-Means converged after {iteration + 1} iterations")
                centroids = new_centroids
                self._current_centroids = new_centroids
                break
            
            centroids = new_centroids
            self._current_centroids = new_centroids
            
            # Report progress after each iteration
            if self.progress_callback:
                self.progress_callback(int(iteration_progress))
        
        # Report progress - starting count calculation
        if self.progress_callback:
            self.progress_callback(92)
        print(f"[PaletteGen] Progress: 92% - Calculating counts for each centroid")
        
        # Calculate counts for each centroid (parallelized)
        counts = []
        
        # Submit count calculation tasks
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for centroid in centroids:
                centroid_idx = centroids.index(centroid)
                future = executor.submit(
                    self._count_colors_for_centroid,
                    centroid_idx
                )
                futures.append(future)
            
            # Collect results in order
            for future in futures:
                counts.append(future.result())
        
        # Report progress - sorting
        if self.progress_callback:
            self.progress_callback(95)
        print(f"[PaletteGen] Progress: 95% - Sorting centroids by cluster size")
        
        # Sort centroids by count (descending)
        sorted_indices = sorted(range(len(centroids)), key=lambda i: counts[i], reverse=True)
        sorted_centroids = [centroids[i] for i in sorted_indices]
        sorted_counts = [counts[i] for i in sorted_indices]
        
        # Convert to integer RGB values
        final_colors = [(int(r), int(g), int(b)) for r, g, b in sorted_centroids]
        
        # Report progress - finalizing
        if self.progress_callback:
            self.progress_callback(98)
        print(f"[PaletteGen] Progress: 98% - Converting to integer RGB values")
        
        color_map = {i: sorted_counts[i] for i in range(len(final_colors))}
        
        print(f"[PaletteGen] K-Means complete: {len(final_colors)} colors")
        
        # Report completion
        if self.progress_callback:
            self.progress_callback(100)
        print(f"[PaletteGen] Progress: 100% - Complete")
        
        return final_colors, sorted_counts, color_map
    
    def _kmeans_plus_plus_init(self, data: List[Tuple[int, int, int]], k: int) -> List[Tuple[float, float, float]]:
        """
        Initialize K-Means centroids using K-Means++ algorithm.
        
        This spreads initial centroids across the color space for better convergence.
        
        Args:
            data: List of color samples
            k: Number of centroids
        
        Returns:
            List of k centroid colors as (r, g, b) floats
        """
        centroids = []
        
        # Choose first centroid randomly
        first_idx = random.randint(0, len(data) - 1)
        centroids.append(tuple(float(x) for x in data[first_idx]))
        
        # Choose remaining centroids with probability proportional to distance squared
        for _ in range(1, k):
            distances = []
            for color in data:
                # Find minimum distance to any existing centroid
                min_dist = float('inf')
                for centroid in centroids:
                    dist = self._color_distance(color, centroid)
                    if dist < min_dist:
                        min_dist = dist
                distances.append(min_dist ** 2)
            
            # Choose new centroid based on weighted probability
            total_dist = sum(distances)
            if total_dist == 0:
                next_idx = random.randint(0, len(data) - 1)
            else:
                r = random.uniform(0, total_dist)
                cumulative = 0
                for i, d in enumerate(distances):
                    cumulative += d
                    if cumulative >= r:
                        next_idx = i
                        break
                else:
                    next_idx = len(data) - 1
            
            centroids.append(tuple(float(x) for x in data[next_idx]))
        
        return centroids
    
    def _find_nearest_centroid(self, color: Tuple[int, int, int], 
                            centroids: List[Tuple[float, float, float]]) -> int:
        """
        Find the index of the nearest centroid to a color.
        
        Args:
            color: RGB color tuple
            centroids: List of centroid colors
        
        Returns:
            Index of nearest centroid
        """
        min_dist = float('inf')
        nearest_idx = 0
        
        for i, centroid in enumerate(centroids):
            dist = self._color_distance(color, centroid)
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i
        
        return nearest_idx
    
    def _color_distance(self, color1: Tuple[int, int, int], 
                     color2: Tuple[float, float, float]) -> float:
        """
        Calculate Euclidean distance between two colors in RGB space.
        
        Args:
            color1: First color as (r, g, b) ints
            color2: Second color as (r, g, b) floats
        
        Returns:
            Euclidean distance
        """
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)
    
    def _calculate_weighted_average(self, colors: List[Tuple[int, int, int]]) -> Tuple[float, float, float]:
        """
        Calculate average color from a list of colors.
        
        Args:
            colors: List of RGB color tuples
        
        Returns:
            Average color as (r, g, b) floats
        """
        if not colors:
            return (128.0, 128.0, 128.0)  # Default to gray
        
        total_r = 0.0
        total_g = 0.0
        total_b = 0.0
        
        for r, g, b in colors:
            total_r += r
            total_g += g
            total_b += b
        
        n = len(colors)
        return (total_r / n, total_g / n, total_b / n)
    
    def _centroids_converged(self, old: List[Tuple[float, float, float]], 
                         new: List[Tuple[float, float, float]], 
                         threshold: float = 1.0) -> bool:
        """
        Check if centroids have converged (changed less than threshold).
        
        Args:
            old: Previous centroids
            new: New centroids
            threshold: Convergence threshold (default 1.0)
        
        Returns:
            True if converged, False otherwise
        """
        if len(old) != len(new):
            return False
        
        for old_c, new_c in zip(old, new):
            if self._color_distance(
                (int(old_c[0]), int(old_c[1]), int(old_c[2])),
                (int(new_c[0]), int(new_c[1]), int(new_c[2]))
            ) > threshold:
                return False
        
        return True
    
    def _count_colors_for_centroid(self, centroid_idx: int) -> int:
        """
        Count colors closest to a specific centroid.
        
        Args:
            centroid_idx: Index of the centroid in centroids list
        
        Returns:
            Total pixel count for colors closest to this centroid
        """
        total = 0
        for color, count in self.sorted_colors:
            if self._find_nearest_centroid(color, self._get_current_centroids()) == centroid_idx:
                total += count
        return total
    
    def _get_current_centroids(self) -> List[Tuple[float, float, float]]:
        """
        Get current centroids being used in K-Means iteration.
        
        Returns:
            List of current centroids
        """
        # This is a helper to access centroids from within iteration
        # In practice, centroids are passed as parameters, but we need
        # to store them temporarily for multi-threaded access
        if hasattr(self, '_current_centroids'):
            return self._current_centroids
        return []
    
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
