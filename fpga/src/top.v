/**
 * Top-level Verilog module for Papilio RetroCade FPGA
 * 
 * This example implements:
 * - LED blinky pattern
 * - SPI slave interface for communication with ESP32-S3
 * - Simple register file for configuration
 * 
 * Target: Gowin GW5A-25A (Tang Primer 20K)
 */

module top (
    // System clock (27 MHz on Tang Primer 20K)
    input wire clk,
    
    // System reset (active low)
    input wire rst_n,
    
    // LED outputs
    output reg [5:0] led,
    
    // SPI slave interface
    input wire spi_clk,
    input wire spi_mosi,
    output reg spi_miso,
    input wire spi_cs_n,
    
    // Additional I/O (configure as needed)
    output wire [7:0] gpio_out
);

    // =========================================================================
    // Clock and Reset
    // =========================================================================
    
    wire sys_clk;
    wire sys_rst_n;
    
    // Use input clock directly (or instantiate PLL for different frequencies)
    assign sys_clk = clk;
    assign sys_rst_n = rst_n;
    
    // =========================================================================
    // LED Blinky Counter
    // =========================================================================
    
    reg [25:0] blink_counter;
    reg [5:0] led_pattern;
    reg led_mode; // 0 = auto blink, 1 = SPI controlled
    
    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n) begin
            blink_counter <= 26'd0;
            led_pattern <= 6'b000001;
        end else begin
            blink_counter <= blink_counter + 1'b1;
            
            // Update LED pattern every ~0.5 seconds (27MHz / 2^25 ≈ 0.8 Hz)
            if (blink_counter[24:0] == 25'd0) begin
                // Rotate pattern left
                led_pattern <= {led_pattern[4:0], led_pattern[5]};
            end
        end
    end
    
    // =========================================================================
    // SPI Slave Interface
    // =========================================================================
    
    // SPI registers
    reg [7:0] spi_rx_data;
    reg [7:0] spi_tx_data;
    reg [7:0] spi_cmd;
    reg [2:0] spi_bit_count;
    reg spi_active;
    
    // Register file
    reg [7:0] reg_id = 8'hA5;           // Device ID
    reg [7:0] reg_led_control = 8'h00;  // LED control register
    reg [7:0] reg_status = 8'h01;       // Status register
    
    // SPI command definitions (match ESP32 definitions)
    localparam CMD_NOP         = 8'h00;
    localparam CMD_READ_ID     = 8'h01;
    localparam CMD_WRITE_REG   = 8'h02;
    localparam CMD_READ_REG    = 8'h03;
    localparam CMD_LED_CONTROL = 8'h10;
    
    // Synchronize SPI signals to system clock
    reg [2:0] spi_cs_sync;
    reg [2:0] spi_clk_sync;
    
    always @(posedge sys_clk) begin
        spi_cs_sync <= {spi_cs_sync[1:0], spi_cs_n};
        spi_clk_sync <= {spi_clk_sync[1:0], spi_clk};
    end
    
    wire spi_cs_active = ~spi_cs_sync[2];
    wire spi_clk_rise = (spi_clk_sync[2:1] == 2'b01);
    wire spi_clk_fall = (spi_clk_sync[2:1] == 2'b10);
    
    // SPI state machine
    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n) begin
            spi_bit_count <= 3'd0;
            spi_rx_data <= 8'd0;
            spi_tx_data <= 8'd0;
            spi_cmd <= 8'd0;
            spi_active <= 1'b0;
        end else begin
            if (!spi_cs_active) begin
                // CS inactive - reset
                spi_bit_count <= 3'd0;
                spi_active <= 1'b0;
            end else begin
                spi_active <= 1'b1;
                
                if (spi_clk_rise) begin
                    // Sample MOSI on rising edge
                    spi_rx_data <= {spi_rx_data[6:0], spi_mosi};
                    spi_bit_count <= spi_bit_count + 1'b1;
                    
                    // After 8 bits, process command/data
                    if (spi_bit_count == 3'd7) begin
                        if (spi_cmd == 8'd0) begin
                            // First byte is command
                            spi_cmd <= {spi_rx_data[6:0], spi_mosi};
                            
                            // Prepare response based on command
                            case ({spi_rx_data[6:0], spi_mosi})
                                CMD_READ_ID: begin
                                    spi_tx_data <= reg_id;
                                end
                                CMD_LED_CONTROL: begin
                                    spi_tx_data <= reg_led_control;
                                end
                                default: begin
                                    spi_tx_data <= 8'h00;
                                end
                            endcase
                        end else begin
                            // Second byte is data
                            case (spi_cmd)
                                CMD_LED_CONTROL: begin
                                    reg_led_control <= {spi_rx_data[6:0], spi_mosi};
                                    led_mode <= 1'b1; // Switch to SPI control
                                end
                                CMD_WRITE_REG: begin
                                    // Could implement register writes here
                                end
                            endcase
                            
                            // Reset for next transaction
                            spi_cmd <= 8'd0;
                        end
                    end
                end
                
                if (spi_clk_fall) begin
                    // Update MISO on falling edge
                    spi_miso <= spi_tx_data[7];
                    spi_tx_data <= {spi_tx_data[6:0], 1'b0};
                end
            end
        end
    end
    
    // =========================================================================
    // LED Output Multiplexer
    // =========================================================================
    
    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n) begin
            led <= 6'b000000;
            led_mode <= 1'b0;
        end else begin
            if (led_mode) begin
                // SPI controlled
                led <= reg_led_control[5:0];
            end else begin
                // Auto blink pattern
                led <= led_pattern;
            end
        end
    end
    
    // =========================================================================
    // Additional GPIO (example)
    // =========================================================================
    
    assign gpio_out = {2'b00, led};
    
endmodule
