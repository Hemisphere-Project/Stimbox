/*
   SETTINGS
*/
#define CR_VERSION  0.01  // Init

#include <Arduino.h>
#include "debug.h"
#include "img_crnl.h"

#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include "Adafruit_SSD1306.h"

#define SCREEN_WIDTH 64 // OLED display width, in pixels
#define SCREEN_HEIGHT 48 // OLED display height, in pixels
#define oled2_RESET     -1 // Reset pin # (or -1 if sharing Arduino reset pin)
Adafruit_SSD1306 display(0);

#define BTN_GO 27

// BTNS CLBCK
//
void ICACHE_RAM_ATTR go() {
  event_trigger(BTN_GO, [](){ 
    Serial.println("GO");
  });
}


// SETUP
//
void setup(void) {
  LOGSETUP();
  LOG("hello");

  // Settings config
  String keys[16] = {"id", "model"};
  settings_load( keys );

  // Settings SET EEPROM !
  settings_set("id", 1);
  settings_set("model", 0);   // 0: TTGO/Wemos 

  // SET PULLUP
  pinMode(BTN_GO, INPUT_PULLUP);
  
  // GO 
  attachInterrupt(digitalPinToInterrupt(BTN_GO), go, FALLING);
  
  // Oled INIT
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay();
  display.drawBitmap(0, 0, crnl, 64, 48, 1);
  display.display();
  delay(2000);

  // Olead header
  display.setTextWrap(false);
  display.clearDisplay();
  display.setCursor(0, 0);
  display.setTextSize(1);
  display.setTextColor(BLACK);
  display.setTextColor(BLACK, WHITE);
  display.println("  stimbox  ");
  display.display();
}

// LOOP
//
void loop(void) 
{
  event_loop();

  
  delay(1);
  
}
