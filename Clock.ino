#include <DS3231.h>
#include <Wire.h>
#include <EEPROM.h>

DS3231 Clock;

/* Code TM1637 4 digit 7 segment display with Arduino and DS3231 RTC */


#include <TM1637Display.h>
// Define the connections pins:
#define CLK 2
#define DIO 3
// Create display object of type TM1637Display:
TM1637Display display = TM1637Display(CLK, DIO);
// Create array that turns all segments on:
const uint8_t data[] = {0xff, 0xff, 0xff, 0xff};
// Create array that turns all segments off:
const uint8_t blank[] = {0x00, 0x00, 0x00, 0x00};
// You can set the individual segments per digit to spell words or create other symbols:
const uint8_t done[] = {
  SEG_B | SEG_C | SEG_D | SEG_E | SEG_G,           // d
  SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F,   // O
  SEG_C | SEG_E | SEG_G,                           // n
  SEG_A | SEG_D | SEG_E | SEG_F | SEG_G            // E
};
// Create degree Celsius symbol:
const uint8_t celsius[] = {
  SEG_A | SEG_B | SEG_F | SEG_G,  // Circle
  SEG_A | SEG_D | SEG_E | SEG_F   // C
};


const byte max_chars = 32;        // Size of array to read serial data into
char received_chars[max_chars];   // Array to store the received serial data
int num_bytes;                    // Number of bytes read
boolean newData = false;          // Indicates if new data has been found or not
const int timeout_length = 10;    // Timeout reading commands...10 is a good value

int years = 20;
int months = 1;
int days = 1;
int dow = 0;
int hours = 1;
int minutes = 1;
int seconds = 0;
int disp = 12;
int brightness = 7;

void setup() {
    // Set up I2C interface to RTC module
    Wire.begin();
    // Set up the display
    display.clear();
    delay(500);
    brightness = retrieveDisplayBrightness();
    if (brightness == 0) brightness = 7;
    display.setBrightness(brightness);
    delay(500);
    display.showNumberDecEx(0, 0b01000000, true, 4, 0);
    // Start the serial connection
    Serial.begin(9600);
    delay(1000);
    display.showNumberDecEx(0, 0b00000000, true, 4, 0);
    // Send a ready message to any PC that's listening
    Serial.println("<Ready>");
    delay(1000);
    // Set clock module to 24 hour.  This hasn't been working for me so will deal with 12/24 differently
    Clock.setClockMode(false);
    // Initialise the time
    getClockBrightness();
    getClockDisplay();
    getTime();
    //fakeTime();
}


void loop() {
    bool h12, PM; // These are populated with whether it's a 12 or 24 hour clock, and whether it's currently AM or PM
    int delay_length = 1000;
    int last_time_length = 4;
    while (true) {        
        hours = Clock.getHour(h12, PM);
        minutes = Clock.getMinute();
        seconds = Clock.getSecond();
        if (seconds > 50) delay_length = 1000;
        else delay_length = 10000;
        // Time is 24 hour, adjust the hour display if it's a 12 hour display
        if (disp == 12 and hours > 12) 
            hours = hours - 12;
        if (hours < 10) {
            // Clear the left most segment if last time was four digits
            if (last_time_length == 4) {
                display.setSegments(blank, 1, 0);
            }
            // Display a three character time with leading zeros
            display.showNumberDecEx(hours*100 + minutes, 0b10000000, true, 3, 1);
            last_time_length = 3;
        } else {
            // Display a four character time
            display.showNumberDecEx(hours*100 + minutes, 0b01000000, false, 4, 0);
            last_time_length = 4;
        }
        delay(delay_length);
    }
}


// Read data from the USB between a < and a > into a string array
// If after the timeout period no more data is received, no new data is recorded
void receiveDataFromUSB(int timeout) {
    int waited = 0;
    char rc;
    bool started = false;
    bool colon = false;
    num_bytes = 0;
    newData = false;
    while (not newData) {
        // Flash the colon on the display to indicate we're waiting
        if (colon) display.showNumberDecEx(0, 0b01000000, true, 4, 0);
        else display.showNumberDecEx(0, 0b00000000, true, 4, 0);
        colon = not colon;
        // Read the data on the serial queue if there is any
        if (Serial.available() > 0) {
            waited = 0;
            rc = Serial.read();
            delay(100);
            if (rc == '<') {
                started = true;
            } else {
                if (rc == '>') {
                    newData = true;
                    return;
                } else {
                    // Read the data into a character array
                    if (started) {
                        received_chars[num_bytes] = rc;
                        num_bytes++;
                        // Bail if there's no room left in the buffer
                        if (num_bytes == max_chars) return;
                    }
                }
            }
        } else {
            // Wait for a second before seeing if there's more data, eventually timing out
            delay(1000);
            waited++;
            if (waited > timeout) {
                return;
            }
        }
    }
}


