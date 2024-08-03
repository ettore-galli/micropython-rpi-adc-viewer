from machine import ADC, Pin, I2C  # type: ignore

import asyncio

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
        hardware_information: HardwareInformation = HardwareInformation(),
        adc_delay: float = 0.0001,
        frame_delay: float = 0.05,
    ):
        self.hardware_information = hardware_information

        self.adc_delay = adc_delay
        self.frame_delay = frame_delay

        self.adc = ADC(Pin(hardware_information.adc_gpio_pin))
        self.adc_value = 0

        self.frame_raw_values = []
        self.frame_read_event = asyncio.Event()

        self.display = self.display_setup(hardware_information=hardware_information)

        self.display_init(self.display)
        self.draw_init()

    def display_setup(
        self, hardware_information: HardwareInformation
    ) -> ssd1306.SSD1306_I2C:
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
        self.display.text("Val:", 5, 5, 1)
        self.display.rect(0, 0, 128, 64, 1)
        self.display.show()

    async def read_adc_values_for_frame(
        self, number_of_samples: int, sample_value_reader
    ):
        raw_adc_values = []
        for _ in range(number_of_samples):
            raw_adc_values.append(sample_value_reader())
            await asyncio.sleep(self.adc_delay)

        return raw_adc_values

    def clear_plot_area(self, frame_buffer, plot_information: PlotInformation):
        frame_buffer.fill_rect(
            plot_information.left_start,
            plot_information.bottom_line - (plot_information.pixels_top + 1),
            plot_information.pixels_per_screen,
            plot_information.pixels_top + 1,
            0,
        )

    def prepare_frame_buffer_pixels(
        self, plot_information: PlotInformation, raw_values
    ):
        def to_pixels(value):
            return int(value * plot_information.pixels_top / 65536)

        frame_buffer_pixels = []

        for position, value in enumerate(raw_values):
            value_in_pixels = to_pixels(value)
            left = plot_information.left_start + position
            frame_buffer_pixels.append(
                (left, plot_information.bottom_line - value_in_pixels, 1)
            )

        return frame_buffer_pixels

    def draw_points_on_screen(
        self, frame_buffer: ssd1306.SSD1306_I2C, frame_buffer_points
    ):
        for x, y, color in frame_buffer_points:
            frame_buffer.pixel(x, y, color)

        frame_buffer.show()

    async def read_and_draw_screen(
        self, frame_buffer, plot_information: PlotInformation, sample_value_reader
    ):

        raw_values = await self.read_adc_values_for_frame(
            number_of_samples=plot_information.pixels_per_screen,
            sample_value_reader=sample_value_reader,
        )

        await self.draw_screen(
            frame_buffer=frame_buffer,
            plot_information=plot_information,
            raw_values=raw_values,
        )

    async def draw_screen(
        self, frame_buffer, plot_information: PlotInformation, raw_values
    ):
        frame_buffer_points = self.prepare_frame_buffer_pixels(
            plot_information=plot_information, raw_values=raw_values
        )

        self.clear_plot_area(
            frame_buffer=frame_buffer,
            plot_information=plot_information,
        )

        self.draw_points_on_screen(
            frame_buffer=frame_buffer, frame_buffer_points=frame_buffer_points
        )

    async def single_screen_loop(self, frame_buffer, plot_information: PlotInformation):
        await self.read_and_draw_screen(
            frame_buffer=frame_buffer,
            plot_information=plot_information,
            sample_value_reader=self.adc.read_u16,
        )

    async def main_data_loop(self):

        plot_information = PlotInformation(self.hardware_information)

        asyncio.create_task(self.draw_screen_loop())

        while True:
            self.frame_raw_values = await self.read_adc_values_for_frame(
                number_of_samples=plot_information.pixels_per_screen,
                sample_value_reader=self.adc.read_u16,
            )
            self.frame_read_event.set()

    async def draw_screen_loop(self):
        plot_information = PlotInformation(self.hardware_information)
        frame_buffer = self.display
        while True:
            await self.frame_read_event.wait()
            await self.draw_screen(
                frame_buffer=frame_buffer,
                plot_information=plot_information,
                raw_values=self.frame_raw_values,
            )
            self.frame_read_event.clear()
            await asyncio.sleep(self.frame_delay)


if __name__ == "__main__":
    adcm = ADCMonitor()
    asyncio.run(adcm.main_data_loop())  #  type: ignore
