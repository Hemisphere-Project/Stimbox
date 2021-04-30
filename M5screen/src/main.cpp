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



void header(uint16_t color) {

  M5.Lcd.setFreeFont(&FreeSansBold9pt7b);
  M5.Lcd.setTextColor(TFT_BLACK, color);
  M5.Lcd.fillRect(0, 0, 320, 24, color);
  M5.Lcd.setTextDatum(TC_DATUM);
  M5.Lcd.drawString("STiMBOX", 160, 5);

}

void setStatus(String status1 = "") {

  M5.Lcd.fillRect(0, 38, 320, 22,  TFT_BLACK);

  if (status1 != "") {
    M5.Lcd.setFreeFont(&FreeSans9pt7b);
    M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
    M5.Lcd.setTextDatum(TC_DATUM);
    M5.Lcd.drawString(status1, 160, 40);
  }
}

void setMedia(String media = "") {
  
  M5.Lcd.fillRect(0, 108, 320, 27,  TFT_BLACK);

  if (media != "") {
    M5.Lcd.setFreeFont(&FreeSans12pt7b);
    M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
    M5.Lcd.setTextDatum(TC_DATUM);
    M5.Lcd.drawString(media, 160, 110);
  }
}

void setCtrl(String txt = "", uint16_t bgColor = TFT_CYAN) {

  M5.Lcd.fillRect(25, 210, 80, 30,  TFT_BLACK); // clear CTRL area
  if (txt != "") {
    M5.Lcd.fillRect(25, 210, 80, 30,  bgColor); 
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
    setStatus("connecting");
  }

  else if (_state == STOP) 
  {
    header(TFT_DARKCYAN);
    setStatus("ready");
    setMedia();
    setCtrl("PLAY", TFT_DARKGREY);
  }
  else if (_state == PLAY) 
  {
    header(TFT_DARKGREEN);
    setStatus("playing");
    setCtrl("PAUSE", TFT_DARKGREY);
  }
  else if (_state == PAUSE) 
  {
    header(TFT_YELLOW);
    setStatus("paused");
    setCtrl("PLAY", TFT_DARKGREY);
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
    setStatus("system is shutting down..");
  }  

}


// RECV
//

const byte numChars = 64;
char receivedChars[numChars];
const char fluxMarker = '^';
boolean recvInProgress = false;
byte ndx = 0;

void recvWithStartEndMarkers() 
{

  while (Serial.available() > 0) {
    
    char rc = Serial.read();
    
    // CONTINUE 
    if (recvInProgress == true) 
    {
      // Receive
      if (rc != fluxMarker) 
      {
        receivedChars[ndx] = rc;
        ndx++;
        if (ndx >= numChars) ndx = numChars - 1;
      }

      // End
      else 
      {
        recvInProgress = false;
        receivedChars[ndx] = '\0'; // terminate the string

        // Parse
        String input = String(receivedChars);
        if (input.length() != 0) 
        {
          char cmd = input.charAt(0);
          input.remove(0, 1);

          // State
          if (cmd == 'S')
            setState( (State)input.toInt() );

          // Volume
          else if (cmd == 'V')
            setVolume( input.toInt() );
          
          // Media
          else if (cmd == 'M')
            setMedia( input );
        }
      }
    }

    // NEW INSTRUCTION 
    else if (rc == fluxMarker) {
      recvInProgress = true;
      ndx = 0;
    }
  }
}


// SETUP
//

void setup() 
{
  Serial.begin(115200);
  delay(100);
  Serial.setTimeout(10);

  M5.begin(true, false, false, true);   // LCD : SD : Serial : I2C
  delay(100);
  
  setState(BOOT);
}

// LOOP
//

void loop() {

  M5.update();

  recvWithStartEndMarkers();

  if (M5.BtnA.wasPressed()) 
  {
    if (_state == STOP) Serial.println("play");
    else if (_state == PLAY) Serial.println("pause");
    else if (_state == PAUSE) Serial.println("resume");
  }
  else if (M5.BtnA.pressedFor(500,500)) {
    if (_state == PLAY || _state == PAUSE) Serial.println("stop");
  }
  
  if (M5.BtnB.wasPressed() || M5.BtnB.pressedFor(300,150) ) {
    Serial.println("voldown");
  }

  if (M5.BtnC.wasPressed() || M5.BtnC.pressedFor(300,150) ) {
    Serial.println("volup");
  }

}


