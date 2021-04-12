#include <Arduino.h>
#include <M5Stack.h>


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

void control(String txt, uint16_t color) {
  M5.Lcd.setFreeFont(&FreeSansBold9pt7b);
  M5.Lcd.setTextColor(TFT_BLACK,    color);
  M5.Lcd.fillRect(20, 210, 90, 30,  color);
  M5.Lcd.setTextDatum(TC_DATUM);
  M5.Lcd.drawString(txt, 65, 216);  
}

void volume(uint8_t value) {
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

void status(String status, String media="") {

  M5.Lcd.setFreeFont(&FreeSans9pt7b);
  M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
  M5.Lcd.setTextDatum(TC_DATUM);
  M5.Lcd.drawString(status, 160, 70);

  M5.Lcd.setFreeFont(&FreeSans12pt7b);
  M5.Lcd.drawString(media, 160, 120);

}


void setup() {

  M5.begin();
  delay(100);

  Serial.println("starting");
  
  // SCREEN
  M5.Lcd.clear(TFT_BLACK);

  header(TFT_DARKGREEN);
  control("PLAY", TFT_DARKGREEN);
  volume(100);

  status("playing", "Super_top_01.wav");


  Serial.println("ready");

}

void loop() {

  M5.update();

  // recvWithStartEndMarkers();
}


// void recvWithStartEndMarkers() 
// {
//   static boolean recvInProgress = false;
//   static byte ndx = 0;
//   char fluxMarker = '¤';
//   char splitMarker = '£';
//   char rc;

//   while (Serial.available() > 0 && newData == false) {
    
//     rc = Serial.read();
    
//     if (recvInProgress == true) {

//       // End of Line
//       if (rc == fluxMarker || rc == splitMarker) {
//         receivedChars[ndx] = '\0'; // terminate the string
//         ndx = 0;

//         // Draw
//         String input = String(receivedChars);
//         if (input.length() != 0) {
//           // Get args
//           int input_arg1 = atoi(&input[0]);
      
//           // SPECIAL ARGS
//           if (input_arg1 == 0) M5.Lcd.clear(TFT_BLACK);
      
//           // STANDARD TEXT ( Line 1--9 )
//           else if ((input_arg1 >= 1) && (input_arg1 <= 9)) {
//             input.remove(0, 1);
//             int posY = 10 + 13*(input_arg1-1);
//             drawStringWithSymbol(0, posY, input);
//           }
//         }

//         // End of Transmission
//         if (rc == fluxMarker) recvInProgress = false;
//       }

//       // Receive in progress
//       else {
//         receivedChars[ndx] = rc;
//         ndx++;
//         if (ndx >= numChars) ndx = numChars - 1;
//       }
      
//     }

//     else if (rc == fluxMarker) {
//       recvInProgress = true;
//       ndx = 0;
//     }
//   }

// }