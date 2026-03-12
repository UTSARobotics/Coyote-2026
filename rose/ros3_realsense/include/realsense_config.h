#ifndef REALSENSE_CONFIG_H
#define REALSENSE_CONFIG_H

// RealSense D435 Camera Configuration
#define REALSENSE_RGB_WIDTH 1280
#define REALSENSE_RGB_HEIGHT 720
#define REALSENSE_RGB_FPS 6
#define REALSENSE_DEPTH_WIDTH 640
#define REALSENSE_DEPTH_HEIGHT 480
#define REALSENSE_DEPTH_FPS 6

// Decimation filter configuration (reduces resolution for better performance)
#define ENABLE_DECIMATION_FILTER 1
#define DECIMATION_MAGNITUDE 2.0f  // 2.0 = half resolution, 3.0 = third resolution, etc.

// Emitter configuration (IR projector for depth sensing)
#define ENABLE_EMITTER 1                 // Set to 0 to disable emitter (passive mode)
#define EMITTER_POWER 150.0f            // Emitter power level (0-360 mW)

// Topic names
#define TOPIC_RGB "/camera/rgb"
#define TOPIC_DEPTH "/camera/depth"
#define TOPIC_POINTCLOUD "/camera/pointcloud"

// Message buffer sizes (in bytes)
#define RGB_MESSAGE_SIZE (REALSENSE_RGB_WIDTH * REALSENSE_RGB_HEIGHT * 3)
#define DEPTH_MESSAGE_SIZE (REALSENSE_DEPTH_WIDTH * REALSENSE_DEPTH_HEIGHT * 2)
#define POINTCLOUD_MESSAGE_SIZE (REALSENSE_DEPTH_WIDTH * REALSENSE_DEPTH_HEIGHT * 12) // 12 bytes per point (3 floats)

// Message rates (Hz)
#define RGB_MESSAGE_RATE 30
#define DEPTH_MESSAGE_RATE 30
#define POINTCLOUD_MESSAGE_RATE 30

#endif // REALSENSE_CONFIG_H