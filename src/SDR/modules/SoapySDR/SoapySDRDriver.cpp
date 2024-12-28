#include "SoapySDRDriver.hpp"

#include <iostream>

SoapySDRDriver::SoapySDRDriver(const SDRConfig& cfg) : SDR(cfg) {}

void SoapySDRDriver::initialize() {
    std::cout << "Initializing SoapySDR with sample rate: " << config.sampleRate
              << " Hz, frequency: " << config.frequency
              << " Hz, and gain: " << config.gain << " dB." << std::endl;
}

void SoapySDRDriver::sendSamples() {
    std::cout << "Sending samples to SoapySDR" << std::endl;
}

void SoapySDRDriver::receiveSamples() {
    std::cout << "Receiving samples from SoapySDR" << std::endl;
}
