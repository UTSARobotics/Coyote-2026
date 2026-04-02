# Coyote-2026 Robotics System

## Table of Contents
- [Kira KV260 Initial Setup](#kira-kv260-initial-setup)
- [System Startup Guide](#system-startup-guide)
- [Realsense D345 Setup](#realsense-d345-setup)
- [Motor Control Firmware](#motor-control-firmware)
- [ArUco ROS2 Package](#aruco-ros2-package)
- [PCL ROS2 Package](#pcl-ros2-package)
- [Running realsense-aruco.py](#running-realsense-aruco.py)

## Kira KV260 Initial Setup 

Follow the instructions detailed here: https://xilinx.github.io/kria-apps-docs/kv260/2022.1/linux_boot/ubuntu_22_04/build/html/docs/sdcard.html

## System Startup Guide

Follow these steps to start the Coyote-2026 system with proper RealSense camera configuration:

### 1. Launch RViz
First, open RViz for visualization:
```bash
rviz2
```

### 2. Start RealSense Camera Node
Launch the RealSense camera node in a new terminal:
```bash
ros2 run realsense2_camera realsense2_camera_node
```

### 3. Configure Camera Settings with rqt_reconfigure
Open the dynamic reconfigure tool:
```bash
ros2 run rqt_reconfigure rqt_reconfigure
```

Configure the following settings:

1. **Enable Decimation Filter**
   - Set `enable_decimation_filter` to `True`
   - Set `decimation_magnitude` to `8`

2. **Enable PointCloud Neon**
   - Set `enable_pointcloud_neon` to `True`

3. **Camera Stream Configuration**
   - Ensure only `color` and `depth` cameras are enabled
   - Toggle them if they are already enabled to ensure proper initialization

### 4. Verify System Status
Check that all nodes are running and topics are publishing:
```bash
ros2 node list
ros2 topic list
```

### 5. Start Additional Processing Nodes (Optional)
If needed, launch additional processing nodes:
```bash
# Start ArUco detection
ros2 run ros2_aruco aruco_node

# Start PCL processing
ros2 run pcl_ros2_package pcl_node
```

## Realsense D345 Setup

NOTE: This setup is for Linux only. 

Download the precompiled SDK here: https://github.com/realsenseai/librealsense/blob/master/doc/distribution_linux.md and follow the instructions for setup. 

## Motor Control Firmware

The motor control firmware is designed for differential drive robot control using PWM signals. It interfaces with Electronic Speed Controllers (ESCs) and supports Ghost protocol for radio control input.

### Hardware Setup
- **PWM Pins**: GPIO 18 (left motor), GPIO 19 (right motor)
- **UART**: UART2 at 420000 baud (RX: GPIO 16, TX: GPIO 17)
- **PWM Frequency**: 50Hz (standard for RC servos/ESCs)

### Key Features
- **Differential Drive Mixing**: Converts throttle and steering inputs to individual motor speeds
- **ESC Arming**: Automatic ESC arming sequence (1450μs pulse for 10 seconds)
- **Pulse Width Range**: 1000-2000μs (standard RC servo range)
- **Deadband Filtering**: Ignores small input fluctuations for smoother control
- **CRC Validation**: CRC8-DVB-S2 error checking for Ghost protocol frames

### Input Processing
- **Input Range**: 346-3622 (12-bit ADC range)
- **Center Position**: 1984
- **Deadband**: ±40 around center (±0.05 normalized)
- **Normalized Output**: -1.0 to +1.0 range

### Usage
1. Connect motors to specified GPIO pins
2. Connect radio receiver via UART2
3. Power on the system - ESCs will arm automatically
4. Use radio controller to send throttle (channel 1) and steering (channel 2) inputs

### Protocol Details
The firmware expects Ghost protocol frames with the following structure:
- `[ADDR][LEN][TYPE][PAYLOAD...][CRC]`
- Payload contains channel data in 12-bit format
- Channels 1-4 are extracted from the payload for control

## Realsense D345 Setup

NOTE: This setup is for Linux only. 

Download the precompiled SDK here: https://github.com/realsenseai/librealsense/blob/master/doc/distribution_linux.md and follow the instructions for setup. 

## Running realsense-aruco.py

The `realsense-aruco.py` uses OpenCV object detction (utilizing the Realsense camera) to determine if an 6x6 [ArUco](https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html) is within frame and calculates the distance of the ArUco to the camera.    

Download the python dependencies for the Realsense viewer https://github.com/realsenseai/librealsense/blob/master/readme.md#install.

As well as, the OpenCV dependencies https://docs.opencv.org/4.x/db/dd1/tutorial_py_pip_install.html.

Finally, connect the realsense viewer to your machine and simply run
```python
python3 realsense-aruco.py
```

## ArUco ROS2 Package

The ArUco ROS2 package provides marker detection and pose estimation using OpenCV's ArUco module integrated with ROS2. This package is designed to work with various camera sources including Intel RealSense depth cameras.

### Package Overview
- **ROS2 Wrapper**: Bridges OpenCV ArUco detection with ROS2 messaging
- **Marker Detection**: Supports multiple ArUco dictionary types (4x4, 5x5, 6x6, 7x7)
- **Pose Estimation**: Provides 6-DOF pose information for detected markers
- **Camera Integration**: Works with calibrated cameras for accurate 3D positioning

### Key Features
- **Multiple Dictionary Support**: DICT_4X4_50, DICT_5X5_250, DICT_6X6_250, etc.
- **ROS2 Integration**: Publishes marker poses as ROS2 topics
- **Configuration**: Flexible parameter configuration via YAML files
- **Visualization**: Compatible with RViz2 for 3D visualization

### ROS2 API

#### Subscriptions
- `/camera/image_raw` (`sensor_msgs.msg.Image`) - Input image stream for marker detection
- `/camera/camera_info` (`sensor_msgs.msg.CameraInfo`) - Camera calibration information

#### Published Topics
- `/aruco_poses` (`geometry_msgs.msg.PoseArray`) - 3D poses of detected markers (RViz compatible)
- `/aruco_markers` (`ros2_aruco_interfaces.msg.ArucoMarkers`) - Marker IDs with corresponding poses

#### Parameters
- `marker_size` (float): Physical size of markers in meters (default: 0.0625)
- `aruco_dictionary_id` (string): ArUco dictionary type (default: "DICT_5X5_250")
- `image_topic` (string): Image topic to subscribe to (default: "/camera/image_raw")
- `camera_info_topic` (string): Camera info topic (default: "/camera/camera_info")
- `camera_frame` (string): Camera optical frame ID

### Installation & Dependencies

#### Required Packages
```bash
pip3 install opencv-contrib-python transforms3d
sudo apt install ros-jazzy-desktop ros-jazzy-tf-transformations ros-jazzy-cv-bridge
```

#### Building the Package
```bash
cd ~/your_workspace
colcon build --symlink-install
source install/setup.bash
```

### Usage

#### Running the ArUco Node
```bash
# Using launch file (recommended)
ros2 launch ros2_aruco aruco_recognition.launch.py

# Running as standalone node
ros2 run ros2_aruco aruco_node

# With custom parameters
ros2 run ros2_aruco aruco_node --ros-args -p marker_size:=0.05 -p aruco_dictionary_id:=DICT_4X4_50
```

#### Generating ArUco Markers
```bash
# Generate a marker image
ros2 run ros2_aruco aruco_generate_marker --id 1 --size 200 --dictionary DICT_5X5_250

# Generate multiple markers
ros2 run ros2_aruco aruco_generate_marker --id 1 --size 200 --dictionary DICT_5X5_250
ros2 run ros2_aruco aruco_generate_marker --id 2 --size 200 --dictionary DICT_5X5_250
```

### Configuration
The package includes a default configuration file at `config/aruco_parameters.yaml`:

```yaml
/aruco_node:
  ros__parameters:
    marker_size: 0.055
    aruco_dictionary_id: DICT_5X5_250
    image_topic: /image_raw
    camera_info_topic: /camera_info
```

### RealSense Integration
For Intel RealSense D435I camera integration, use the following launch configuration:

```python
# Example launch file snippet
aruco_node = Node(
    package='ros2_aruco',
    executable='aruco_node',
    name='aruco_node',
    parameters=[{
        'marker_size': 0.03,
        'aruco_dictionary_id': 'DICT_4X4_50',
        'image_topic': '/camera/camera/color/image_raw',
        'camera_info_topic': '/camera/camera/color/camera_info',
    }],
)
```

### Visualization with RViz2
Add these displays to visualize ArUco detection:
- **Image**: `/camera/camera/color/image_raw` (RGB feed)
- **PoseArray**: `/aruco_poses` (3D marker poses)
- **TF**: All coordinate frames

### Troubleshooting
- **No markers detected**: Verify marker size parameter matches physical marker size
- **Pose estimation inaccurate**: Ensure proper camera calibration
- **OpenCV version issues**: Use `opencv-contrib-python==4.10.0.84` for best compatibility
- **Topic connection issues**: Verify topic names match between camera and ArUco node parameters

### Available ArUco Dictionaries
- `DICT_4X4_100`, `DICT_4X4_1000`, `DICT_4X4_250`, `DICT_4X4_50`
- `DICT_5X5_100`, `DICT_5X5_1000`, `DICT_5X5_250`, `DICT_5X5_50`
- `DICT_6X6_100`, `DICT_6X6_1000`, `DICT_6X6_250`, `DICT_6X6_50`
- `DICT_7X7_100`, `DICT_7X7_1000`, `DICT_7X7_250`, `DICT_7X7_50`
- `DICT_ARUCO_ORIGINAL`

For complete setup instructions including RealSense D435I integration, refer to the detailed setup guide.

## PCL ROS2 Package

The PCL ROS2 package provides real-time point cloud processing for obstacle detection and environment mapping using the Point Cloud Library (PCL) integrated with ROS2. This package is designed to work with depth cameras like the Intel RealSense D435I.

### Package Overview
- **Language**: C++17 with ROS2
- **Processing Pipeline**: Voxel filtering → Outlier removal → Ground plane segmentation → Obstacle clustering → Centroid extraction
- **Real-time Performance**: Optimized for real-time robotics applications
- **ROS2 Integration**: Full ROS2 topic interface with proper message headers

### Key Features
- **Voxel Grid Downsampling**: Reduces point density for efficient processing (3cm default resolution)
- **Statistical Outlier Removal**: Cleans noise from depth camera data
- **RANSAC Ground Plane Segmentation**: Robustly detects and removes floor/ground points
- **Euclidean Cluster Extraction**: Identifies distinct obstacle clusters
- **Centroid Computation**: Calculates 3D center positions of obstacles
- **Temporal Smoothing**: Reduces jitter in ground plane estimation across frames

### ROS2 API

#### Subscriptions
- `/camera/camera/depth/color/points` (`sensor_msgs/msg/PointCloud2`) - Input colored point cloud from RealSense camera

#### Published Topics
- `/above_ground_points` (`sensor_msgs/msg/PointCloud2`) - All points above the detected ground plane (filtered and cleaned)
- `/obstacle_centroids` (`sensor_msgs/msg/PointCloud2`) - 3D centroid positions of detected obstacle clusters

### Processing Pipeline Details

```
Input: /camera/camera/depth/color/points (300K+ points)
       │
       ▼ Voxel Grid Filter (3cm leaf size)
       │ Reduces to ~30K points for efficient processing
       ▼
       │ Statistical Outlier Removal (k=50, stddev=1.0)
       │ Removes noise spikes and invalid depth measurements
       ▼
       │ RANSAC Ground Plane Segmentation (3000 iterations, 3cm threshold)
       │ Detects floor plane and separates ground from obstacles
       ├──► /above_ground_points (all non-ground points)
       │
       ▼ Euclidean Cluster Extraction (5cm tolerance, 100-25000 points)
       │ Groups nearby points into distinct obstacle clusters
       ▼
       │ Centroid Calculation (arithmetic mean of cluster points)
       │ Computes 3D center position for each obstacle
       └──► /obstacle_centroids (one XYZ point per obstacle)
```

### Installation & Dependencies

#### Required Packages
```bash
# ROS2 and PCL dependencies
sudo apt install ros-jazzy-desktop ros-jazzy-pcl-ros ros-jazzy-pcl-conversions libpcl-dev

# Build tools
sudo apt install build-essential cmake
```

#### Building the Package
```bash
cd ~/your_workspace
colcon build --packages-select pcl_ros2_package
source install/setup.bash
```

### Usage

#### Running the PCL Node
```bash
# Launch RealSense camera with point cloud enabled
ros2 launch realsense2_camera rs_launch.py \
  enable_color:=true \
  enable_depth:=true \
  pointcloud.enable:=true \
  align_depth.enable:=true \
  enable_sync:=true

# Run PCL processing node
ros2 run pcl_ros2_package pcl_node
```

#### Single Terminal Launch
```bash
# Kill any existing nodes
pkill -f realsense2_camera_node; sleep 2

# Launch camera and PCL processing
ros2 launch realsense2_camera rs_launch.py \
  enable_color:=true enable_depth:=true \
  pointcloud.enable:=true align_depth.enable:=true \
  enable_sync:=true & sleep 6
ros2 run pcl_ros2_package pcl_node
```

### Configuration Parameters

The PCL node uses the following default processing parameters:

| Parameter | Default Value | Description |
|----------|---------------|-------------|
| Voxel leaf size | 0.03m (3cm) | Point cloud downsampling resolution |
| Outlier removal k | 50 | Number of neighbors for statistical analysis |
| Outlier stddev threshold | 1.0 | Standard deviation multiplier for outlier detection |
| RANSAC iterations | 3000 | Maximum iterations for ground plane fitting |
| RANSAC distance threshold | 0.03m (3cm) | Maximum distance from plane to be considered inlier |
| Cluster tolerance | 0.05m (5cm) | Maximum distance between points in same cluster |
| Minimum cluster size | 100 points | Minimum points to consider as valid obstacle |
| Maximum cluster size | 25000 points | Maximum points to consider as single obstacle |
| Temporal smoothing | 70% previous, 30% current | Ground plane coefficient blending |

### Visualization with RViz2

Add these displays to visualize the PCL processing pipeline:

1. **Raw Input**: `/camera/camera/depth/color/points` (colored point cloud)
2. **Filtered Output**: `/above_ground_points` (all non-ground points)
3. **Obstacle Centroids**: `/obstacle_centroids` (one point per obstacle)

**Recommended RViz2 Settings:**
- **Fixed Frame**: `camera_depth_optical_frame`
- **Centroid Size**: 0.05 (make centroids visible as larger points)
- **Centroid Color**: Bright color (e.g., red) with FlatColor transformer

### Topic Monitoring

```bash
# Check if topics are publishing
ros2 topic list | grep -E "above_ground|centroids|points"

# Monitor publishing rates
ros2 topic hz /above_ground_points
ros2 topic hz /obstacle_centroids

# View centroid data
ros2 topic echo /obstacle_centroids
```

### Performance Tuning

#### For Faster Processing
```cpp
// Increase voxel grid size (coarser resolution)
voxel_filter.setLeafSize(0.05f, 0.05f, 0.05f); // 5cm instead of 3cm

// Reduce RANSAC iterations
seg.setMaxIterations(1000); // Instead of 3000

// Increase cluster tolerance
 ec.setClusterTolerance(0.1); // 10cm instead of 5cm
```

#### For More Detailed Detection
```cpp
// Decrease voxel grid size (finer resolution)
voxel_filter.setLeafSize(0.01f, 0.01f, 0.01f); // 1cm for close-range scanning

// Increase RANSAC iterations for better plane fitting
seg.setMaxIterations(5000);

// Decrease cluster tolerance for better object separation
 ec.setClusterTolerance(0.03); // 3cm for small objects
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| `Could not estimate a ground plane` | Ensure floor is visible, reduce RANSAC distance threshold, or tilt camera down |
| No clusters detected | Reduce `minClusterSize` (e.g., 50), increase `clusterTolerance` (e.g., 0.08) |
| Too many false clusters | Increase `minClusterSize` (e.g., 200), decrease `clusterTolerance` (e.g., 0.03) |
| Slow processing | Increase voxel leaf size (e.g., 0.05), reduce RANSAC iterations (e.g., 1000) |
| Ground not fully removed | Increase RANSAC distance threshold (e.g., 0.05) for uneven surfaces |
| Obstacles merged together | Decrease cluster tolerance (e.g., 0.03) for better separation |
| Build errors | Ensure all dependencies installed: `sudo apt install libpcl-dev ros-jazzy-pcl-ros ros-jazzy-pcl-conversions` |

### Integration with Other Components

#### ArUco Marker Fusion
Combine PCL obstacle centroids with ArUco marker detections:

```python
# Subscribe to both topics
aruco_sub = create_subscription(ArucoMarkers, '/aruco_markers', aruco_callback)
centroids_sub = create_subscription(PointCloud2, '/obstacle_centroids', centroids_callback)

# Associate markers with obstacles based on proximity
for marker in aruco_markers:
    for centroid in obstacle_centroids:
        distance = math.sqrt((marker.x - centroid.x)**2 + (marker.y - centroid.y)**2)
        if distance < 0.2:  # Within 20cm
            tagged_obstacles.append((marker.id, centroid))
```

#### Navigation Integration
Use obstacle centroids for path planning:

```python
# Convert centroids to navigation costmap
for centroid in obstacle_centroids:
    # Add obstacle to costmap at (centroid.x, centroid.y)
    costmap.set_cost(centroid.x, centroid.y, LETHAL_OBSTACLE)
```

### Advanced Features

#### Bounding Box Calculation
Extend the node to publish 3D bounding boxes:

```cpp
// Add to cluster processing loop
pcl::PointXYZ min_pt, max_pt;
pcl::getMinMax3D(*cluster_cloud, min_pt, max_pt);

// Publish as visualization_msgs/msg/Marker
visualization_msgs::msg::Marker box_marker;
box_marker.type = visualization_msgs::msg::Marker::CUBE;
box_marker.pose.position.x = (min_pt.x + max_pt.x) / 2;
box_marker.pose.position.y = (min_pt.y + max_pt.y) / 2;
box_marker.pose.position.z = (min_pt.z + max_pt.z) / 2;
box_marker.scale.x = max_pt.x - min_pt.x;
box_marker.scale.y = max_pt.y - min_pt.y;
box_marker.scale.z = max_pt.z - min_pt.z;
```

#### Distance Filtering
Add range-based filtering:

```cpp
// Add PassThrough filter before clustering
pcl::PassThrough<pcl::PointXYZ> pass;
pass.setInputCloud(filtered_cloud);
pass.setFilterFieldName("z");
pass.setFilterLimits(0.1, 3.0); // Only keep points 10cm-3m from camera
pass.filter(*filtered_cloud);
```

#### Object Tracking
Implement temporal association of clusters:

```cpp
// Store previous frame centroids and match to current frame
std::vector<ObstacleTrack> tracks;
for (auto &current_centroid : current_centroids) {
    for (auto &track : tracks) {
        float dist = distance(current_centroid, track.last_position);
        if (dist < tracking_threshold) {
            track.update(current_centroid);
            break;
        }
    }
}
```

### Performance Characteristics

| Resolution | Input Points | Output Points | Processing Time | Frame Rate |
|------------|--------------|---------------|----------------|------------|
| 640×480 | ~300,000 | ~30,000 | ~50ms | ~20Hz |
| 480×270 | ~150,000 | ~15,000 | ~30ms | ~30Hz |
| 320×240 | ~75,000 | ~7,500 | ~20ms | ~50Hz |

*Note: Performance measured on Intel i7-8700K with RealSense D435I*

### Applications

- **Autonomous Navigation**: Obstacle detection and avoidance
- **Object Recognition**: Pre-processing for machine learning pipelines
- **Environment Mapping**: 3D scene reconstruction and SLAM
- **Robotics Research**: Experimental platform for point cloud algorithms
- **Industrial Automation**: Object detection in manufacturing environments

For complete setup instructions and advanced configuration, refer to the detailed PCL ROS2 processing guide.

