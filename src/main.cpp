#include "Common.hpp"

int main() {
    SDRConfig config(SDRDeviceType::SoapySDR, 1024, 2.4e6, 915e6, 10.0);

    try {
        SoapySDRDriver sdr(config);
        sdr.initialize();
        sdr.sendSamples();
        sdr.receiveSamples();
    } catch (const std::exception &e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
