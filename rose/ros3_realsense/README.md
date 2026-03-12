# ROS3 RealSense2 Driver

A ROS3 C++ driver for Intel RealSense D435 camera that publishes RGB images, depth images, and point clouds.

## Features

- **RGB Image Streaming**: 1280x720 @ 30 FPS
- **Depth Image Streaming**: 1280x720 @ 30 FPS  
- **Point Cloud Generation**: Textured 3D point clouds
- **ROS3 Integration**: Uses ROS3 middleware for inter-process communication
- **Configurable**: Resolution, FPS, and other parameters in `realsense_config.h`

## Topics Published

- `/camera/rgb` - RGB image data (RGB8 format)
- `/camera/depth` - Depth image data (16-bit depth)
- `/camera/pointcloud` - 3D point cloud data (XYZ coordinates)

## Build Requirements

- ROS3 (included in this repository)
- Mirage (included in this repository)  
- Librealsense2 (included in this repository)
- C++17 compiler

## Building

```bash
cd ros3_realsense2
make
```

## Running

```bash
./build/realsense_driver
```

## Configuration

Edit `include/realsense_config.h` to modify camera parameters:

```cpp
// Camera resolution and frame rate
#define REALSENSE_RGB_WIDTH 1280
#define REALSENSE_RGB_HEIGHT 720
#define REALSENSE_RGB_FPS 30
#define REALSENSE_DEPTH_WIDTH 1280
#define REALSENSE_DEPTH_HEIGHT 720
#define REALSENSE_DEPTH_FPS 30

// Decimation filter configuration (reduces resolution for better performance)
#define ENABLE_DECIMATION_FILTER 1       // Set to 0 to disable
#define DECIMATION_MAGNITUDE 2.0f        // 2.0 = half resolution, 3.0 = third resolution, etc.

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
#define POINTCLOUD_MESSAGE_SIZE (REALSENSE_DEPTH_WIDTH * REALSENSE_DEPTH_HEIGHT * 12)

// Message rates (Hz)
#define RGB_MESSAGE_RATE 30
#define DEPTH_MESSAGE_RATE 30
#define POINTCLOUD_MESSAGE_RATE 30
```

### Decimation Filter

The decimation filter reduces the resolution of depth images to improve performance:

- **Magnitude 1.0**: No reduction (original resolution)
- **Magnitude 2.0**: Half resolution (recommended for better performance)
- **Magnitude 3.0**: Third resolution (lower resolution, better performance)
- **Magnitude 4.0**: Quarter resolution (lowest resolution, best performance)

**Note**: RGB images are not decimated, only depth images and derived point clouds.

### Emitter Configuration

The IR emitter (laser projector) can be configured for different operating modes:

- **Enabled (1)**: Active depth sensing with IR projection (better accuracy)
- **Disabled (0)**: Passive mode (uses ambient IR light, lower accuracy)

**Power Levels**: 0-360 mW (higher power = better outdoor performance but more power consumption)

- **0-100 mW**: Indoor use, short range
- **100-200 mW**: General purpose (default 150 mW)
- **200-360 mW**: Outdoor use, long range

**Note**: Emitter must be enabled for optimal depth performance, especially in low-light conditions.

## Message Format Definition

All messages use Mirage's `numericarray` type, which includes size information for self-describing messages.

### RGB Image Message
- **Topic**: `/camera/rgb`
- **Format**: Mirage numeric array (MIRAGE_ARRAY_UINT8)
- **Data Type**: `uint8_t[width × height × 3]`
- **Structure**: `[R, G, B, R, G, B, ...]` (row-major order)
- **Size Information**: Automatically included in numeric array header
- **Units**: 8-bit RGB values (0-255)

### Depth Image Message  
- **Topic**: `/camera/depth`
- **Format**: Mirage numeric array (MIRAGE_ARRAY_UINT16)
- **Data Type**: `uint16_t[width × height]`
- **Structure**: `[depth1, depth2, ...]` (row-major order)
- **Size Information**: Automatically included in numeric array header
- **Units**: Millimeters (0-65535 mm)

### Point Cloud Message
- **Topic**: `/camera/pointcloud`
- **Format**: Mirage numeric array (MIRAGE_ARRAY_FLOAT32)
- **Data Type**: `float[width × height × 3]`
- **Structure**: `[X1,Y1,Z1, X2,Y2,Z2, ...]` (row-major order)
- **Size Information**: Automatically included in numeric array header
- **Units**: Meters (X,Y,Z coordinates)

## Example Decoding Code (C++)

