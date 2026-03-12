#include "realsense_driver.h"
#include <cstdio>

int main(int argc, char **argv) {
    // Initialize driver
    int init_result = realsense_driver_init(argc, argv);
    if (init_result != 0) {
        std::fprintf(stderr, "Driver initialization failed with code %d\n", init_result);
        return init_result;
    }

    // Run main processing loop
    realsense_driver_run();

    // Cleanup
    realsense_driver_shutdown();

    return 0;
}