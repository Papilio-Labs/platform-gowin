-- VHDL Counter Module
-- Tests VHDL compilation and mixed-language instantiation

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity vhdl_counter is
    Generic (
        WIDTH : integer := 32
    );
    Port (
        clk   : in  STD_LOGIC;
        reset : in  STD_LOGIC;
        count : out STD_LOGIC_VECTOR(WIDTH-1 downto 0)
    );
end vhdl_counter;

architecture Behavioral of vhdl_counter is
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
