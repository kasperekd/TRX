#ifndef SDRCONFIGMANAGER_HPP
#define SDRCONFIGMANAGER_HPP

#include <vector>

#include "SDRConfig.hpp"
#include "fkYAML/node.hpp"

class SDRConfigManager {
   private:
    std::vector<SDRcfg::SDRConfig> sdrConfigs;

   public:
    void loadFromNode(const fkyaml::node& sdrNode);
    const std::vector<SDRcfg::SDRConfig>& getConfigs() const;
};

#endif  // SDRCONFIGMANAGER_HPP
