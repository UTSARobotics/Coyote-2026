CC ?= gcc
CXX ?= g++

# Paths to dependencies
ROS3_DIR ?= ../ros3
MIRAGE_DIR ?= ../mirage

# Include paths - use system librealsense headers
INCLUDES := -Iinclude -I$(ROS3_DIR)/include -I$(MIRAGE_DIR)/include -I/usr/include/librealsense2

# Library paths - use local librealsense library (newer version)
LIB_PATHS := -L$(ROS3_DIR)/build -L$(MIRAGE_DIR)/build -L/usr/local/lib

# Libraries
LIBS := -lros3 -lmirage -lrealsense2

# Compiler flags - add rpath for local libraries to override system version
CXXFLAGS := -Wall -Wextra -std=c++17 -O3 $(INCLUDES) -Wl,-rpath,/usr/local/lib

# Compiler flags
CXXFLAGS := -Wall -Wextra -std=c++17 -O3 $(INCLUDES)

# Build directory
BUILD_DIR := build

# Source files
SRC := src/main.cpp src/realsense_driver.cpp

# Target executable
TARGET := $(BUILD_DIR)/realsense_driver

# Default target
all: $(TARGET)

# Build the driver
$(TARGET): $(SRC) | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(SRC) -o $@ $(LIB_PATHS) $(LIBS)

# Create build directory
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Clean
clean:
	rm -rf $(BUILD_DIR)

# Install
install: $(TARGET)
	mkdir -p $(DESTDIR)$(PREFIX)/bin
	cp $(TARGET) $(DESTDIR)$(PREFIX)/bin/

.PHONY: all clean install