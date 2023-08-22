from machine import ADC, Pin, I2C

import uasyncio as asyncio

from ssd1306_official import ssd1306


class HardwareInformation:
    adc_gpio_pin = 26
    display_i2c_peripherial_id = 1  # 0
    display_sda_gpio_pin = 2  # 16
    display_scl_gpio_pin = 3  # 17
    display_width = 128
    display_height = 64


class PlotInformation:
    def __init__(self, hardware_information: HardwareInformation) -> None:
        self.left_start = 5
        self.bottom_line = 62
        self.pixels_top = 40
        self.pixels_per_screen = (
            hardware_information.display_width - 2 * self.left_start
        )


class ADCMonitor:
    def __init__(
        self,
        adc_value_logger,
        hardware_information: HardwareInformation = HardwareInformation(),
        adc_delay_ms: int = 1,
    ):
        self.adc_value_logger = adc_value_logger
        self.hardware_information = hardware_information

        self.adc_delay_ms = adc_delay_ms
        self.adc = ADC(Pin(hardware_information.adc_gpio_pin))
        self.adc_value = 0

        self.display = self.display_setup(hardware_information=hardware_information)

        self.display_init(self.display)
        self.draw_init()

    def display_setup(self, hardware_information: HardwareInformation):
        i2c = I2C(
            hardware_information.display_i2c_peripherial_id,
            sda=Pin(hardware_information.display_sda_gpio_pin),
            scl=Pin(hardware_information.display_scl_gpio_pin),
            freq=400_000,
        )
        display = ssd1306.SSD1306_I2C(
            hardware_information.display_width, hardware_information.display_height, i2c
        )

        return display

    def display_init(self, display):
        display.contrast(255)
        display.invert(0)

    def set_adc_value(self, adc_value: float):
        self.adc_value = adc_value

    def get_adc_value(self):
        return self.adc_value

    def draw_init(self):
        self.display.text("Value", 5, 5, 1)
        self.display.rect(0, 0, 128, 64, 1)
        self.display.show()

    def clear_plot_area(self, frame_buffer, plot_information: PlotInformation):
        frame_buffer.fill_rect(
            plot_information.left_start,
            plot_information.bottom_line - (plot_information.pixels_top + 1),
            plot_information.pixels_per_screen,
            plot_information.pixels_top + 1,
            0,
        )

    async def read_and_draw_screen(
        self, frame_buffer, plot_information: PlotInformation, sample_value_reader
    ):
        def to_pixels(value):
            return int(value * plot_information.pixels_top / 65536)

        for position in range(plot_information.pixels_per_screen):
            value = sample_value_reader()
            value_in_pixels = to_pixels(value)
            left = plot_information.left_start + position
            frame_buffer.pixel(left, plot_information.bottom_line - value_in_pixels, 1)
            await asyncio.sleep_ms(self.adc_delay_ms)

        frame_buffer.show()

    async def single_screen_loop(self, frame_buffer, plot_information: PlotInformation):
        self.clear_plot_area(
            frame_buffer=frame_buffer,
            plot_information=plot_information,
        )

        await self.read_and_draw_screen(
            frame_buffer=frame_buffer,
            plot_information=plot_information,
            sample_value_reader=self.adc.read_u16,
        )

        self.display.show()

    async def screen_loop(self):
        plot_information = PlotInformation(self.hardware_information)
        frame_buffer = self.display

        while True:
            await self.single_screen_loop(
                frame_buffer=frame_buffer,
                plot_information=plot_information,
            )


def render_value(value: float, top: float, stars: int):
    return int(1.0 * stars * value / top)


def log_adc_value(value: float):
    ruler = ". . . . : . . . . 1 . . . . : . . . . 2 . . . . : . . . . 3 . . ."
    n = render_value(value, 65535, len(ruler))
    rendered = ("[" + ruler[:n] + "]" if value > 0 else "--") + str(value)
    print(rendered)


async def main(coroutines):
    tasks = [
        asyncio.create_task(coro()) for coro in coroutines  # pylint: disable=E1101
    ]
    for task in tasks:
        await task


if __name__ == "__main__":
    adcm = ADCMonitor(adc_value_logger=log_adc_value)
    asyncio.run(main([adcm.screen_loop]))  #  type: ignore
