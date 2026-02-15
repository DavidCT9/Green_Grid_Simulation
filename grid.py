class Grid:
    def __init__(self, grid_max_export_limit: float, is_zero_export: bool, grid_max_import_limit: float):
        self._max_export_limit = grid_max_export_limit
        self._is_zero_export = is_zero_export
        self._import_limit = grid_max_import_limit
    def export(self, energy: float) -> float:
        if self._is_zero_export:
            return 0.0
        return min(energy, self._max_export_limit)
    def import_energy(self, energy: float) -> float:
        return min(energy, self._import_limit)
