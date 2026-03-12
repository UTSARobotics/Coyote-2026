cmake_minimum_required(VERSION 3.10)

project(ros3_realsense2)

# Find required packages
find_package(ros3 REQUIRED)
find_package(mirage REQUIRED)
find_package(librealsense2 REQUIRED)

# Include directories
include_directories(
    ${ROS3_INCLUDE_DIRS}
    ${MIRAGE_INCLUDE_DIRS}
    ${LIBREALSENSE2_INCLUDE_DIRS}
    include
)

# Link directories
link_directories(
    ${ROS3_LIBRARY_DIRS}
    ${MIRAGE_LIBRARY_DIRS}
    ${LIBREALSENSE2_LIBRARY_DIRS}
)

# Add executable
add_executable(realsense_driver
    src/main.cpp
    src/realsense_driver.cpp
)

# Link libraries
target_link_libraries(realsense_driver
    ${ROS3_LIBRARIES}
    ${MIRAGE_LIBRARIES}
    ${LIBREALSENSE2_LIBRARIES}
)

# Set C++ standard
target_compile_features(realsense_driver PRIVATE cxx_std_17)

# Install target
install(TARGETS realsense_driver
    RUNTIME DESTINATION bin
)