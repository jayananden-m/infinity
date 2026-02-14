
import sys
from pathlib import Path

# sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from src.dp import SeamCarving

# Test with 3x3 energy map from earlier
energy = np.array([
    [1, 3, 1],
    [2, 1, 2],
    [1, 4, 1]
])

sc = SeamCarving(energy)
seam = sc.find_minimum_seam()
print(f"Seam: {seam}")