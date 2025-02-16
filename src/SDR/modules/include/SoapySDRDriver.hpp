#ifndef SOAPYSDRDRIVER_HPP
#define SOAPYSDRDRIVER_HPP

#include <SoapySDR/Device.hpp>
#include <SoapySDR/Errors.hpp>
#include <SoapySDR/Formats.hpp>

#include "RingBuffer.hpp"
#include "SDRDriver.hpp"

class SoapySDRDriver : public SDR {
   public:
    explicit SoapySDRDriver(const SDRcfg::SDRConfig& cfg);
    void initialize() override;
    void sendSamples() override;
    void receiveSamples() override;

    RingBuffer<int16_t>& getRxBuffer() { return rxBuffer; }
    RingBuffer<int16_t>& getTxBuffer() { return txBuffer; }

   private:
    SoapySDR::Device* device;      // Указатель на устройство SoapySDR
    SoapySDR::Stream* rxStream;    // Поток RX
    SoapySDR::Stream* txStream;    // Поток TX
    size_t rxMTU;                  // Размер MTU для RX
    size_t txMTU;                  // Размер MTU для TX
    RingBuffer<int16_t> rxBuffer;  // Кольцевой буфер для RX
    RingBuffer<int16_t> txBuffer;  // Кольцевой буфер для TX
};

#endif