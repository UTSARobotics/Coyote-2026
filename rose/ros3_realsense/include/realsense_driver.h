#ifndef REALSENSE_DRIVER_H
#define REALSENSE_DRIVER_H

#include "realsense_config.h"
#include "ros3.h"

#ifdef __cplusplus
extern "C" {
#endif

// Initialize RealSense driver
int realsense_driver_init(int argc, char **argv);

// Main processing loop
void realsense_driver_run();

// Cleanup and shutdown
void realsense_driver_shutdown();

#ifdef __cplusplus
}
#endif

#endif // REALSENSE_DRIVER_H