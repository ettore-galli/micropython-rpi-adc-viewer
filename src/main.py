import time
from machine import ADC, Pin, PWM

import uasyncio as asyncio


class PWMLed:
    def __init__(
        self,
        pwm_value_logger,
        adc_delay_seconds: float = 0.05,
        adc_pin: int = 26,
        pwm_pin=0,
        pwm_delay_seconds=0.01,
    ):
        self.adc = ADC(Pin(adc_pin))
        self.pwm_pin = pwm_pin
        self.adc_delay_seconds = adc_delay_seconds
        self.pwm_value_logger = pwm_value_logger
        self.init_pwm()
        self.pwm_delay_seconds = pwm_delay_seconds
        self.pwm_duty = 0

    def init_pwm(self):
        pwm0 = PWM(Pin(self.pwm_pin))
        pwm0.freq(1000)
        pwm0.duty_u16(0)
        self.pwm0 = pwm0

    def adc_to_pwm(self, adc, zero_threshold=127):
        adc_top = 65535
        pwm_top = 65535
        pwm = (
            int(((adc - zero_threshold) / (adc_top - zero_threshold)) * pwm_top)
            if adc > zero_threshold
            else 0
        )

        return pwm

    def update_pwm_duty(self, duty):
        self.pwm_duty = duty

    def get_pwm_duty(self):
        return self.pwm_duty

    async def adc_loop(self):
        while True:
            value = self.adc.read_u16()
            self.update_pwm_duty(self.adc_to_pwm(value))

            await asyncio.sleep(self.adc_delay_seconds)

    async def pwm_change_loop(self):
        while True:
            duty = self.get_pwm_duty()
            self.pwm0.duty_u16(duty)
            self.pwm_value_logger(duty)
            await asyncio.sleep(self.pwm_delay_seconds)


def render_value(value, top, stars):
    return int(1.0 * stars * value / top)


def display_adc(value):
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
    adcm = PWMLed(pwm_value_logger=display_adc)

    asyncio.run(main([adcm.pwm_change_loop, adcm.adc_loop]))
