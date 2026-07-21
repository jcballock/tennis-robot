#include <Arduino.h>

String inputBuffer = "";

void parseCommand(String command) {
  command.trim(); // Remove leading/trailing whitespace & line endings

  if (command.equalsIgnoreCase("PING")) {
    Serial.println("PONG");
  } 
  else if (command.equalsIgnoreCase("LED_ON")) {
    digitalWrite(LED_BUILTIN, HIGH);
    Serial.println("OK: LED turned ON");
  } 
  else if (command.equalsIgnoreCase("LED_OFF")) {
    digitalWrite(LED_BUILTIN, LOW);
    Serial.println("OK: LED turned OFF");
  } 
  else {
    Serial.print("ERR: Unknown Command -> ");
    Serial.println(command);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  while (Serial.available() > 0) {
    char incomingChar = Serial.read();

    if (incomingChar == '\n' || incomingChar == '\r') {
      if (inputBuffer.length() > 0) {
        parseCommand(inputBuffer);
        inputBuffer = ""; // Reset buffer after parsing
      }
    } else {
      inputBuffer += incomingChar;
    }
  }
}