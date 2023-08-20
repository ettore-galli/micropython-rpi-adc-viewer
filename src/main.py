from machine import ADC, Pin, PWM


import uasyncio as asyncio


class HardwareInformation:
    adc_gpio_pin = 26
    display_sda_gpio_pin = 16
    display_scl_gpio_pin = 17


class ADCMonitor:
    def __init__(
        self,
        pwm_value_logger,
        adc_delay_seconds: float = 0.05,
        hardware_information: HardwareInformation = HardwareInformation(),
        refresh_delay_seconds: float = 0.01,
    ):
        self.pwm_value_logger = pwm_value_logger
        self.adc_delay_seconds = adc_delay_seconds
        self.adc = ADC(Pin(hardware_information.adc_gpio_pin))

        self.refresh_delay_seconds = refresh_delay_seconds
        self.adc_value = 0

    def adc_to_pwm(self, adc: float, zero_threshold: float = 127):
        adc_top = 65535
        pwm_top = 65535
        pwm = (
            int(((adc - zero_threshold) / (adc_top - zero_threshold)) * pwm_top)
            if adc > zero_threshold
            else 0
        )

        return pwm

    def set_adc_value(self, adc_value: float):
        self.adc_value = adc_value

    def get_adc_value(self):
        return self.adc_value

    async def adc_loop(self):
        while True:
            value = self.adc.read_u16()
            self.set_adc_value(self.adc_to_pwm(value))

            await asyncio.sleep(self.adc_delay_seconds)

    async def display_change_loop(self):
        while True:
            adc_value = self.get_adc_value()
            self.pwm_value_logger(adc_value)
            await asyncio.sleep(self.refresh_delay_seconds)


def render_value(value: float, top: float, stars: int):
    return int(1.0 * stars * value / top)


def display_adc(value: float):
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
    adcm = ADCMonitor(pwm_value_logger=display_adc)

    asyncio.run(main([adcm.display_change_loop, adcm.adc_loop]))  #  type: ignore
