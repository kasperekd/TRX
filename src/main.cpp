#include "Common.hpp"
// #include "fkYAML/node.hpp"

#include <chrono>
#include <cmath>

#include "ThreadManager.hpp"

bool isPrime(int number) {
    if (number <= 1) return false;
    for (int i = 2; i <= std::sqrt(number); ++i) {
        if (number % i == 0) return false;
    }
    return true;
}

void heavyTask(size_t id, int limit) {
    int count = 0;
    for (int i = 2; i < limit; ++i) {
        if (isPrime(i)) ++count;
    }
    std::cout << "Task " << id << " finished, primes counted: " << limit
              << "\n";
    return;
}

int main() {
    const size_t numThreads = 2;
    const size_t numTasks = 10;
    const int computationLimit = 100000;
    const int computationLimit2 = 100001;

    ThreadManager threadManager(numThreads);

    auto start = std::chrono::high_resolution_clock::now();

    for (size_t i = 0; i < numTasks; ++i) {
        threadManager.addTask(
            [i, computationLimit]() { heavyTask(i, computationLimit); },
            ThreadManager::TaskPriority::Low);
    }
    for (size_t i = 0; i < 2; ++i) {
        threadManager.addTask(
            [i, computationLimit2]() { heavyTask(i, computationLimit2); });
    }

    threadManager.waitForAll();
    threadManager.stopAll();

    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> duration = end - start;

    std::cout << "Total execution time: " << duration.count() << " seconds\n";

    return 0;

    // std::ifstream ifs("/home/kasperekd/code/TRX/examples/test_config.yml");
    // try {
    //     Config config;

    //     std::string configPath =
    //         "/home/kasperekd/code/TRX/examples/test_config.yml";

    //     config.loadFromFile(configPath);

    //     const auto& systemConfig = config.getSystemConfig();
    //     std::cout << "System Configuration:" << std::endl;
    //     std::cout << "  Log Level: " << systemConfig.logLevel << std::endl;
    //     std::cout << "  Log File: " << systemConfig.logFile << std::endl;
    //     std::cout << "  Max Threads: " << systemConfig.maxThreads <<
    //     std::endl;

    //     const auto& sdrConfigs = config.getSDRConfigs();
    //     std::cout << "\nSDR Configurations:" << std::endl;

    //     for (const auto& sdr : sdrConfigs) {
    //         std::cout << "  Name: " << sdr.name << std::endl;
    //         std::cout << "  Device Type: "
    //                   << (sdr.deviceType == SDRcfg::SDRDeviceType::SoapySDR
    //                           ? "SoapySDR"
    //                           : "UHD")
    //                   << std::endl;
    //         std::cout << "  Device Address: " << sdr.deviceAddress <<
    //         std::endl; std::cout << "  Buffer Size: " << sdr.bufferSize <<
    //         std::endl; std::cout << "  Multiplier: " << sdr.multiplier <<
    //         std::endl;

    //         std::cout << "  RX Settings:" << std::endl;
    //         std::cout << "    Frequency: " << sdr.rxFrequency << ""
    //                   << std::endl;
    //         std::cout << "    Sample Rate: " << sdr.rxSampleRate << ""
    //                   << std::endl;
    //         std::cout << "    Bandwidth: " << sdr.rxBandwidth << ""
    //                   << std::endl;

    //         std::cout << "  TX Settings:" << std::endl;
    //         std::cout << "    Frequency: " << sdr.txFrequency << ""
    //                   << std::endl;
    //         std::cout << "    Sample Rate: " << sdr.txSampleRate << ""
    //                   << std::endl;
    //         std::cout << "    Bandwidth: " << sdr.txBandwidth << ""
    //                   << std::endl;

    //         std::cout << "-----------------------" << std::endl;
    //     }

    //     return 0;
    // } catch (const std::exception& e) {
    //     std::cerr << "Error: " << e.what() << std::endl;
    //     return 1;
    // }

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
