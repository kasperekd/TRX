#ifndef SDRDRIVER_HPP
#define SDRDRIVER_HPP

#include <memory>

#include "SDRConfig.hpp"

class SDR {
   public:
    SDRcfg::SDRConfig config;
    // TODO: Нужно использовать кольцевые буферы без блокировок который работает
    // на основе атомарных индексов.
    std::unique_ptr<int16_t[]> rxBuffer;
    std::unique_ptr<int16_t[]> txBuffer;

    explicit SDR(const SDRcfg::SDRConfig& cfg);
    virtual void initialize() = 0;
    virtual void sendSamples() = 0;
    virtual void receiveSamples() = 0;
    virtual ~SDR() = default;

   protected:
    void allocateBuffers();
};

#endif
