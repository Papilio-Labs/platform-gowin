/**
 * Simple FPGA Blinky with SPI Interface
 *
 * Features:
 * - LED blinker with adjustable speed
 * - SPI slave interface for ESP32 communication
 * - Demonstrates dual-target (ESP32 + FPGA) design
 */

module top (
    input  wire clk,        // 27 MHz clock input
    input  wire rst_n,      // Active-low reset from ESP32

    // SPI interface from ESP32
    input  wire spi_cs,     // SPI chip select (active low)
    input  wire spi_sck,    // SPI clock
    input  wire spi_mosi,   // SPI data from ESP32
    output wire spi_miso,   // SPI data to ESP32

    // LED outputs
    output reg [7:0] leds   // 8 LEDs for blinky pattern
);

    // Clock divider for LED blink rate
    reg [25:0] counter;
    reg [7:0] blink_pattern;

    // SPI receiver
    reg [7:0] spi_data_rx;
    reg [2:0] spi_bit_counter;
    reg [15:0] esp32_counter;  // Counter value from ESP32

    // LED blinker
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= 26'd0;
            blink_pattern <= 8'b00000001;
        end else begin
            counter <= counter + 1;

            // Update LED pattern every ~0.5 seconds (27MHz / 2^25 ≈ 1.6 Hz)
            if (counter == 26'd0) begin
                // Rotate pattern left
                blink_pattern <= {blink_pattern[6:0], blink_pattern[7]};
            end
        end
    end

    // Simple SPI slave receiver
    always @(posedge spi_sck or negedge rst_n) begin
        if (!rst_n) begin
            spi_bit_counter <= 3'd0;
            spi_data_rx <= 8'd0;
            esp32_counter <= 16'd0;
        end else if (!spi_cs) begin  // SPI active when CS is low
            spi_data_rx <= {spi_data_rx[6:0], spi_mosi};
            spi_bit_counter <= spi_bit_counter + 1;

            // After receiving 8 bits
            if (spi_bit_counter == 3'd7) begin
                // Store received byte (simplified protocol)
                // In a real design, you'd decode commands properly
                if (spi_data_rx[7:4] != 4'd0) begin
                    esp32_counter <= {esp32_counter[7:0], spi_data_rx};
                end
            end
        end else begin
            spi_bit_counter <= 3'd0;
        end
    end

    // Output LED pattern
    always @(*) begin
        leds = blink_pattern;
    end

    // SPI MISO (for future use - send data back to ESP32)
    assign spi_miso = 1'b0;  // Not used in this simple example

endmodule
