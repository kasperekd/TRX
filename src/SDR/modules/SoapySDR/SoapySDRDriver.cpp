#include "SoapySDRDriver.hpp"

#include <iostream>
#include <stdexcept>

SoapySDRDriver::SoapySDRDriver(const SDRcfg::SDRConfig& cfg)
    : SDR(cfg),
      device(nullptr),
      rxStream(nullptr),
      txStream(nullptr),
      rxMTU(0),
      txMTU(0),
      rxBuffer(cfg.bufferSize * 2),
      txBuffer(cfg.bufferSize * 2) {
    try {
        // Поиск устройства SoapySDR
        auto devices = SoapySDR::Device::enumerate();
        if (devices.empty()) {
            throw std::runtime_error("No SoapySDR devices found.");
        }

        // Выбор устройства по имени или адресу
        // for (const auto& devInfo : devices) {
        //     if (devInfo.at("label") == config.name ||
        //         devInfo.at("serial") == config.deviceAddress) {
        //         device = SoapySDR::Device::make(devInfo);
        //         break;
        //     }
        // }
        SoapySDRKwargs args = {};
        SoapySDRKwargs_set(&args, "uri", "usb:");
        SoapySDRKwargs_set(&args, "direct", "1");

        if (!device) {
            throw std::runtime_error(
                "Failed to find SoapySDR device with name: " + config.name +
                " or address: " + config.deviceAddress);
        }

        std::cout << "SoapySDR device initialized." << std::endl;
    } catch (const std::exception& e) {
        throw std::runtime_error("Error initializing SoapySDR: " +
                                 std::string(e.what()));
    }
}

void SoapySDRDriver::initialize() {
    try {
        device->setFrequency(SOAPY_SDR_RX, 0, config.rxFrequency);

        device->setSampleRate(SOAPY_SDR_RX, 0, config.rxSampleRate);

        device->setBandwidth(SOAPY_SDR_RX, 0, config.rxBandwidth);

        device->setGain(SOAPY_SDR_RX, 0, config.gain);

        if (config.gainMode != SDRcfg::Manual) {
            device->setGainMode(SOAPY_SDR_RX, 0, true);  // AGC
        } else {
            device->setGainMode(SOAPY_SDR_RX, 0, false);
        }

        device->setFrequency(SOAPY_SDR_TX, 0, config.txFrequency);

        device->setSampleRate(SOAPY_SDR_TX, 0, config.txSampleRate);

        device->setBandwidth(SOAPY_SDR_TX, 0, config.txBandwidth);

        rxStream = device->setupStream(SOAPY_SDR_RX, SOAPY_SDR_CS16);
        txStream = device->setupStream(SOAPY_SDR_TX, SOAPY_SDR_CS16);

        rxMTU = device->getStreamMTU(rxStream);
        txMTU = device->getStreamMTU(txStream);

        std::cout << "SoapySDR initialized with MTU (RX: " << rxMTU
                  << ", TX: " << txMTU << ")." << std::endl;
    } catch (const std::exception& e) {
        throw std::runtime_error("Error during SoapySDR initialization: " +
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