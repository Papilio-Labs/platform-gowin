/*
 * FPGA SPI Slave - Test Module for Papilio RetroCade
 * 
 * Simple SPI slave that echoes received data back to ESP32
 * and displays the data pattern on PMOD LEDs if connected.
 */

module fpga_spi_slave (
    // ESP32 SPI Interface
    input  wire       spi_cs,      // SPI Chip Select (active low)
    input  wire       spi_clk,     // SPI Clock
    input  wire       spi_mosi,    // Master Out Slave In
    output reg        spi_miso,    // Master In Slave Out
    
    // Test outputs (PMOD connector)
    output reg  [3:0] pmod_out     // Display data pattern
);

    reg [7:0] rx_data;
    reg [7:0] tx_data;
    reg [2:0] bit_counter;
    reg       spi_cs_prev;
    
    // SPI clock domain logic
    always @(posedge spi_clk or posedge spi_cs) begin
        if (spi_cs) begin
            // Reset when CS goes high
            bit_counter <= 0;
            spi_miso <= 1'b0;
        end else begin
            // Shift in MOSI bit, shift out MISO bit
            rx_data <= {rx_data[6:0], spi_mosi};
            spi_miso <= tx_data[7 - bit_counter];
            
            bit_counter <= bit_counter + 1;
        end
    end
    
    // Capture complete byte when CS goes high
    always @(posedge spi_cs) begin
        tx_data <= rx_data;  // Echo received data
        pmod_out <= rx_data[3:0];  // Display lower 4 bits
    end
    
    // Track CS edge for byte capture
    always @(posedge spi_clk) begin
        spi_cs_prev <= spi_cs;
    end

endmodule
