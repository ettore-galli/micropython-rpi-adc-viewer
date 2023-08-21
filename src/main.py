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


class ADCMonitor:
    def __init__(
        self,
        adc_value_logger,
        hardware_information: HardwareInformation = HardwareInformation(),
        adc_delay_seconds: float = 0.0001,
        refresh_delay_seconds: float = 0.0001,
    ):
        self.adc_value_logger = adc_value_logger
        self.hardware_information = hardware_information

        self.adc_delay_seconds = adc_delay_seconds
        self.adc = ADC(Pin(hardware_information.adc_gpio_pin))
        self.adc_value = 0

        self.refresh_delay_seconds = refresh_delay_seconds
        self.display = self.display_setup(hardware_information=hardware_information)

        self.display_init(self.display)
        self.draw_init()

        self.last_displayed_value: float = 0

        self.pixels_num = 100
        self.pixels = [0] * self.pixels_num
        self.pixels_index = 0

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
        self.display.show()
        print(self.display.buffer)

    def display_value(self):
        value = self.get_adc_value()
        rect_height = 60
        rect_left = 5
        rect_top = 25
        pixels_top = 120

        def to_pixels(value):
            return int(value * pixels_top / 65536)

        display_pixels = to_pixels(value)

        self.display.fill_rect(rect_left, rect_top, display_pixels, rect_height, 1)
        self.display.fill_rect(
            rect_left + display_pixels,
            rect_top,
            self.hardware_information.display_width - (rect_left + display_pixels),
            rect_height,
            0,
        )

        self.display.show()

        self.displayed_value = value

    def draw_wave_pixel_to_framebuffer(self, frame_buffer, value):
        left_start = 5
        bottom_line = 62

        pixels_top = 40

        def to_pixels(value):
            return int(value * pixels_top / 65536)

        display_pixels = to_pixels(value)

        left = left_start + self.pixels_index

        frame_buffer.pixel(left, bottom_line - self.pixels[self.pixels_index], 0)
        frame_buffer.pixel(left, bottom_line - display_pixels, 1)

        return display_pixels

    def display_wave(self):
        value = self.get_adc_value()

        display_pixels = self.draw_wave_pixel_to_framebuffer(frame_buffer=self.display, value=value)
        self.display.show()

        self.pixels[self.pixels_index] = display_pixels
        self.pixels_index = (self.pixels_index + 1) % self.pixels_num

        self.displayed_value = value
        print(self.display.buffer)

    async def adc_loop(self):
        while True:
            value = self.adc.read_u16()
            self.set_adc_value(value)

            await asyncio.sleep(self.adc_delay_seconds)

    async def display_change_loop(self):
        while True:
            adc_value = self.get_adc_value()
            # self.adc_value_logger(adc_value)
            self.display_wave()
            await asyncio.sleep(self.refresh_delay_seconds)


def render_value(value: float, top: float, stars: int):
    return int(1.0 * stars * value / top)


def log_adc_value(value: float):
    ruler = ". . . . : . . . . 1 . . . . : . . . . 2 . . . . : . . . . 3 . . ."
    n = render_value(value, 65535, len(ruler))
    rendered = ("[" + ruler[:n] + "]" if value > 0 else "--") + str(value)
    print(rendered)


async def main(coroutines):
    tasks = [
        asyncio.create_task(coro()) for coro in coroutines  # pylint: disable=E1101 #
    ]
    for task in tasks:
        await task


if __name__ == "__main__":
    adcm = ADCMonitor(adc_value_logger=log_adc_value)

    asyncio.run(main([adcm.display_change_loop, adcm.adc_loop]))  #  type: ignore
