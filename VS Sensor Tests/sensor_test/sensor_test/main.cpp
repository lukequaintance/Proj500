#include <windows.h>
#include <iostream>
#include <vector>
#include <chrono>

#define COM_PORT "\\\\.\\COM13"
#define BAUD_RATE CBR_4800

#define moist			0x00
#define temp			0x01
#define cond			0x02
#define N				0x04
#define P				0x05
#define K				0x06


constexpr unsigned char data_codes[6] = { moist,temp,cond,N,P,K };

//////// CHOOSE TEST DATA ////////
unsigned char test_data = data_codes[5];

// Create Modbus request (without CRC)
std::vector<unsigned char> modbusRequest = { 0x01, 0x03, 0x00, test_data, 0x00, 0x01 };

// functions
void ConfigureSerialPort(HANDLE hSerial);
bool WriteToSerial(HANDLE hSerial, const std::vector<unsigned char>& data);
bool ReadFromSerial(HANDLE hSerial, std::vector<unsigned char>& response, int expectedBytes);
uint16_t calculateCRC(const std::vector<unsigned char>& data);



int main() {

	std::cout << "Sensor Test Program!!!" << std::endl << std::endl;

	// Compute CRC-16 during runtime
	uint16_t crc = calculateCRC(modbusRequest);
	
	// add the CRC bytes to the 'modbusRequest' frame
	modbusRequest.push_back(static_cast<unsigned char>(crc & 0xFF));			// Low byte
	modbusRequest.push_back(static_cast<unsigned char>((crc >> 8) & 0xFF));		// High byte
	// now the modbusRequest frame has the two CRC bytes

	// open handle to serial port
	HANDLE hSerial = CreateFile(COM_PORT, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);

	// error handling
	if (hSerial == INVALID_HANDLE_VALUE) {
		std::cerr << "Error opening COM13" << std::endl;
		return 1;
	}

	// serial port init
	ConfigureSerialPort(hSerial);

	// write to COM port
	if (!WriteToSerial(hSerial, modbusRequest)) {
		std::cerr << "Error writing to COM13" << std::endl;
		CloseHandle(hSerial);
		return 1;
	}

	// response stored here
	std::vector<unsigned char> response;
	// read from COM port
	if (ReadFromSerial(hSerial, response, 7)) {  // Expected response length: 7 bytes
		if (response[1] == 0x03) { // Modbus function code 0x03 (read holding registers)
			int16_t data_rx = (response[3] << 8) | response[4];  // Combine two bytes			
			float tm = data_rx / 10.0f; // scale by 10 (for temp or humid values)

			// print appropriate value
			if (test_data == temp) std::cout << "Temperature: " << tm << " C" << std::endl;
			else if (test_data == moist) std::cout << "Moisture: " << tm << " %" << std::endl;
			else {
				float other_data = data_rx;
				if (test_data == cond) std::cout << "Conductivity: " << other_data << " uS/cm" << std::endl;
				if (test_data == N) std::cout << "Nitrogen Level: " << other_data << " ppm" << std::endl;
				if (test_data == P) std::cout << "Phosphorus Level: " << other_data << " ppm" << std::endl;
				if (test_data == K) std::cout << "Potassium Level: " << other_data << " ppm" << std::endl;
			}
			
			
		}
		else {
			std::cerr << "Error: Invalid response from sensor." << std::endl;
		}
	}
	else {
		std::cerr << "Error reading from COM13" << std::endl;
	}

	// serial port deinit
	CloseHandle(hSerial);
	
}


// functions

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
				crc ^= 0xA001; // Modbus CRC-16 polynomial
			}
			else {
				crc >>= 1;
			}
		}
	}
	return crc;
}
