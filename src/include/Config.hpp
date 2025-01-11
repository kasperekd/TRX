#ifndef CONFIG_HPP
#define CONFIG_HPP

#include <string>

#include "SDRConfig.hpp"
#include "SDRConfigManager.hpp"
#include "SystemConfig.hpp"
#include "fkYAML/node.hpp"

class Config {
   private:
    SystemConfig systemConfig;
    SDRConfigManager sdrConfigManager;

   public:
    void loadFromFile(const std::string& filepath);
    const SystemConfig& getSystemConfig() const;
    const std::vector<SDRcfg::SDRConfig>& getSDRConfigs() const;
};

#endif  // CONFIG_HPP
