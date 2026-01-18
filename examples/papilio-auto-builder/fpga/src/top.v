// Papilio Automatic Library Builder - FPGA Top Module Template
// 
// This file demonstrates marker-based code injection. The regions between
// PAPILIO_AUTO_*_BEGIN and PAPILIO_AUTO_*_END markers are auto-generated.
// User code outside markers is preserved during regeneration.
//
// To disable auto-generation for a section, simply remove its markers.

module top (
    input  wire clk_27mhz,      // 27 MHz system clock
    input  wire rst_n,          // Active-low reset
    
    // SPI Interface (directly wired to ESP32)
    input  wire spi_sclk,
    input  wire spi_mosi,
    output wire spi_miso,
    input  wire spi_cs_n,
    
    // User I/O (directly controlled)
    output wire [7:0] led
    
    //# PAPILIO_AUTO_PORTS_BEGIN
    // Auto-generated port declarations will appear here
    //# PAPILIO_AUTO_PORTS_END
);

    // =========================================================================
    // Clock and Reset
    // =========================================================================
    wire clk = clk_27mhz;
    wire rst = ~rst_n;
    
    // =========================================================================
    // Wishbone Bus Signals
    // =========================================================================
    wire [15:0] wb_adr;        // Address bus
    wire [7:0]  wb_dat_m2s;    // Data from master to slave
    wire [7:0]  wb_dat_s2m;    // Data from slave to master
    wire        wb_we;         // Write enable
    wire        wb_cyc;        // Bus cycle active
    wire        wb_stb;        // Strobe (valid transfer)
    wire        wb_ack;        // Acknowledge
    
    //# PAPILIO_AUTO_WIRES_BEGIN
// Auto-generated wire declarations

// papilio_spi_slave signals
wire [7:0] papilio_spi_slave_wb_dat_s2m;
wire        papilio_spi_slave_wb_ack;

// papilio_wb_register signals
wire [7:0] papilio_wb_register_wb_dat_s2m;
wire        papilio_wb_register_wb_ack;
wire        papilio_wb_register_wb_sel;
wire        papilio_wb_register_wb_stb;

// papilio_wishbone_rgb_led signals
wire [7:0] papilio_wishbone_rgb_led_wb_dat_s2m;
wire        papilio_wishbone_rgb_led_wb_ack;
wire        papilio_wishbone_rgb_led_wb_sel;
wire        papilio_wishbone_rgb_led_wb_stb;
//# PAPILIO_AUTO_WIRES_END
    
    // =========================================================================
    // SPI to Wishbone Bridge (Master)
    // =========================================================================
    //# PAPILIO_AUTO_MODULE_INST_BEGIN
// Auto-generated module instantiations

// SPI to Wishbone Bridge
simple_spi_wb_bridge papilio_spi_slave_inst (
    .clk(clk),
    .rst(rst),
    // SPI Interface
    .spi_sclk(spi_sclk),
    .spi_mosi(spi_mosi),
    .spi_miso(spi_miso),
    .spi_cs_n(spi_cs_n),
    // Wishbone Master Interface
    .wb_adr_o(wb_adr),
    .wb_dat_o(wb_dat_m2s),
    .wb_dat_i(wb_dat_s2m),
    .wb_we_o(wb_we),
    .wb_cyc_o(wb_cyc),
    .wb_stb_o(wb_stb),
    .wb_ack_i(wb_ack)
);

// Wishbone Register Block
wb_register_block #(
    .ADDR_WIDTH(4),
    .DATA_WIDTH(8),
    .RESET_VALUE(0)
) papilio_wb_register_inst (
    .clk(clk),
    .rst(rst),
    .wb_adr_i(wb_adr[3:0]),
    .wb_dat_i(wb_dat_m2s[7:0]),
    .wb_dat_o(papilio_wb_register_wb_dat_s2m[7:0]),
    .wb_we_i(wb_we),
    .wb_cyc_i(wb_cyc),
    .wb_stb_i(papilio_wb_register_wb_stb),
    .wb_ack_o(papilio_wb_register_wb_ack)
);

    wb_simple_rgb_led rgb_led_inst (
        .clk(clk),
        .rst(rst),
        .wb_adr_i(wb_adr[7:0]),
        .wb_dat_i(wb_dat_m2s[7:0]),
        .wb_dat_o(papilio_wishbone_rgb_led_wb_dat_s2m),
        .wb_we_i(wb_we),
        .wb_cyc_i(wb_cyc),
        .wb_stb_i(papilio_wishbone_rgb_led_wb_stb),
        .wb_ack_o(papilio_wishbone_rgb_led_wb_ack),
        .led_out(led_out)
    );
//# PAPILIO_AUTO_MODULE_INST_END
    
    // =========================================================================
    // Wishbone Interconnect (Address Decode + Mux)
    // =========================================================================
    //# PAPILIO_AUTO_WISHBONE_BEGIN
// Auto-generated Wishbone interconnect

// Address decode
assign papilio_wb_register_wb_sel = (wb_adr >= 16'h1000) && (wb_adr <= 16'h10FF);
assign papilio_wishbone_rgb_led_wb_sel = (wb_adr >= 16'h2000) && (wb_adr <= 16'h20FF);

// Strobe gating
assign papilio_wb_register_wb_stb = wb_stb && papilio_wb_register_wb_sel;
assign papilio_wishbone_rgb_led_wb_stb = wb_stb && papilio_wishbone_rgb_led_wb_sel;

// Data multiplexer
assign wb_dat_s2m = 
    (papilio_wb_register_wb_sel ? papilio_wb_register_wb_dat_s2m : 32'h0) |
    (papilio_wishbone_rgb_led_wb_sel ? papilio_wishbone_rgb_led_wb_dat_s2m : 32'h0);

// ACK multiplexer
assign wb_ack = 
    (papilio_wb_register_wb_sel ? papilio_wb_register_wb_ack : 1'b0) |
    (papilio_wishbone_rgb_led_wb_sel ? papilio_wishbone_rgb_led_wb_ack : 1'b0);
//# PAPILIO_AUTO_WISHBONE_END
    
    // =========================================================================
    // User Logic - NOT auto-generated, preserved during regeneration
    // =========================================================================
    
    // Example: Drive LEDs from register values
    // (This section is preserved when markers are regenerated)
    assign led = 8'hAA;  // Placeholder - user can modify
    
endmodule
