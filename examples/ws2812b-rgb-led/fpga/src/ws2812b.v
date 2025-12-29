/*
 * WS2812B RGB LED Controller
 * 
 * Drives a WS2812B addressable RGB LED with precise timing.
 * Designed for 27MHz clock from ESP32.
 * 
 * The LED cycles through green color patterns on the Papilio RetroCade board.
 */

module ws2812b(
    input wire clk,           // Input clock (27MHz from ESP32)
    input wire rst_n,         // Active low reset
    output reg dout           // Data output to WS2812B
);

    // Parameters for WS2812B timing (for 27MHz clock)
    // WS2812B requires precise timing:
    // - T0H: 0.35us ±150ns (0 bit high time)
    // - T0L: 0.8us  ±150ns (0 bit low time)
    // - T1H: 0.7us  ±150ns (1 bit high time)
    // - T1L: 0.6us  ±600ns (1 bit low time)
    // - RES: >50us (reset/latch time)
    
    parameter T0H = 9;       // 0.33us (9 cycles @ 27MHz)
    parameter T0L = 22;      // 0.81us (22 cycles @ 27MHz)
    parameter T1H = 19;      // 0.70us (19 cycles @ 27MHz)
    parameter T1L = 16;      // 0.59us (16 cycles @ 27MHz)
    parameter RES = 1350;    // 50us reset time (1350 cycles @ 27MHz)

    // RGB Color definitions (GRB order for WS2812B)
    // Format: [23:16]=Green, [15:8]=Red, [7:0]=Blue
    // Using low brightness values for comfortable viewing
    parameter [23:0] GREEN_COLOR  = 24'h050000; // Dim green
    parameter [23:0] PURPLE_COLOR = 24'h000505; // Dim purple

    // State machine states
    reg [1:0] state;
    localparam IDLE  = 2'b00;
    localparam SEND  = 2'b01;
    localparam RESET = 2'b10;

    // Counters and registers
    reg [9:0] bit_counter;    // Counts bits being sent (24 bits total)
    reg [9:0] cycle_counter;  // Counts clock cycles for timing
    reg [23:0] led_data;      // Data to send to LED

    // Main state machine
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            dout <= 0;
            bit_counter <= 0;
            cycle_counter <= 0;
            led_data <= GREEN_COLOR;
        end else begin
            case (state)
                IDLE: begin
                    dout <= 0;
                    bit_counter <= 23;  // Start with MSB
                    cycle_counter <= 0;
                    state <= SEND;
                end

                SEND: begin
                    // Generate WS2812B timing pattern
                    if (cycle_counter == 0) begin
                        dout <= 1;  // Start of bit (always high)
                    end else if (led_data[bit_counter] == 1'b1 && cycle_counter == T1H) begin
                        dout <= 0;  // End of '1' bit
                    end else if (led_data[bit_counter] == 1'b0 && cycle_counter == T0H) begin
                        dout <= 0;  // End of '0' bit
                    end

                    // Move to next bit or reset state
                    if ((led_data[bit_counter] == 1'b1 && cycle_counter == (T1H + T1L - 1)) ||
                        (led_data[bit_counter] == 1'b0 && cycle_counter == (T0H + T0L - 1))) begin
                        cycle_counter <= 0;
                        if (bit_counter == 0) begin
                            state <= RESET;
                        end else begin
                            bit_counter <= bit_counter - 1;
                        end
                    end else begin
                        cycle_counter <= cycle_counter + 1;
                    end
                end

                RESET: begin
                    // Hold low for >50us to latch the data
                    dout <= 0;
                    if (cycle_counter == RES - 1) begin
                        state <= IDLE;
                        cycle_counter <= 0;
                    end else begin
                        cycle_counter <= cycle_counter + 1;
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