void getClockBrightness() {
    // Request the 12 or 24 hour setting
    display.showNumberDecEx(0, 0b01000000, true, 4, 0);
    Serial.println("<Brightness>");
    delay(1000);
    receiveDataFromUSB(timeout_length);
    if (newData) {
        // <FIXME> could check the brightness better here and loop if it was bad
        brightness = (received_chars[0] - 48);
        // Send to clock, write to eeprom if different
        if (retrieveDisplayBrightness() != brightness) {
            storeDisplayBrightness(brightness);
            display.setBrightness(brightness);
            // Flash the display to indicate brightness has been updated from PC
            for (int i = 0; i <= 5; i++) {
                display.showNumberDecEx(brightness, 0b00000000, false, 4, 0);
                delay(100);
                display.clear();
                delay(100);
            }
        }
        newData = false;
    }
    brightness = retrieveDisplayBrightness();
    //Serial.println(brightness);
}


void getClockDisplay() {
    // Request the 12 or 24 hour setting
    display.showNumberDecEx(0, 0b01000000, true, 4, 0);
    Serial.println("<Display>");
    delay(1000);
    receiveDataFromUSB(timeout_length);
    if (newData) {
        // <FIXME> could check the display better here and loop if it was bad
        disp = ((received_chars[0] - 48) * 10) + (received_chars[1] - 48);
        if (retrieveDisplay1224() != disp) {
            storeDisplay1224(disp);        
            // Flash the display to indicate display has been updated from PC
            for (int i = 0; i <= 5; i++) {
                display.showNumberDecEx(disp, 0b00000000, false, 4, 0);
                delay(100);
                display.clear();
                delay(100);
            }
        }
        newData = false;
    }
    // Put the current display setting in a variable for use later
    disp = retrieveDisplay1224();
    //Serial.println(disp);
}


void fakeTime() {
    // Fake the time up for testing the display
    
    delay(1000);
    Clock.setYear(2020);
    Clock.setMonth(04);
    Clock.setDate(8);
    Clock.setDoW(1);
    Clock.setHour(11);
    Clock.setMinute(30);
    Clock.setSecond(45);
    delay(1000);
    //Clock.setClockMode(true);

}


void getTime() {
    // Request the time and parse any return
    display.showNumberDecEx(0, 0b01000000, true, 4, 0);
    Serial.println("<Time>");
    delay(1000);
    receiveDataFromUSB(timeout_length);
    if (newData) {
        // <FIXME> could check the time better here and loop if it was bad
        years = ((received_chars[0] - 48) * 10) + (received_chars[1] - 48);
        months = ((received_chars[2] - 48) * 10) + (received_chars[3] - 48);
        days = ((received_chars[4] - 48) * 10) + (received_chars[5] - 48);
        dow = (received_chars[6] - 48);
        hours = ((received_chars[7] - 48) * 10) + (received_chars[8] - 48);
        minutes = ((received_chars[9] - 48) * 10) + (received_chars[10] - 48);
        seconds = ((received_chars[11] - 48) * 10) + (received_chars[12] - 48);
        Clock.setYear(years);
        Clock.setMonth(months);
        Clock.setDate(days);
        Clock.setDoW(dow);
        Clock.setHour(hours);
        Clock.setMinute(minutes);
        Clock.setSecond(seconds);
        //Serial.println(hours+minutes+seconds);
        // Flash the display to indicate time has been updated from PC
        for (int i = 0; i <= 5; i++) {
            display.showNumberDecEx(hours*100 + minutes, 0b01000000, false, 4, 0);
            delay(100);
            display.clear();
            delay(100);
        }
        // Tell PC we're good and wait in expectation of a reset
        Serial.println("<Thanks>");
        delay(5000);
    } 
}


int retrieveDisplayBrightness() {
    // Return the brightness from EEPROM
    return EEPROM.read(0);
}


void storeDisplayBrightness(int b) {
    // Set the brightness in the EEPROM
    EEPROM.write(0, b);
}


int retrieveDisplay1224() {
    // Return the 12/24 from EEPROM
    return EEPROM.read(1);
}


void storeDisplay1224(int b) {
    // Set the 12/24 in the EEPROM
    EEPROM.write(1, b);
}
