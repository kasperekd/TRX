#include "SDRDriver.hpp"

#include <stdexcept>

SDR::SDR(const SDRConfig& cfg) : config(cfg) { allocateBuffers(); }

void SDR::allocateBuffers() {
    size_t totalSize = config.bufferSize * 2;  // I и Q
    try {
        rxBuffer = std::make_unique<int16_t[]>(totalSize);
        txBuffer = std::make_unique<int16_t[]>(totalSize);
    } catch (const std::bad_alloc& e) {
        throw std::runtime_error("Failed to allocate buffers: " +
                                 std::string(e.what()));
    }
}
