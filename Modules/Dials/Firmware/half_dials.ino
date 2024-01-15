/* Source: Adafruit's Seesaw Peripheral library. https://github.com/adafruit/Adafruit_seesawPeripheral/tree/main/examples

Modifications:

- Called Adafruit_seesawPeripheral_setIRQ() in setup() to fire the interrupt on first boot.
- Configured UART to use as a first boot flag only.
- Configured pins and I2C addresses for different modules.

Note: To program the modules you need a UPDI Programmer and to complie using megaTinyCore. 
See Adafruit Guide for reprogramming Seesaw with UPDI: https://learn.adafruit.com/adafruit-attiny817-seesaw/advanced-reprogramming-with-updi
*/

#define PRODUCT_CODE            1234
#define CONFIG_I2C_PERIPH_ADDR  0x70

#define CONFIG_INTERRUPT_PIN      1

// Pin to change I2C address on the module
#define CONFIG_ADDR_0_PIN          13
// Used only as a first boot signal by accessing this register and changing the baudrate from the controller side.
#define CONFIG_UART                1
#define CONFIG_UART_BUF_MAX       32
#define CONFIG_UART_SERCOM    Serial
// Other Seesaw features
#define CONFIG_ADC                 1
#define CONFIG_PWM                 1
#define CONFIG_NEOPIXEL            1
#define CONFIG_NEOPIXEL_BUF_MAX   (60*3) // 30 pixels == 180 bytes
// Encoders
#define CONFIG_ENCODER 1
#define CONFIG_NUM_ENCODERS 4
#define CONFIG_ENCODER0_A_PIN 7
#define CONFIG_ENCODER0_B_PIN 6
#define CONFIG_ENCODER1_A_PIN 4
#define CONFIG_ENCODER1_B_PIN 3
#define CONFIG_ENCODER2_A_PIN 14
#define CONFIG_ENCODER2_B_PIN 15
#define CONFIG_ENCODER3_A_PIN 10
#define CONFIG_ENCODER3_B_PIN 11


#include "Adafruit_seesawPeripheral.h"

void setup() { 

  Adafruit_seesawPeripheral_begin();

  // Trigger interrupt on first power up 
  Adafruit_seesawPeripheral_setIRQ();
}


void loop() {
  Adafruit_seesawPeripheral_run();
}
