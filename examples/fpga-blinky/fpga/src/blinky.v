/**
 * Simple LED Blinky for Gowin FPGA
 * 
 * Pure FPGA project - no MCU code
 * Blinks LEDs in a rotating pattern on PMOD connector
 * 
 * Target: Papilio RetroCade (GW2AR-18)
 * 
 * NOTE: Clock must be provided by ESP32 on GPIO1.
 *       Connect LEDs to PMOD connector pins to see output.
 *       Assumes ~27 MHz clock from ESP32.
 */

module blinky (
    // System clock (provided by ESP32, typically ~27 MHz)
    input wire clk,
    
    // System reset (active low)
    input wire rst_n,
    
    // LED outputs
    output reg [5:0] led
);

    // Clock divider for visible blinking
    // 27 MHz / 2^25 ≈ 0.8 Hz
    reg [25:0] counter;
    
    // LED pattern
    reg [5:0] pattern;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= 26'd0;
            pattern <= 6'b000001;
            led <= 6'b000000;
        end else begin
            counter <= counter + 1'b1;
            
            // Update pattern every ~0.5 seconds
            if (counter[24:0] == 25'd0) begin
                // Rotate pattern left
                pattern <= {pattern[4:0], pattern[5]};
                led <= pattern;
            end
        end
    end

endmodule
