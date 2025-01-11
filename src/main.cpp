#include "Common.hpp"
// #include "fkYAML/node.hpp"

int main() {
    // std::ifstream ifs("/home/kasperekd/code/TRX/examples/test_config.yml");
    try {
        // Создаем экземпляр конфигурации
        Config config;

        // Путь к YAML-файлу
        std::string configPath =
            "/home/kasperekd/code/TRX/examples/test_config.yml";

        // Загружаем конфигурацию
        config.loadFromFile(configPath);

        // Получаем и отображаем системные настройки
        const auto& systemConfig = config.getSystemConfig();
        std::cout << "System Configuration:" << std::endl;
        std::cout << "  Log Level: " << systemConfig.logLevel << std::endl;
        std::cout << "  Log File: " << systemConfig.logFile << std::endl;
        std::cout << "  Max Threads: " << systemConfig.maxThreads << std::endl;

        // Получаем и отображаем настройки SDR
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

            // Параметры приемника
            std::cout << "  RX Settings:" << std::endl;
            std::cout << "    Frequency: " << sdr.rxFrequency << " MHz"
                      << std::endl;
            std::cout << "    Sample Rate: " << sdr.rxSampleRate << " KSPS"
                      << std::endl;
            std::cout << "    Bandwidth: " << sdr.rxBandwidth << " kHz"
                      << std::endl;

            // Параметры передатчика
            std::cout << "  TX Settings:" << std::endl;
            std::cout << "    Frequency: " << sdr.txFrequency << " MHz"
                      << std::endl;
            std::cout << "    Sample Rate: " << sdr.txSampleRate << " KSPS"
                      << std::endl;
            std::cout << "    Bandwidth: " << sdr.txBandwidth << " kHz"
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
