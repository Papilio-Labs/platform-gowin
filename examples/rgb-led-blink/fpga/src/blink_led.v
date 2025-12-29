module blink_led(
    input  wire clk,          // 27MHz clock from ESP32
    input  wire rst_n,        // Active low reset
    output wire led_out       // Output to WS2812B RGB LED
);

    // Instantiate the WS2812B LED controller
    ws2812b ws2812b_inst (
        .clk(clk),           // Connect to 27MHz clock
        .rst_n(rst_n),       // Connect reset
        .dout(led_out)       // Connect to LED output pin
    );

endmodule
