import numpy as np

class SeamCarving:
    def __init__(self, energy_map):
        self.energy_map = energy_map
        self.height, self.width = np.size(energy_map, 0), np.size(energy_map, 1)

    def find_minimum_seam(self):
        """
            return: list of column indices per row (top to bottom)
        """
        # Build DP table and backtrack table
        dp_table = np.zeros((self.height, self.width))
        col_table = np.zeros((self.height, self.width))

        # Initialize the tables
        dp_table[0] = self.energy_map[0]
        col_table[0] = -1

        # Find minimum in last row and backtrack
        for row in range(1, self.height):
            for col in range(self.width):
                neighbors = []
                neighbor_cols = []
                
                # Check left neighbor
                if col > 0:
                    neighbors.append(dp_table[row-1][col-1])
                    neighbor_cols.append(col-1)
                
                # Check straight neighbor
                neighbors.append(dp_table[row-1][col])
                neighbor_cols.append(col)
                
                # Check right neighbor
                if col < self.width - 1:
                    neighbors.append(dp_table[row-1][col+1])
                    neighbor_cols.append(col+1)
                
                # Find which neighbor was minimum
                min_index = np.argmin(neighbors)
                min_col = neighbor_cols[min_index]
                min_value = neighbors[min_index]
                
                # Update tables
                current_value = self.energy_map[row][col]
                dp_table[row][col] = min_value + current_value
                col_table[row][col] = min_col
        
        # Backtracking the minium value from last row
        seam = []

        last_row = self.height - 1
        min_col = np.argmin(dp_table[last_row])

        current_col = int(min_col)
        for row in range(self.height - 1, -1, -1):
            seam.append(current_col)
            current_col = int(col_table[row][current_col])
        
        seam.reverse()
        return seam

        