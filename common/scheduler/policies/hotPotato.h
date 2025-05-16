/**
* This header implements a policy that utilizes the Hot Potato approach
* 
*/

#ifndef __HOTPOTATO_H
#define __HOTPOTATO_H
#include <vector>
#include <queue>

#include "mappingpolicy.h"
#include "migrationpolicy.h"
#include "performance_counters.h"
class HotPotato : public MappingPolicy, public MigrationPolicy {
   public:
    HotPotato(const PerformanceCounters *performanceCounters,
        int coreRows, int coreColumns, float criticalTemperature, float recoveryTemperature, 
        float rotationIncrementStep, float rotationStartInterval, float rotationMinInterval);
    virtual std::vector<int> map(String taskName, int taskCoreRequirement,
            const std::vector<bool> &availableCores,
            const std::vector<bool> &activeCores);
    virtual std::vector<migration> migrate(
        SubsecondTime time, const std::vector<int> &taskIds,
        const std::vector<bool> &activeCores);

   private:
    const PerformanceCounters *performanceCounters;
    float criticalTemperature;
    float recoveryTemperature;
    unsigned int coreRows;
    unsigned int coreColumns;
    String logic;
    float rotationIncrementStep;
    float rotationStartInterval;
    float rotationMinInterval;
    float rotationInterval;
    std::queue<int> masterCore;
    int totalMasters;

    void logTemperatures(const std::vector<bool> &availableCores);
};
#endif