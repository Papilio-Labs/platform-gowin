"""
Gowin FPGA Platform for PlatformIO

Supports Gowin FPGA devices with the Gowin EDA toolchain.
Enables both pure FPGA projects and dual-target projects (MCU + FPGA).
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
        
        For dual-target boards (ESP32 + FPGA), we need both
        FPGA toolchain and ESP32 tools.
        """
        board = variables.get("board")
        board_config = self.board_config(board) if board else {}
        frameworks = variables.get("pioframework", [])
        upload_protocol = variables.get("upload_protocol", "")
        
        # Gowin toolchain is optional - user must install manually
        # or specify path via board_build.gowin_path
        
        # Configure based on framework
        if "arduino" in frameworks:
            # Dual-target board (e.g., Papilio RetroCade with ESP32 + FPGA)
            self.packages["framework-arduinoespressif32"]["optional"] = False

            # Enable ESP32 toolchains based on MCU type
            mcu = board_config.get("build.mcu", "").lower()
            if "esp32s3" in mcu or "esp32s2" in mcu:
                # ESP32-S3 and ESP32-S2 use Xtensa architecture
                if "toolchain-xtensa-esp32s3" in self.packages:
                    self.packages["toolchain-xtensa-esp32s3"]["optional"] = False
            elif "esp32c" in mcu or "esp32h" in mcu:
                # ESP32-C and ESP32-H series use RISC-V architecture
                if "toolchain-riscv32-esp" in self.packages:
                    self.packages["toolchain-riscv32-esp"]["optional"] = False
            else:
                # Default ESP32 (classic) uses Xtensa, but may need different toolchain
                # For now, enable S3 toolchain as it's backward compatible
                if "toolchain-xtensa-esp32s3" in self.packages:
                    self.packages["toolchain-xtensa-esp32s3"]["optional"] = False

            # ESP tools will be installed when needed
            if "tool-esptoolpy" in self.packages:
                self.packages["tool-esptoolpy"]["optional"] = False
            if "tool-openocd-esp32" in self.packages:
                self.packages["tool-openocd-esp32"]["optional"] = False

            self.frameworks["arduino"]["package"] = "framework-arduinoespressif32"
        
        # HDL and Verilog frameworks don't need additional packages
        # (they use the toolchain-gowin which is already required)
        
        # Configure upload tools based on environment or board default
        # pesptool is automatically downloaded on Windows when upload_protocol=pesptool
        # Other upload tools (openFPGALoader, Gowin Programmer) must be installed system-wide
        
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
        # Get build configuration (PlatformBoardConfig uses .get() method)
        build = board.get("build", {})
        
        # Set default FPGA project path if not specified
        if "fpga_project" not in build:
            build["fpga_project"] = "fpga/project.gprj"
        
        # Set default top module if not specified
        if "fpga_top_module" not in build:
            build["fpga_top_module"] = "top"
        
        return board

    def configure_debug_session(self, debug_config):
        """
        Configure debugging session.
        
        Note: FPGA debugging typically uses vendor tools (Gowin Analyzer)
        or external logic analyzers. This method is primarily for
        dual-target boards where the MCU can be debugged.
        """
        # For dual-target boards with ESP32, delegate to ESP32 debug config
        adapter = debug_config.get("tool")
        
        if adapter:
            # Configure based on debug adapter type
            if adapter.startswith("esp"):
                # Use ESP32 debug configuration
                debug_config.setdefault("server_ready_pattern", "Listening on port")
        
        return debug_config
