#ifndef SOAPYSDRDRIVER_HPP
#define SOAPYSDRDRIVER_HPP

#include "SDRDriver.hpp"

class SoapySDRDriver : public SDR {
   public:
    explicit SoapySDRDriver(const SDRcfg::SDRConfig& cfg);
    void initialize() override;
    void sendSamples() override;
    void receiveSamples() override;
};

#endif
