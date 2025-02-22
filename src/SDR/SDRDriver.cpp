#include "SDRDriver.hpp"

#include <iostream>
#include <stdexcept>

SDR::SDR(const SDRcfg::SDRConfig& cfg)
    : config(cfg), rxBuffer(cfg.bufferSize * 2), txBuffer(cfg.bufferSize * 2) {
    std::cout << "SDR CLASS INIT";
}
