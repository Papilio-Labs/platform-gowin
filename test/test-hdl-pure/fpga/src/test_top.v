/**
 * Test Top Module - Verilog
 * 
 * Simple test design that uses both Verilog and VHDL components
 * to verify mixed-language support.
 */

module test_top (
    input wire clk,
    input wire rst_n,
    output wire [3:0] pmod_out
);

    // Internal signals
    wire [31:0] counter_val;
    
    // Instantiate VHDL counter component
    vhdl_counter #(
        .WIDTH(32)
    ) counter_inst (
        .clk(clk),
        .reset(~rst_n),  // VHDL uses active high reset
        .count(counter_val)
    );
    
    // Output MSBs to PMOD pins
    assign pmod_out = counter_val[27:24];

endmodule