```cpp
#include <ros3.h>
#include <mirage.h>
#include <cstdio>

void decode_rgb_message(mirage_msg *msg) {
    // Read numeric array (automatically gets size from header)
    mirage_read_start(msg);
    int64_t array_type;
    int64_t element_size;
    int64_t array_length;
    uint8_t *rgb_data = nullptr;
    
    mirage_read_numericarray(msg, &array_type, &element_size, &array_length, &rgb_data);
    
    if (array_type == MIRAGE_ARRAY_UINT8 && element_size == 1) {
        int width = 1280;
        int height = 720;
        int expected_size = width * height * 3;
        
        if (array_length == expected_size) {
            // Process RGB data (example: save first pixel)
            uint8_t r = rgb_data[0];
            uint8_t g = rgb_data[1]; 
            uint8_t b = rgb_data[2];
            printf("RGB - First pixel: R=%d, G=%d, B=%d\n", r, g, b);
            
            // Get center pixel
            int center_idx = (height / 2) * width + (width / 2);
            center_idx *= 3; // 3 bytes per pixel
            uint8_t center_r = rgb_data[center_idx];
            uint8_t center_g = rgb_data[center_idx + 1];
            uint8_t center_b = rgb_data[center_idx + 2];
            printf("RGB - Center pixel: R=%d, G=%d, B=%d\n", center_r, center_g, center_b);
        }
    }
    
    if (rgb_data) {
        free(rgb_data); // Mirage allocates this memory
    }
}

void decode_depth_message(mirage_msg *msg) {
    // Read numeric array (automatically gets size from header)
    mirage_read_start(msg);
    int64_t array_type;
    int64_t element_size;
    int64_t array_length;
    uint8_t *depth_data_bytes = nullptr;
    
    mirage_read_numericarray(msg, &array_type, &element_size, &array_length, &depth_data_bytes);
    
    if (array_type == MIRAGE_ARRAY_UINT16 && element_size == 2) {
        int width = 1280;
        int height = 720;
        int expected_size = width * height;
        
        if (array_length == expected_size * 2) { // 2 bytes per element
            uint16_t *depth_data = (uint16_t*)depth_data_bytes;
            
            // Process depth data (example: get center depth in mm)
            int center_idx = (height / 2) * width + (width / 2);
            uint16_t depth_mm = depth_data[center_idx];
            float depth_m = depth_mm / 1000.0f;
            printf("Depth - Center depth: %.3f meters (%.0f mm)\n", depth_m, (float)depth_mm);
        }
    }
    
    if (depth_data_bytes) {
        free(depth_data_bytes); // Mirage allocates this memory
    }
}

void decode_pointcloud_message(mirage_msg *msg) {
    // Read numeric array (automatically gets size from header)
    mirage_read_start(msg);
    int64_t array_type;
    int64_t element_size;
    int64_t array_length;
    uint8_t *pointcloud_data_bytes = nullptr;
    
    mirage_read_numericarray(msg, &array_type, &element_size, &array_length, &pointcloud_data_bytes);
    
    if (array_type == MIRAGE_ARRAY_FLOAT32 && element_size == 4) {
        int width = 1280;
        int height = 720;
        int expected_points = width * height;
        
        if (array_length == expected_points * 3 * 4) { // 3 floats per point, 4 bytes each
            float *pointcloud_data = (float*)pointcloud_data_bytes;
            
            // Process point cloud (example: get center point)
            int center_idx = (height / 2) * width + (width / 2);
            center_idx *= 3; // 3 floats per point
            
            float x = pointcloud_data[center_idx];
            float y = pointcloud_data[center_idx + 1];
            float z = pointcloud_data[center_idx + 2];
            float distance = sqrt(x*x + y*y + z*z);
            
            printf("PointCloud - Center point: X=%.3f, Y=%.3f, Z=%.3f meters\n", x, y, z);
            printf("PointCloud - Distance from origin: %.3f meters\n", distance);
        }
    }
    
    if (pointcloud_data_bytes) {
        free(pointcloud_data_bytes); // Mirage allocates this memory
    }
}

int main() {
    // Example usage with ROS3 subscriber
    rose_node *node = rose_init(0, nullptr, (char*)"realsense_viewer", nullptr, nullptr);
    
    // Create subscribers for all topics
    rose_subscriber *rgb_sub = rose_create_sub(node, (char*)"/camera/rgb", -1, 0, nullptr);
    rose_subscriber *depth_sub = rose_create_sub(node, (char*)"/camera/depth", -1, 0, nullptr);
    rose_subscriber *pointcloud_sub = rose_create_sub(node, (char*)"/camera/pointcloud", -1, 0, nullptr);
    
    mirage_msg *msg = mirage_create(1024 * 1024, nullptr); // 1MB buffer
    
    while (rose_ok(node)) {
        // Check RGB topic
        if (rose_read(rgb_sub, msg) >= 0) {
            decode_rgb_message(msg);
        }
        
        // Check Depth topic
        if (rose_read(depth_sub, msg) >= 0) {
            decode_depth_message(msg);
        }
        
        // Check PointCloud topic
        if (rose_read(pointcloud_sub, msg) >= 0) {
            decode_pointcloud_message(msg);
        }
        
        rose_sleep(0.01); // 10ms sleep
    }
    
    mirage_destroy(&msg, nullptr);
    rose_shutdown(node);
    return 0;
}
```

