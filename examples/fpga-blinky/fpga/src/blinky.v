/**
 * Simple LED Blinky for Gowin FPGA
 * 
 * Pure FPGA project - no MCU code
 * Blinks LEDs in a rotating pattern
 * 
 * Target: Tang Primer 20K (GW5A-25A with 6 discrete LEDs)
 * 
 * NOTE: This design is for boards with discrete LEDs.
 *       Papilio RetroCade has only an RGB LED (WS2812) which
 *       requires different control logic. See 'papilio-blinky'
 *       example for RGB LED control.
 */

module blinky (
    // System clock (27 MHz on Tang Primer 20K)
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
