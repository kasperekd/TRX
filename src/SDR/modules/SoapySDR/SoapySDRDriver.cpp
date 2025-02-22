#include "SoapySDRDriver.hpp"

#include <iostream>
#include <stdexcept>

SoapySDRDriver::SoapySDRDriver(const SDRcfg::SDRConfig& cfg)
    : SDR(cfg),
      device(nullptr),
      rxStream(nullptr),
      txStream(nullptr),
      rxMTU(0),
      txMTU(0) {
    try {
        std::cout << "Scanning for available SDR devices..." << std::endl;
        std::vector<SoapySDR::Kwargs> devices = SoapySDR::Device::enumerate();

        if (devices.empty()) {
            std::cerr << "No SoapySDR devices found!" << std::endl;
        } else {
            std::cout << "Available SDR devices:" << std::endl;
            for (size_t i = 0; i < devices.size(); i++) {
                std::cout << "Device " << i + 1 << ":" << std::endl;
                for (const auto& [key, value] : devices[i]) {
                    std::cout << "  " << key << ": " << value << std::endl;
                }
            }
        }

        SoapySDR::Kwargs args;
        args["driver"] = "plutosdr";
        args["remote"] = config.deviceAddress;

        device = SoapySDR::Device::make(args);
        if (!device) {
            throw std::runtime_error("Failed to create SoapySDR device.");
        }

        std::cout << "SoapySDR device successfully created." << std::endl;
    } catch (const std::exception& e) {
        throw std::runtime_error("Error creating SoapySDR device: " +
                                 std::string(e.what()));
    }
}

SoapySDRDriver::~SoapySDRDriver() {
    try {
        if (device) {
            std::cout << "Releasing SoapySDR resources..." << std::endl;

            if (rxStream) {
                device->deactivateStream(rxStream);
                device->closeStream(rxStream);
                rxStream = nullptr;
            }

            if (txStream) {
                device->deactivateStream(txStream);
                device->closeStream(txStream);
                txStream = nullptr;
            }

            SoapySDR::Device::unmake(device);
            device = nullptr;

            std::cout << "SoapySDR resources released successfully."
                      << std::endl;
        }
    } catch (const std::exception& e) {
        std::cerr << "Error in SoapySDRDriver destructor: " << e.what()
                  << std::endl;
    }
}

void SoapySDRDriver::initialize() {
    if (!device) {
        throw std::runtime_error("Device is not initialized.");
    }

    try {
        // FIXME: Задавать Buffer Size, MTU Size
        // device->writeSetting("buffer_size",
        // std::to_string(config.bufferSize));

        device->setSampleRate(SOAPY_SDR_RX, 0, config.rxSampleRate);
        device->setFrequency(SOAPY_SDR_RX, 0, config.rxFrequency);
        device->setBandwidth(SOAPY_SDR_RX, 0, config.rxBandwidth);
        device->setGain(SOAPY_SDR_RX, 0, config.gain);
        // device->setStreamMTU(SOAPY_SDR_RX, 0, 4096);

        device->setSampleRate(SOAPY_SDR_TX, 0, config.txSampleRate);
        device->setFrequency(SOAPY_SDR_TX, 0, config.txFrequency);
        device->setBandwidth(SOAPY_SDR_TX, 0, config.txBandwidth);
        device->setGain(SOAPY_SDR_TX, 0, config.gain);

        // FIXME: Нужен CF32 ?
        rxStream = device->setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32);
        if (!rxStream) throw std::runtime_error("Failed to create RX stream.");

        txStream = device->setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32);
        if (!txStream) throw std::runtime_error("Failed to create TX stream.");

        device->activateStream(rxStream);
        device->activateStream(txStream);

        rxMTU = device->getStreamMTU(rxStream);
        txMTU = device->getStreamMTU(txStream);

        std::cout << "SoapySDR device initialized successfully." << std::endl;
    } catch (const std::exception& e) {
        throw std::runtime_error("Error in SoapySDRDriver::initialize: " +
                                 std::string(e.what()));
    }
}

void SoapySDRDriver::receiveSamples() {
    try {
        device->activateStream(rxStream);

        std::vector<int16_t> buffer(
            rxMTU * 2);  // FIXME: ЭТО ПРОСТО ЗАГЛУШКА! НЕ ИСПОЛЬЗОВАТЬ ТАК
        void* buffs[] = {buffer.data()};  // Массив указателей на буферы

        int flags = 0;
        long long timeNs = 0;
        int ret =
            device->readStream(rxStream, buffs, rxMTU, flags, timeNs, 400000);

        if (ret < 0) {
            throw std::runtime_error("Error reading samples from SoapySDR: " +
                                     std::string(SoapySDR::errToStr(ret)));
        }

        for (int i = 0; i < ret * 2; ++i) {  // I и Q
            rxBuffer.push(buffer[i]);
        }

        std::cout << "Received " << ret << " samples from SoapySDR."
                  << std::endl;

        device->deactivateStream(rxStream);
    } catch (const std::exception& e) {
        throw std::runtime_error("Error receiving samples: " +
                                 std::string(e.what()));
    }
}
void SoapySDRDriver::sendSamples() {
    try {
        device->activateStream(txStream);

        std::vector<int16_t> buffer(
            txMTU * 2);  // FIXME: ЭТО ПРОСТО ЗАГЛУШКА! НЕ ИСПОЛЬЗОВАТЬ ТАК

        // извлечение из кольцевого буфера
        for (size_t i = 0; i < txMTU * 2; ++i) {
            if (!txBuffer.pop(buffer[i])) {
                buffer[i] = 0;
            }
        }

        const void* buffs[] = {buffer.data()};

        int flags = 0;
        long long timeNs = 0;
        int ret =
            device->writeStream(txStream, buffs, txMTU, flags, timeNs, 400000);

        if (ret < 0) {
            throw std::runtime_error("Error writing samples to SoapySDR: " +
                                     std::string(SoapySDR::errToStr(ret)));
        }

        std::cout << "Sent " << ret << " samples to SoapySDR." << std::endl;

        device->deactivateStream(txStream);
    } catch (const std::exception& e) {
        throw std::runtime_error("Error sending samples: " +
                                 std::string(e.what()));
    }
}