/**
 * Simple FPGA Top Module
 *
 * This is a minimal example that demonstrates the FPGA portion of
 * the custom ESP32+FPGA board.
 */

module top (
    input wire clk,           // System clock
    input wire rst_n,         // Active-low reset
    output wire [2:0] led_rgb // RGB LED outputs
);

    // Simple counter to blink LED
    reg [25:0] counter;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= 26'h0;
        end else begin
            counter <= counter + 1'b1;
        end
    end

    // Drive RGB LED with counter bits
    assign led_rgb[0] = counter[23]; // Red
    assign led_rgb[1] = counter[24]; // Green
    assign led_rgb[2] = counter[25]; // Blue

endmodule
