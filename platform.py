"""
Gowin FPGA Platform for PlatformIO

Supports Gowin FPGA devices with the Gowin EDA toolchain.
"""

from platformio.public import PlatformBase


class GowinPlatform(PlatformBase):
    """
    Gowin FPGA development platform.
    
    Supports multiple Gowin FPGA families:
    - GW1N (Nano series)
    - GW2A (Arora series)
    - GW5A (Arora V series)
    - GW5AST (Arora V with high-speed transceivers)
    """

    def configure_default_packages(self, variables, targets):
        """
        Configure default packages based on board and framework.
        
        Gowin toolchain is optional - user must install manually
        or specify path via GOWIN_HOME environment variable or
        board_build.gowin_path in platformio.ini.
        """
        # No additional package configuration needed for HDL framework
        return super().configure_default_packages(variables, targets)

    def is_embedded(self):
        """
        Return True if this is an embedded platform.
        FPGAs are considered embedded hardware.
        """
        return True

    def get_boards(self, id_=None):
        """
        Get board definitions.
        
        Args:
            id_: Optional board ID to get specific board
            
        Returns:
            Dict of board configurations or single board config
        """
        result = super().get_boards(id_)
        
        if not result:
            return result
            
        # Add FPGA-specific metadata to boards
        if id_:
            return self._add_fpga_metadata(result)
        else:
            for board_id, board_data in result.items():
                result[board_id] = self._add_fpga_metadata(board_data)
        
        return result

    def _add_fpga_metadata(self, board):
        """
        Add FPGA-specific metadata to board configuration.
        
        Args:
            board: PlatformBoardConfig object
            
        Returns:
            Updated board configuration
        """
        # Get build configuration
        build = board.get("build", {})
        
        # Set default FPGA project path if not specified
        if "fpga_project" not in build:
            build["fpga_project"] = "fpga/project.gprj"
        
        # Set default top module if not specified
        if "fpga_top_module" not in build:
            build["fpga_top_module"] = "top"
        
        return board
