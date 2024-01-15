/* Source: Adafruit's Seesaw Peripheral library. https://github.com/adafruit/Adafruit_seesawPeripheral/tree/main/examples

Modifications:

- Called Adafruit_seesawPeripheral_setIRQ() in setup() to fire the interrupt on first boot.
- Configured UART to use as a first boot flag only.
- Configured pins and I2C addresses for different modules.

Note: To program the modules you need a UPDI Programmer and to complie using megaTinyCore. 
See Adafruit Guide for reprogramming Seesaw with UPDI: https://learn.adafruit.com/adafruit-attiny817-seesaw/advanced-reprogramming-with-updi
*/

#define PRODUCT_CODE            1234
#define CONFIG_I2C_PERIPH_ADDR  0x60

#define CONFIG_INTERRUPT_PIN      1

// Pins to change I2C address on the module
#define CONFIG_ADDR_0_PIN          10
#define CONFIG_ADDR_1_PIN          11                                                                                                
#define CONFIG_ADDR_2_PIN          12
#define CONFIG_ADDR_3_PIN          13
// Used only as a first boot signal by accessing this register and changing the baudrate from the controller side.
#define CONFIG_UART                1
#define CONFIG_UART_BUF_MAX       32
#define CONFIG_UART_SERCOM    Serial
// Other Seesaw features
#define CONFIG_ADC                 1
#define CONFIG_PWM                 1
#define CONFIG_NEOPIXEL            1
#define CONFIG_NEOPIXEL_BUF_MAX   (60*3) // 30 pixels == 180 bytes


#include "Adafruit_seesawPeripheral.h"

void setup() { 

  Adafruit_seesawPeripheral_begin();

  // Trigger interrupt on first power up 
  Adafruit_seesawPeripheral_setIRQ();
}


void loop() {
  Adafruit_seesawPeripheral_run();
}

