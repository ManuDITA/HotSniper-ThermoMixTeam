#include <hotPotato.h>

#include <iomanip>
using namespace std;
HotPotato::HotPotato(const PerformanceCounters *performanceCounters,
                     int coreRows, int coreColumns,
                     float criticalTemperature,
                     float recoveryTemperature, 
                     float rotationIncrementStep, 
                     float rotationStartInterval,
                     float rotationMinInterval)
    : performanceCounters(performanceCounters),
      coreRows(coreRows), coreColumns(coreColumns),
      criticalTemperature(criticalTemperature), recoveryTemperature(recoveryTemperature),
      rotationIncrementStep(rotationIncrementStep), 
      rotationStartInterval(rotationStartInterval), rotationInterval(rotationStartInterval),
      rotationMinInterval(rotationMinInterval) {
        masterCore.push(0);
      }

std::vector<int> HotPotato::map(String taskName, int taskCoreRequirement,
const std::vector<bool> &availableCoresRO,
const std::vector<bool> &activeCores) {
    std::vector<bool> availableCores(availableCoresRO);
    std::vector<int> cores;
    static int lastAssignedCore = -1;
    
    for (int c = 0; c < availableCores.size() && taskCoreRequirement > 0; c++) {
        if (availableCores.at(c)) {
            cores.push_back(c);
            taskCoreRequirement--;
        }
    }

    return cores;
}

std::vector<migration> HotPotato::migrate(
    SubsecondTime time, const std::vector<int> &taskIds,
    const std::vector<bool> &activeCores) {
    std::vector<migration> migrations;
    std::vector<bool> availableCores(coreRows * coreColumns);
    for (int c = 0; c < coreRows * coreColumns; c++) {
        availableCores.at(c) = taskIds.at(c) == -1;
    }

    SubsecondTime currentTime = time;
    static SubsecondTime lastMigrationTime = SubsecondTime::NS(0);
    SubsecondTime localRotationInterval = SubsecondTime::NS(rotationInterval);
    if(currentTime - lastMigrationTime < localRotationInterval){
        //Nothing to migrate
        return migrations;
    }
    lastMigrationTime = currentTime;

    //Update migration speed
    if(performanceCounters->getPeakTemperature() > criticalTemperature){
        cout << "[Scheduler][hotPotato-migrate]: Decreasing rotation interval due to thermal violation" << endl;
        if(rotationInterval > rotationMinInterval) rotationInterval -= rotationIncrementStep;
    }
    else if(performanceCounters->getPeakTemperature() <= recoveryTemperature){
        cout << "[Scheduler][hotPotato-migrate]: Resuming rotation interval due to thermal recovery" << endl;
        rotationInterval = rotationStartInterval;
    }

    size_t cores = coreRows * coreColumns;

    //Keep track of task ids
    std::vector<int> newTaskIds(taskIds);
    int masterCount = masterCore.empty() ? 0 : masterCore.size();
    cout << "[Scheduler][hotPotato-migrate]: Number of masters is " << masterCore.size()
                        << endl;
    if(masterCore.empty())  return migrations;

    int multiStep = 1; //How many cores ahead to check for new master
    for (int j = 0; j < masterCount; j++) {
        //Pop first master core and set it as the current master
        int currentMaster = masterCore.front();
        masterCore.pop();
        cout << "[Scheduler][hotPotato-migrate]: Current master is " << currentMaster
                                                << endl;
        //if (activeCores.at(c) && c == currentMaster) {
        if (activeCores.at(currentMaster)) {
        
            //Find the next core. If the next core is also the master, go one ahead
            int nextCore = (currentMaster + 1) % cores;
            cout << "[Scheduler][hotPotato-migrate]: Next core is " << nextCore
                    << endl;

            //Check if next core is free and we have another master core
            //If next core has adifferent task id, that must mean it is another master
            int multiMaster = (nextCore+multiStep) % cores;
            if(taskIds.at(currentMaster) != taskIds.at(multiMaster) && activeCores.at(multiMaster)){
                masterCore.push(multiMaster);
                cout << "[Scheduler][hotPotato-migrate]: Diff master at " 
                << multiMaster << endl;
            }

            masterCore.push(nextCore); //Push the master for the next interval         

            cout << "[Scheduler][hotPotato-migrate]: core " << currentMaster
                    << " migrate to core " << nextCore << endl;
            //Since next core is free, perform migration
            migration m;
            m.fromCore = currentMaster;
            m.toCore = nextCore;
            m.swap = taskIds.at(nextCore) != -1;
            migrations.push_back(m);
            
            //Swap task ids in list
            newTaskIds.at(nextCore) = newTaskIds.at(currentMaster);
        }   
    }
    return migrations;
}

void HotPotato::logTemperatures(const std::vector<bool> &availableCores) {
    cout << "[Scheduler][hotPotato-map]: temperatures of available cores:"
         << endl;
    for (int y = 0; y < coreRows; y++) {
        for (int x = 0; x < coreColumns; x++) {
            if (x > 0) {
                cout << " ";
            }
            int coreId = y * coreColumns + x;
            if (!availableCores.at(coreId)) {
                cout << " - ";
            } else {
                float temperature =
                    performanceCounters->getTemperatureOfCore(coreId);
                cout << fixed << setprecision(1) << temperature;
            }
        }
        cout << endl;
    }
}
