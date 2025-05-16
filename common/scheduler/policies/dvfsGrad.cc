#include "dvfsGrad.h"

#include <iomanip>
#include <iostream>
using namespace std;
DVFSGrad::DVFSGrad(const PerformanceCounters *performanceCounters,
                           int coreRows, int coreColumns, int minFrequency,
                           int maxFrequency, int frequencyStepSize,
                           float upThreshold, float downThreshold,
                           float dtmCriticalTemperature,
                           float dtmRecoveredTemperature)
    : performanceCounters(performanceCounters),
      coreRows(coreRows),
      coreColumns(coreColumns),
      minFrequency(minFrequency),
      maxFrequency(maxFrequency),
      frequencyStepSize(frequencyStepSize),
      upThreshold(upThreshold),
      downThreshold(downThreshold),
      dtmCriticalTemperature(dtmCriticalTemperature),
      dtmRecoveredTemperature(dtmRecoveredTemperature) {
        cout << "[Scheduler][grad-DTM]: initialized" << endl;
        freqStep = (int)(1000 * frequencyStepSize + 0.5);
      }
std::vector<int> DVFSGrad::getFrequencies(
    const std::vector<int> &oldFrequencies,
    const std::vector<bool> &activeCores) {
    if (throttle()) {
        std::vector<int> minFrequencies(coreRows * coreColumns, minFrequency);
        cout << "[Scheduler][grad-DTM]: in throttle mode -> return min. frequencies " << endl;
            return minFrequencies;
    } else {
        std::vector<int> frequencies(coreRows * coreColumns);
        for (unsigned int coreCounter = 0; coreCounter < coreRows * coreColumns;
             coreCounter++) {
            if (activeCores.at(coreCounter)) {
                float power = performanceCounters->getPowerOfCore(coreCounter);
                float temperature =
                    performanceCounters->getTemperatureOfCore(coreCounter);
                int frequency = oldFrequencies.at(coreCounter);
                float utilization =
                    performanceCounters->getUtilizationOfCore(coreCounter);
                cout << "[Scheduler][grad]: Core " << setw(2)
                     << coreCounter << ":";
                cout << " P=" << fixed << setprecision(3) << power << " W";
                cout << " f=" << frequency << " MHz";
                cout << " T=" << fixed << setprecision(1) << temperature
                     << " C";
                // avoid the little circle symbol, it is not ASCII
                cout << " utilization=" << fixed << setprecision(3)
                     << utilization << endl;
                // use same period for upscaling and downscaling as described
                // in "The grad governor."
                if (utilization > upThreshold) {
                    cout << " -> try to increase frequency" << endl;
                    float midpoint = dtmRecoveredTemperature + ((dtmCriticalTemperature - dtmRecoveredTemperature) / 2);

//                    if (temperature > midpoint){
//                        cout << "Exceeded midpoint, try to recover" << endl;
//                        frequency /= 2;    
//                    }
                    //else {
                        float multiplier = dtmRecoveredTemperature - temperature;
                        int change = 100 * multiplier;
                        if (change < 0){
                            change *= 4;
                        } else if (change > freqStep) {
                            change = freqStep;
                        }

                        frequency = frequency + change;
                        if (frequency > maxFrequency)
                            frequency = maxFrequency;
                    //}
                } else if (utilization < downThreshold) {
                    cout
                        << "[Scheduler][grad]: utilization < downThreshold";
                    if (frequency == minFrequency) {
                        cout << " but already at min frequency" << endl;
                    } else {
                        cout << " -> lower frequency" << endl;
                        // frequency = frequency * 80 / 100;
                        // frequency = (frequency / frequencyStepSize) *
                        //             frequencyStepSize;  // round
                        frequency /= 2;
                        if (frequency < minFrequency) {
                            frequency = minFrequency;
                        }
                    }
                }
                frequencies.at(coreCounter) = frequency;
            } else {
                frequencies.at(coreCounter) = minFrequency;
            }
        }
        return frequencies;
    }
}
bool DVFSGrad::throttle() {
    if (performanceCounters->getPeakTemperature() > dtmCriticalTemperature) {
        if (!in_throttle_mode) {
            cout << "[Scheduler][grad-DTM]: detected thermal violation"
                 << endl;
        }
        in_throttle_mode = true;
    } else if (performanceCounters->getPeakTemperature() <
               dtmRecoveredTemperature) {
        if (in_throttle_mode) {
            cout << "[Scheduler][grad-DTM]: thermal violation ended"
                 << endl;
        }
        in_throttle_mode = false;
    }
    return in_throttle_mode;
}

