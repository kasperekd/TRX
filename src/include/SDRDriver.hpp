#ifndef SDRDRIVER_HPP
#define SDRDRIVER_HPP

#include <memory>

#include "RingBuffer.hpp"
#include "SDRConfig.hpp"

class SDR {
   public:
    SDRcfg::SDRConfig config;
    // std::unique_ptr<int16_t[]> rxBuffer;
    // std::unique_ptr<int16_t[]> txBuffer;

    RingBuffer<int16_t> rxBuffer;  // Кольцевой буфер для RX
    RingBuffer<int16_t> txBuffer;  // Кольцевой буфер для TX

    explicit SDR(const SDRcfg::SDRConfig& cfg);
    virtual void initialize() = 0;
    virtual void sendSamples() = 0;
    virtual void receiveSamples() = 0;
    virtual ~SDR() = default;

   protected:
    void allocateBuffers();
};

#endif