## Testing the Driver

A comprehensive test script is included to verify the driver functionality:

```bash
# Run the test script
python3 test_realsense_driver.py
```

The test script performs:
- ✅ **Automatic NumPy array decoding validation**
- ✅ **Data type and shape verification**
- ✅ **Pixel value range checking**
- ✅ **Depth validity analysis**
- ✅ **Point cloud quality assessment**
- ✅ **Success rate calculation**

### Test Features

- **Real-time validation**: Tests all three topics simultaneously
- **Statistical analysis**: Calculates valid pixel percentages
- **Performance metrics**: Success rate scoring
- **Automatic cleanup**: Proper resource management
- **Timeout handling**: 30-second safety timeout

## Python Decoding Example

**Note**: Python Mirage automatically decodes numeric arrays to NumPy arrays with correct size information!

```python
import ros3 as rose
import mirage
import numpy as np
import math

# Create node and subscribers
node = rose.Node("realsense_viewer")
rgb_sub = node.subscriber("/camera/rgb")
depth_sub = node.subscriber("/camera/depth")
pointcloud_sub = node.subscriber("/camera/pointcloud")

print("RealSense viewer started. Waiting for messages...")

while node.ok():
    # Process RGB messages
    for msg in rgb_sub:
        # Mirage automatically decodes to NumPy array with correct size!
        decoded = mirage.decode(msg)
        if decoded and len(decoded) > 0:
            rgb_data = decoded[0]
            # rgb_data is already a NumPy array with correct shape!
            if isinstance(rgb_data, np.ndarray):
                # Automatic size detection - no need to manually specify dimensions
                height, width, channels = rgb_data.shape
                print(f"RGB Image: {width}x{height}x{channels}")
                
                # Get first and center pixels
                first_pixel = rgb_data[0, 0, :]
                center_pixel = rgb_data[height//2, width//2, :]
                
                print(f"RGB - First pixel: R={first_pixel[0]}, G={first_pixel[1]}, B={first_pixel[2]}")
                print(f"RGB - Center pixel: R={center_pixel[0]}, G={center_pixel[1]}, B={center_pixel[2]}")
    
    # Process Depth messages
    for msg in depth_sub:
        decoded = mirage.decode(msg)
        if decoded and len(decoded) > 0:
            depth_data = decoded[0]
            # depth_data is already a NumPy array with correct shape!
            if isinstance(depth_data, np.ndarray):
                # Automatic size detection
                height, width = depth_data.shape
                print(f"Depth Image: {width}x{height}")
                
                # Get center depth
                center_depth_mm = depth_data[height//2, width//2]
                center_depth_m = center_depth_mm / 1000.0
                
                print(f"Depth - Center depth: {center_depth_m:.3f} meters ({center_depth_mm:.0f} mm)")
    
    # Process Point Cloud messages
    for msg in pointcloud_sub:
        decoded = mirage.decode(msg)
        if decoded and len(decoded) > 0:
            pc_data = decoded[0]
            # pc_data is already a NumPy array with correct shape!
            if isinstance(pc_data, np.ndarray):
                # Automatic size detection
                height, width, coords = pc_data.shape
                print(f"Point Cloud: {width}x{height}x{coords}")
                
                # Get center point
                center_point = pc_data[height//2, width//2, :]
                x, y, z = center_point
                distance = math.sqrt(x*x + y*y + z*z)
                
                print(f"PointCloud - Center point: X={x:.3f}, Y={y:.3f}, Z={z:.3f} meters")
                print(f"PointCloud - Distance from origin: {distance:.3f} meters")
    
    rose.sleep(0.01)
```

### Python Decoding Benefits

✅ **Automatic NumPy array conversion** - No manual buffer conversion needed  
✅ **Automatic size detection** - Shape information is preserved  
✅ **Type preservation** - Correct data types (uint8, uint16, float32)  
✅ **Simplified code** - No need to manually specify dimensions  
✅ **Error handling** - Built-in type and shape validation  

The Python Mirage library automatically handles the numeric array decoding and converts to properly shaped NumPy arrays!

## Implementation Details

- Uses RealSense2 C++ API for camera access
- Follows ROS3 C-style C++ patterns
- Encodes image data using Mirage binary format
- Handles camera errors and graceful shutdown

## Data Formats

- **RGB**: width×height×3 bytes (RGB8 format)
- **Depth**: width×height×2 bytes (16-bit depth values)
- **Point Cloud**: width×height×12 bytes (XYZ float coordinates, 4 bytes each)

## Error Handling

The driver handles:
- Camera initialization failures
- Frame processing errors
- ROS3 communication errors
- Graceful shutdown on errors

## License

Apache 2.0 (same as ROS3 and Librealsense2)