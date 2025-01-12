#include "Common.hpp"
// #include "fkYAML/node.hpp"

int main() {
    // std::ifstream ifs("/home/kasperekd/code/TRX/examples/test_config.yml");
    try {
        Config config;

        std::string configPath =
            "/home/kasperekd/code/TRX/examples/test_config.yml";

        config.loadFromFile(configPath);

        const auto& systemConfig = config.getSystemConfig();
        std::cout << "System Configuration:" << std::endl;
        std::cout << "  Log Level: " << systemConfig.logLevel << std::endl;
        std::cout << "  Log File: " << systemConfig.logFile << std::endl;
        std::cout << "  Max Threads: " << systemConfig.maxThreads << std::endl;

        const auto& sdrConfigs = config.getSDRConfigs();
        std::cout << "\nSDR Configurations:" << std::endl;

        for (const auto& sdr : sdrConfigs) {
            std::cout << "  Name: " << sdr.name << std::endl;
            std::cout << "  Device Type: "
                      << (sdr.deviceType == SDRcfg::SDRDeviceType::SoapySDR
                              ? "SoapySDR"
                              : "UHD")
                      << std::endl;
            std::cout << "  Device Address: " << sdr.deviceAddress << std::endl;
            std::cout << "  Buffer Size: " << sdr.bufferSize << std::endl;
            std::cout << "  Multiplier: " << sdr.multiplier << std::endl;

            std::cout << "  RX Settings:" << std::endl;
            std::cout << "    Frequency: " << sdr.rxFrequency << ""
                      << std::endl;
            std::cout << "    Sample Rate: " << sdr.rxSampleRate << ""
                      << std::endl;
            std::cout << "    Bandwidth: " << sdr.rxBandwidth << ""
                      << std::endl;

            std::cout << "  TX Settings:" << std::endl;
            std::cout << "    Frequency: " << sdr.txFrequency << ""
                      << std::endl;
            std::cout << "    Sample Rate: " << sdr.txSampleRate << ""
                      << std::endl;
            std::cout << "    Bandwidth: " << sdr.txBandwidth << ""
                      << std::endl;

            std::cout << "-----------------------" << std::endl;
        }

        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    // try {
    //     SoapySDRDriver sdr(sdrConfig);
    //     sdr.initialize();
    //     sdr.sendSamples();
    //     sdr.receiveSamples();
    // } catch (const std::exception &e) {
    //     std::cerr << "Error: " << e.what() << std::endl;
    //     return 1;
    // }

    return 0;
}
