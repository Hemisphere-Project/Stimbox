#include <Arduino.h>
#include <M5Stack.h>

#include <OSCBundle.h>
#include <SLIPEncodedSerial.h>
SLIPEncodedSerial SLIPSerial(Serial);

// STATE
enum State {BOOT, HELLO, STOP, PLAY, PAUSE, EXIT, OFF};

State _state = BOOT;
int _volume = 100;
String _media = "";

// CONFIG
int Brightness = 20;
int longPressDelay = 300;
int holdRepeatDelay = 100;

// RECV
const byte numChars = 32;
char receivedChars[numChars];
boolean newData = false;


// void drawStringWithSymbol( int x, int y, String s) {

//   bool special = false;
//   bool unifont = false;
//   bool colored = false;

//   // clear line
//   u8g2.drawUTF8(x, y, "                      ");
  
//   for (int k = 0; k < s.length(); k++) {

//     // engage special
//     if (s[k] == '^') special = true;
    
//     // special engaged
//     else if (special) {
//       if (s[k] == '0') u8g2.setDrawColor(1);      // Black BG
//       else if (s[k] == '1') u8g2.setDrawColor(0); // White BG
//       else if (s[k] == '2') u8g2.setFont(u8g2_font_open_iconic_embedded_1x_t);
//       else if (s[k] == '3') u8g2.setFont(u8g2_font_open_iconic_gui_1x_t);
//       else if (s[k] == '4') u8g2.setFont(u8g2_font_open_iconic_thing_1x_t);
//       else if (s[k] == '5') u8g2.setFont(u8g2_font_open_iconic_play_1x_t);
//       else if (s[k] == '6') u8g2.setFont(u8g2_font_open_iconic_arrow_1x_t);
//       else if (s[k] == '7') u8g2.setFont(u8g2_font_open_iconic_human_1x_t);
//       else if (s[k] == '8') u8g2.setFont(u8g2_font_open_iconic_mime_1x_t);
//       else if (s[k] == '9') u8g2.setFont(u8g2_font_open_iconic_www_1x_t);
      
//       if (s[k] >= '2') unifont = true;
//       special = false;
//     }
    
//     // draw next character
//     else {
//       x += u8g2.drawUTF8(x, y, String(s[k]).c_str() );
//       if (unifont) {
//         x += 5;
//         u8g2.setFont(u8g2_font_6x12_me);
//         unifont = false;
//       }
//     }
    
//   }
  
//   u8g2.setDrawColor(1);
  
// }

int xpos, ypos;


void header(uint16_t color) {

  M5.Lcd.setFreeFont(&FreeSansBold9pt7b);
  M5.Lcd.setTextColor(TFT_BLACK, color);
  M5.Lcd.fillRect(0, 0, 320, 24, color);
  M5.Lcd.setTextDatum(TC_DATUM);
  M5.Lcd.drawString("STiMBOX", 160, 5);

}

void setStatus(String status1, String status2="") {

  M5.Lcd.setFreeFont(&FreeSans9pt7b);
  M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
  M5.Lcd.setTextDatum(TC_DATUM);
  M5.Lcd.drawString(status1, 160, 70);

  M5.Lcd.setFreeFont(&FreeSans12pt7b);
  M5.Lcd.drawString(status2, 160, 120);

}

void setCtrl(String txt = "", uint16_t bgColor = TFT_CYAN) {

  M5.Lcd.fillRect(20, 210, 90, 30,  TFT_BLACK); // clear CTRL area

  if (txt != "") 
  {
    M5.Lcd.setFreeFont(&FreeSansBold9pt7b);
    M5.Lcd.setTextDatum(TC_DATUM);
    M5.Lcd.setTextColor(TFT_BLACK,    bgColor);
    M5.Lcd.drawString(txt, 65, 216);  
  }

}

void setVolume(int value) 
{
  _volume = value;

  M5.Lcd.setFreeFont(&TomThumb);
  M5.Lcd.setTextColor(TFT_DARKGREY, TFT_BLACK);
  M5.Lcd.setTextDatum(TC_DATUM);
  M5.Lcd.setTextSize(2);
  M5.Lcd.drawString("volume", 213, 204);

  M5.Lcd.setFreeFont(&FreeSansBold9pt7b);
  M5.Lcd.setTextSize(1);
  M5.Lcd.setTextColor(TFT_BLACK, TFT_DARKGREY);
  M5.Lcd.fillRect(132, 219, 152, 21, TFT_DARKGREY);
  M5.Lcd.setTextDatum(TC_DATUM);
  M5.Lcd.drawString("-", 160, 222);
  M5.Lcd.drawString(String(value), 207, 222);
  M5.Lcd.drawString("+", 255, 222);
}


void setState(State value) {

  _state = value;

  if (_state == BOOT) {
    M5.Lcd.clear(TFT_BLACK);
    setStatus("STiMBOX starting..");
  }

  else if (_state == HELLO) {
    M5.Lcd.clear(TFT_BLACK);
    header(TFT_DARKCYAN);
    setStatus("connected");
  }

  else if (_state == STOP) 
  {
    header(TFT_DARKGREY);
    setStatus("stopped");
    setCtrl("PLAY", TFT_DARKGREEN);
  }
  else if (_state == PLAY) 
  {
    header(TFT_DARKGREEN);
    setStatus("playing", _media);
    setCtrl("PAUSE", TFT_YELLOW);
  }
  else if (_state == PAUSE) 
  {
    header(TFT_YELLOW);
    setStatus("paused");
    setCtrl("PLAY", TFT_DARKGREEN);
  }  
  else if (_state == EXIT) 
  {
    M5.Lcd.clear(TFT_BLACK);
    header(TFT_CYAN);
    setStatus("STiMBOX exiting..");
  }  
  else if (_state == OFF) 
  {
    M5.Lcd.clear(TFT_BLACK);
    header(TFT_RED);
    setStatus("shutting down..");
  }  

}






void setup() {

  SLIPSerial.begin(115200);

  M5.begin(true, false, false, true);   // LCD : SD : Serial : I2C
  delay(100);

  setState(BOOT);
  Serial.println("starting");
}


void loop() {

  M5.update();

  OSCBundle bundleIN;
  int size;

  while(!SLIPSerial.endofPacket())
    if( (size = SLIPSerial.available()) > 0)
       while(size--) bundleIN.fill(SLIPSerial.read());
  
  if(!bundleIN.hasError()) 
  {

    bundleIN.dispatch("/hello", [](OSCMessage &msg){
      setState(HELLO);
    });

    bundleIN.dispatch("/stopped", [](OSCMessage &msg){
      setState(STOP);
    });

    bundleIN.dispatch("/paused", [](OSCMessage &msg){
      setState(PAUSE);
    });

    bundleIN.dispatch("/playing", [](OSCMessage &msg){
      if(msg.isString(0))
      {
        int length=msg.getDataLength(0);
        char str[length];
        msg.getString(0,str,length);
        _media = String(str);
      }
      setState(PLAY);
    });

    bundleIN.dispatch("/exit", [](OSCMessage &msg){
      setState(EXIT);
    });

    bundleIN.dispatch("/off", [](OSCMessage &msg){
      setState(OFF);
    });

    bundleIN.dispatch("/volumeset", [](OSCMessage &msg){
      if (msg.isInt(0)) 
        setVolume(msg.getInt(0));
    });

  }

}

