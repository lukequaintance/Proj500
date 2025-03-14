#include <windows.h>
#include <iostream>
#include <vector>
#include <chrono>
#include <thread>

#define COM_PORT L"\\\\.\\COM3"
#define BAUD_RATE CBR_4800

// Data addresses
#define moist 0x00
#define temp  0x01
#define cond  0x02
#define ph    0x03
#define N     0x04
#define P     0x05
#define K     0x06

constexpr unsigned char data_codes[7] = { moist, temp, cond, ph, N, P, K };

void ConfigureSerialPort(HANDLE hSerial);
bool WriteToSerial(HANDLE hSerial, const std::vector<unsigned char>& data);
bool ReadFromSerial(HANDLE hSerial, std::vector<unsigned char>& response, int expectedBytes);
uint16_t calculateCRC(const std::vector<unsigned char>& data);
float parseResponse(unsigned char registerAddress, const std::vector<unsigned char>& response);

int main() {
    std::cout << "Sensor Test Program - Updating every 5 seconds" << std::endl << std::endl;

    HANDLE hSerial = CreateFile(COM_PORT, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);
    if (hSerial == INVALID_HANDLE_VALUE) {
        std::cerr << "Error opening " << COM_PORT << std::endl;
        return 1;
    }
    ConfigureSerialPort(hSerial);

    while (true) {
        std::cout << "\nReading sensor data...\n";
        for (unsigned char test_data : data_codes) {
            std::vector<unsigned char> modbusRequest = { 0x01, 0x03, 0x00, test_data, 0x00, 0x01 };
            uint16_t crc = calculateCRC(modbusRequest);
            modbusRequest.push_back(static_cast<unsigned char>(crc & 0xFF));
            modbusRequest.push_back(static_cast<unsigned char>((crc >> 8) & 0xFF));

            if (!WriteToSerial(hSerial, modbusRequest)) {
                std::cerr << "Error writing to COM port" << std::endl;
                continue;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(500));

            std::vector<unsigned char> response;
            if (ReadFromSerial(hSerial, response, 7)) {
                if (response[1] == 0x03) {
                    float value = parseResponse(test_data, response);
                    switch (test_data) {
                    case temp:  std::cout << "Temperature: " << value << " C" << std::endl; break;
                    case moist: std::cout << "Moisture: " << value << " %" << std::endl; break;
                    case cond:  std::cout << "Conductivity: " << value << " uS/cm" << std::endl; break;
                    case ph:    std::cout << "pH: " << value << " level" << std::endl; break;
                    case N:     std::cout << "Nitrogen: " << value << " ppm" << std::endl; break;
                    case P:     std::cout << "Phosphorus: " << value << " ppm" << std::endl; break;
                    case K:     std::cout << "Potassium: " << value << " ppm" << std::endl; break;
                    }
                }
                else {
                    std::cerr << "Invalid response from sensor." << std::endl;
                }
            }
            else {
                std::cerr << "Error reading from COM port" << std::endl;
            }
        }
        std::cout << "\nWaiting 5 seconds...\n";
        std::this_thread::sleep_for(std::chrono::seconds(5));
    }
    CloseHandle(hSerial);
}

float parseResponse(unsigned char registerAddress, const std::vector<unsigned char>& response) {
    int16_t rawValue = (response[3] << 8) | response[4];
    if (registerAddress == temp || registerAddress == moist || registerAddress == ph) {
        return rawValue / 10.0f;
    }
    return static_cast<float>(rawValue);
}

void ConfigureSerialPort(HANDLE hSerial) {
    DCB dcbSerialParams = { 0 };
    dcbSerialParams.DCBlength = sizeof(dcbSerialParams);
    GetCommState(hSerial, &dcbSerialParams);
    dcbSerialParams.BaudRate = BAUD_RATE;
    dcbSerialParams.ByteSize = 8;
    dcbSerialParams.Parity = NOPARITY;
    dcbSerialParams.StopBits = ONESTOPBIT;
    SetCommState(hSerial, &dcbSerialParams);
}

bool WriteToSerial(HANDLE hSerial, const std::vector<unsigned char>& data) {
    DWORD bytesWritten;
    return WriteFile(hSerial, data.data(), data.size(), &bytesWritten, NULL);
}

bool ReadFromSerial(HANDLE hSerial, std::vector<unsigned char>& response, int expectedBytes) {
    DWORD bytesRead;
    response.resize(expectedBytes);
    return ReadFile(hSerial, response.data(), expectedBytes, &bytesRead, NULL) && bytesRead == expectedBytes;
}

uint16_t calculateCRC(const std::vector<unsigned char>& data) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < data.size(); i++) {
        crc ^= static_cast<uint16_t>(data[i]);
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x0001) {
                crc >>= 1;
                crc ^= 0xA001;
            }
            else {
                crc >>= 1;
            }
        }
    }
    return crc;
}
