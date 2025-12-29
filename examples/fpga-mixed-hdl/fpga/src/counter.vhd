-- Simple VHDL counter module
-- Demonstrates mixed Verilog/VHDL design support in Gowin platform

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity counter is
    Generic (
        WIDTH : integer := 32
    );
    Port (
        clk   : in  STD_LOGIC;
        reset : in  STD_LOGIC;
        count : out STD_LOGIC_VECTOR(WIDTH-1 downto 0)
    );
end counter;

architecture Behavioral of counter is
    signal count_reg : unsigned(WIDTH-1 downto 0) := (others => '0');
begin
    process(clk, reset)
    begin
        if reset = '1' then
            count_reg <= (others => '0');
        elsif rising_edge(clk) then
            count_reg <= count_reg + 1;
        end if;
    end process;
    
    count <= std_logic_vector(count_reg);
end Behavioral;
