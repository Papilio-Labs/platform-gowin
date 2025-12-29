/**
 * Papilio RetroCade - Simple GPIO Pass-through Example
 * ESP32-S3 + Gowin FPGA
 * 
 * Simple test: ESP32 toggles GPIO1, FPGA passes it through to all PMOD pins.
 */

module top(
    input  wire       gpio1_in,      // Input from ESP32 GPIO1
    output wire [7:0] pmod_out       // Output to all 8 PMOD pins
);

    // Simple pass-through: all PMOD pins follow gpio1_in
    assign pmod_out = {8{gpio1_in}};

endmodule
