# Point Cloud Processing with ROS 2 Jazzy and PCL
### Ground Removal, Obstacle Clustering, and Centroid Publishing using Intel RealSense D435I

---

## Overview

This guide walks through building a ROS 2 C++ node that subscribes to point cloud data from a RealSense D435I camera and performs the following processing pipeline:

1. **Voxel grid downsampling** — reduces point density for efficient processing
2. **Statistical outlier removal** — cleans noise from the raw point cloud
3. **Ground plane segmentation** — uses RANSAC to detect and remove the floor
4. **Euclidean cluster extraction** — identifies distinct obstacle clusters
5. **Centroid computation** — calculates the 3D center of each obstacle

The node publishes two output topics: all above-ground points and the centroid of each detected obstacle cluster.

```
/camera/camera/depth/color/points  (input)
        │
        ▼
  Voxel Grid Filter (3cm leaf)
        │
        ▼
  Statistical Outlier Removal
        │
        ▼
  RANSAC Ground Plane Segmentation
        │
        ├──► above_ground_points   (all non-ground points)
        │
        ▼
  Euclidean Cluster Extraction
        │
        ▼
  Centroid Calculation
        │
        └──► obstacle_centroids    (one point per cluster)
```

---

## Prerequisites

| Requirement | Package |
|---|---|
| ROS 2 Jazzy installed and sourced | See main setup guide |
| RealSense ROS 2 wrapper | `ros-jazzy-realsense2-camera` |
| PCL (Point Cloud Library) | `ros-jazzy-pcl-ros` |
| PCL ROS 2 conversions | `ros-jazzy-pcl-conversions` |
| C++ build tools | `build-essential`, `cmake` |

### Install PCL dependencies

```bash
sudo apt install ros-jazzy-pcl-ros -y
sudo apt install ros-jazzy-pcl-conversions -y
```

Verify PCL is available:

```bash
dpkg -l | grep pcl
# Should show libpcl-dev and ros-jazzy-pcl-ros
```

---

## Step 1: Create the ROS 2 Package

Navigate to your workspace `src` directory and create a new package:

```bash
cd ~/your_ws/src
ros2 pkg create --build-type ament_cmake pcl_ros2_package
```

This creates the following structure:

```
pcl_ros2_package/
├── CMakeLists.txt
├── package.xml
└── src/
```

Create the source file location:

```bash
mkdir -p ~/your_ws/src/pcl_ros2_package/src
```

---

## Step 2: Write the CMakeLists.txt

Replace the default `CMakeLists.txt` with the following. This links all required PCL modules, ROS 2 interfaces, and sets up the install target:

```bash
cat > ~/your_ws/src/pcl_ros2_package/CMakeLists.txt << 'EOF'
cmake_minimum_required(VERSION 3.8)
project(pcl_ros2_package)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(PCL REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(pcl_conversions REQUIRED)

include_directories(
  ${PCL_INCLUDE_DIRS}
  ${rclcpp_INCLUDE_DIRS}
  ${sensor_msgs_INCLUDE_DIRS}
  ${pcl_conversions_INCLUDE_DIRS}
)

link_directories(${PCL_LIBRARY_DIRS})
add_definitions(${PCL_DEFINITIONS})

# Add the executable
add_executable(pcl_node src/pcl.cpp)

# Link with ament dependencies
ament_target_dependencies(pcl_node
  rclcpp
  sensor_msgs
  pcl_conversions
)

# Link PCL libraries directly
target_link_libraries(pcl_node
  ${PCL_LIBRARIES}
)

# Install the executable
install(TARGETS pcl_node
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
EOF
```

> **NOTE:** `ament_target_dependencies` is used for ROS 2 packages instead of manual `target_link_libraries` for ROS deps. PCL is linked directly since it is a non-ament CMake package.

---

## Step 3: Write the package.xml

Replace the default `package.xml` with the correct dependencies:

```bash
cat > ~/your_ws/src/pcl_ros2_package/package.xml << 'EOF'
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>pcl_ros2_package</name>
  <version>0.0.1</version>
  <description>Point cloud processing with PCL and ROS 2</description>
  <maintainer email="your@email.com">Your Name</maintainer>
  <license>Apache-2.0</license>

  <buildtool_depend>ament_cmake</buildtool_depend>

  <depend>rclcpp</depend>
  <depend>sensor_msgs</depend>
  <depend>pcl_conversions</depend>
  <depend>pcl_ros</depend>

  <test_depend>ament_lint_auto</test_depend>
  <test_depend>ament_cmake_copyright</test_depend>
  <test_depend>ament_cmake_cpplint</test_depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
EOF
```

---

## Step 4: Write the PCL Node (pcl.cpp)

Create the main C++ source file:

```bash
cat > ~/your_ws/src/pcl_ros2_package/src/pcl.cpp << 'CPPEOF'
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <pcl_conversions/pcl_conversions.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl/filters/extract_indices.h>
#include <pcl/filters/statistical_outlier_removal.h>
#include <pcl/sample_consensus/method_types.h>
#include <pcl/sample_consensus/model_types.h>
#include <pcl/segmentation/sac_segmentation.h>
#include <pcl/segmentation/extract_clusters.h>
#include <pcl/search/kdtree.h>

class PclNode : public rclcpp::Node {
public:
  PclNode() : Node("pcl_node") {
    // Subscribe to RealSense colored point cloud
    subscription_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
      "/camera/camera/depth/color/points", 10,
      std::bind(&PclNode::pointCloudCallback, this, std::placeholders::_1));

    // Publish all above-ground points
    above_ground_publisher_ = this->create_publisher<sensor_msgs::msg::PointCloud2>(
      "above_ground_points", 10);

    // Publish centroids of obstacle clusters
    centroids_publisher_ = this->create_publisher<sensor_msgs::msg::PointCloud2>(
      "obstacle_centroids", 10);

    // Initialise previous ground plane coefficients for temporal smoothing
    previous_coefficients_.reset(new pcl::ModelCoefficients);

    RCLCPP_INFO(this->get_logger(), "PCL ROS2 Node started");
    RCLCPP_INFO(this->get_logger(), "Subscribing to: /camera/camera/depth/color/points");
    RCLCPP_INFO(this->get_logger(), "Publishing to: above_ground_points, obstacle_centroids");
  }

private:
  void pointCloudCallback(const sensor_msgs::msg::PointCloud2::SharedPtr msg) {

    // ---------------------------------------------------------------
    // STEP 1: Convert ROS2 PointCloud2 message to PCL point cloud
    // ---------------------------------------------------------------
    pcl::PointCloud<pcl::PointXYZ>::Ptr cloud(new pcl::PointCloud<pcl::PointXYZ>);
    pcl::fromROSMsg(*msg, *cloud);

    if (cloud->empty()) {
      RCLCPP_WARN(this->get_logger(), "Received empty point cloud, skipping.");
      return;
    }

    // ---------------------------------------------------------------
    // STEP 2: Voxel grid filter — downsample to reduce point density
    // Leaf size of 3cm means one point per 3x3x3cm cube.
    // Smaller = more detail but slower. Larger = faster but coarser.
    // ---------------------------------------------------------------
    pcl::PointCloud<pcl::PointXYZ>::Ptr voxel_filtered_cloud(new pcl::PointCloud<pcl::PointXYZ>);
    pcl::VoxelGrid<pcl::PointXYZ> voxel_filter;
    voxel_filter.setInputCloud(cloud);
    voxel_filter.setLeafSize(0.03f, 0.03f, 0.03f);
    voxel_filter.filter(*voxel_filtered_cloud);

    RCLCPP_DEBUG(this->get_logger(), "Points after voxel filter: %zu", voxel_filtered_cloud->size());

    // ---------------------------------------------------------------
    // STEP 3: Statistical outlier removal — remove noise points
    // Each point is evaluated against its k nearest neighbors.
    // Points whose mean distance is beyond stddev_mult * stddev
    // from the global mean are removed.
    // ---------------------------------------------------------------
    pcl::PointCloud<pcl::PointXYZ>::Ptr filtered_cloud(new pcl::PointCloud<pcl::PointXYZ>);
    pcl::StatisticalOutlierRemoval<pcl::PointXYZ> sor;
    sor.setInputCloud(voxel_filtered_cloud);
    sor.setMeanK(50);           // Number of nearest neighbors to analyse
    sor.setStddevMulThresh(1.0); // Points beyond 1 stddev from mean are removed
    sor.filter(*filtered_cloud);

    RCLCPP_DEBUG(this->get_logger(), "Points after outlier removal: %zu", filtered_cloud->size());

    // ---------------------------------------------------------------
    // STEP 4: RANSAC ground plane segmentation
    // RANSAC randomly samples 3 points, fits a plane, counts inliers
    // within distanceThreshold. Repeats maxIterations times and keeps
    // the plane with the most inliers. This robustly finds the floor
    // even if the camera is tilted or the floor is partially occluded.
    // ---------------------------------------------------------------
    pcl::ModelCoefficients::Ptr coefficients(new pcl::ModelCoefficients);
    pcl::PointIndices::Ptr inliers(new pcl::PointIndices);
    pcl::SACSegmentation<pcl::PointXYZ> seg;
    seg.setOptimizeCoefficients(true);
    seg.setModelType(pcl::SACMODEL_PLANE);
    seg.setMethodType(pcl::SAC_RANSAC);
    seg.setDistanceThreshold(0.03); // Points within 3cm of the plane are inliers
    seg.setMaxIterations(3000);     // More iterations = more accurate but slower
    seg.setInputCloud(filtered_cloud);
    seg.segment(*inliers, *coefficients);

    if (inliers->indices.empty()) {
      RCLCPP_WARN(this->get_logger(), "Could not estimate a ground plane. Skipping frame.");
      return;
    }

    // ---------------------------------------------------------------
    // STEP 5: Temporal smoothing of ground plane coefficients
    // The plane equation is ax + by + cz + d = 0.
    // We blend the new coefficients with the previous ones (70/30)
    // to reduce jitter between frames caused by small estimation errors.
    // ---------------------------------------------------------------
    if (!previous_coefficients_->values.empty()) {
      for (size_t i = 0; i < coefficients->values.size(); ++i) {
        coefficients->values[i] =
          0.7f * previous_coefficients_->values[i] +
          0.3f * coefficients->values[i];
      }
    }
    *previous_coefficients_ = *coefficients;

    // ---------------------------------------------------------------
    // STEP 6: Extract non-ground points (setNegative = true removes
    // the inliers and keeps everything else)
    // ---------------------------------------------------------------
    pcl::ExtractIndices<pcl::PointXYZ> extract;
    extract.setInputCloud(filtered_cloud);
    extract.setIndices(inliers);
    extract.setNegative(true);
    extract.filter(*filtered_cloud);

    RCLCPP_DEBUG(this->get_logger(), "Above-ground points: %zu", filtered_cloud->size());

    // ---------------------------------------------------------------
    // STEP 7: Publish all above-ground points
    // ---------------------------------------------------------------
    sensor_msgs::msg::PointCloud2 above_ground_msg;
    pcl::toROSMsg(*filtered_cloud, above_ground_msg);
    above_ground_msg.header = msg->header;
    above_ground_publisher_->publish(above_ground_msg);

    // ---------------------------------------------------------------
    // STEP 8: Euclidean cluster extraction
    // Groups nearby points into clusters. Points within clusterTolerance
    // of each other are assigned to the same cluster.
    // Clusters smaller than minClusterSize are discarded as noise.
    // ---------------------------------------------------------------
    pcl::search::KdTree<pcl::PointXYZ>::Ptr tree(new pcl::search::KdTree<pcl::PointXYZ>);
    tree->setInputCloud(filtered_cloud);

    std::vector<pcl::PointIndices> cluster_indices;
    pcl::EuclideanClusterExtraction<pcl::PointXYZ> ec;
    ec.setClusterTolerance(0.05);  // 5cm — points within 5cm are grouped together
    ec.setMinClusterSize(100);     // Ignore clusters with fewer than 100 points
    ec.setMaxClusterSize(25000);   // Ignore clusters larger than 25000 points
    ec.setSearchMethod(tree);
    ec.setInputCloud(filtered_cloud);
    ec.extract(cluster_indices);

    RCLCPP_DEBUG(this->get_logger(), "Clusters found: %zu", cluster_indices.size());

    // ---------------------------------------------------------------
    // STEP 9: Compute centroid of each cluster and publish
    // The centroid is the average (x, y, z) of all points in a cluster.
    // It represents the approximate 3D position of each obstacle.
    // ---------------------------------------------------------------
    pcl::PointCloud<pcl::PointXYZ>::Ptr centroids(new pcl::PointCloud<pcl::PointXYZ>);

    for (const auto &cluster : cluster_indices) {
      pcl::PointXYZ centroid;
      centroid.x = 0.0f;
      centroid.y = 0.0f;
      centroid.z = 0.0f;

      for (const auto &index : cluster.indices) {
        centroid.x += filtered_cloud->points[index].x;
        centroid.y += filtered_cloud->points[index].y;
        centroid.z += filtered_cloud->points[index].z;
      }

      const float n = static_cast<float>(cluster.indices.size());
      centroid.x /= n;
      centroid.y /= n;
      centroid.z /= n;

      centroids->points.push_back(centroid);
    }

    sensor_msgs::msg::PointCloud2 centroids_msg;
    pcl::toROSMsg(*centroids, centroids_msg);
    centroids_msg.header = msg->header;
    centroids_publisher_->publish(centroids_msg);

    RCLCPP_INFO(this->get_logger(), "Obstacles detected: %zu", centroids->points.size());
  }

  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr subscription_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr above_ground_publisher_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr centroids_publisher_;
  pcl::ModelCoefficients::Ptr previous_coefficients_;
};

int main(int argc, char * argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<PclNode>());
  rclcpp::shutdown();
  return 0;
}
CPPEOF
```

---

## Step 5: Build the Package

```bash
cd ~/your_ws
colcon build --packages-select pcl_ros2_package
source install/setup.bash
```

Expected output:

```
Starting >>> pcl_ros2_package
Finished <<< pcl_ros2_package [~30s]
Summary: 1 package finished
```

> **NOTE:** The first build takes longer (~30s) because PCL is a large library. Subsequent builds are faster.

If the build fails with missing headers, install PCL dev libraries:

```bash
sudo apt install libpcl-dev -y
cd ~/your_ws && colcon build --packages-select pcl_ros2_package
```

---

## Step 6: Running the System

You need both the RealSense camera node and the PCL node running. Use two terminals or run them with `&`:

### Terminal 1 — Launch RealSense with point cloud enabled

```bash
ros2 launch realsense2_camera rs_launch.py \
  enable_color:=true \
  enable_depth:=true \
  pointcloud.enable:=true \
  align_depth.enable:=true \
  enable_sync:=true \
  rgb_camera.color_profile:=640x480x30 \
  depth_module.depth_profile:=640x480x30
```

### Terminal 2 — Run the PCL processing node

```bash
source ~/your_ws/install/setup.bash
ros2 run pcl_ros2_package pcl_node
```

You should see output like:

```
[pcl_node]: PCL ROS2 Node started
[pcl_node]: Subscribing to: /camera/camera/depth/color/points
[pcl_node]: Publishing to: above_ground_points, obstacle_centroids
[pcl_node]: Obstacles detected: 3
[pcl_node]: Obstacles detected: 3
[pcl_node]: Obstacles detected: 4
```

### Single terminal alternative

```bash
pkill -f realsense2_camera_node; sleep 2
ros2 launch realsense2_camera rs_launch.py \
  enable_color:=true enable_depth:=true \
  pointcloud.enable:=true align_depth.enable:=true \
  enable_sync:=true &
sleep 6
ros2 run pcl_ros2_package pcl_node
```

---

## Step 7: Verify Output Topics

```bash
ros2 topic list | grep -E "above_ground|centroids|points"
```

Expected:

```
/above_ground_points
/camera/camera/depth/color/points
/obstacle_centroids
```

Check data is flowing:

```bash
ros2 topic hz /above_ground_points
ros2 topic hz /obstacle_centroids
```

Echo centroid positions:

```bash
ros2 topic echo /obstacle_centroids
```

---

## Step 8: Visualize in RViz2

```bash
rviz2
```

In RViz2, add the following displays:

| Display Type | Topic | Notes |
|---|---|---|
| PointCloud2 | `/camera/camera/depth/color/points` | Raw input — colored point cloud |
| PointCloud2 | `/above_ground_points` | Filtered output — everything above floor |
| PointCloud2 | `/obstacle_centroids` | One point per obstacle cluster |

**Recommended RViz2 settings for point clouds:**
- Set **Fixed Frame** to `camera_depth_optical_frame`
- Set **Size** to `0.05` for centroids so they are visible as larger points
- Set **Color Transformer** to `FlatColor` for centroids and pick a bright color

---

## Code Explanation

### Processing Pipeline in Detail

**Voxel Grid Filter**

Reduces the raw point cloud (typically 300,000+ points from the D435I) to a manageable size by replacing all points within each 3x3x3cm cube with a single representative point. This dramatically speeds up all downstream processing without significant loss of spatial information for obstacle detection.

```cpp
voxel_filter.setLeafSize(0.03f, 0.03f, 0.03f); // 3cm voxels
```

Tuning: decrease leaf size for more detail (slower), increase for faster processing (coarser).

**Statistical Outlier Removal**

For each point, computes the mean distance to its k nearest neighbors. Points whose mean distance is more than `stddev_mult` standard deviations above the global mean are considered outliers and removed. This eliminates the random noise spikes common in depth camera data.

```cpp
sor.setMeanK(50);            // Analyse 50 nearest neighbors per point
sor.setStddevMulThresh(1.0); // Remove points > 1 stddev above mean distance
```

Tuning: increase `MeanK` for more aggressive denoising (slower), decrease `StddevMulThresh` to remove more points.

**RANSAC Ground Plane Segmentation**

Random Sample Consensus (RANSAC) robustly fits a plane model to the point cloud even in the presence of outliers. The algorithm:
1. Randomly selects 3 points and fits a plane
2. Counts how many points fall within `distanceThreshold` of that plane (inliers)
3. Repeats `maxIterations` times
4. Keeps the plane with the most inliers

```cpp
seg.setDistanceThreshold(0.03); // Points within 3cm of plane = ground
seg.setMaxIterations(3000);     // More iterations = more accurate
```

Tuning: increase `distanceThreshold` if the ground is not being fully removed (uneven floor), decrease if non-ground points are being incorrectly removed.

**Temporal Smoothing**

Blends the current ground plane coefficients with the previous frame's coefficients using a 70/30 weighted average. This reduces jitter in the plane estimation caused by small frame-to-frame variations, producing smoother above-ground segmentation.

```cpp
coefficients->values[i] = 0.7f * previous + 0.3f * current;
```

Tuning: increase the weight of `current` (e.g. 0.5/0.5) for faster response to ground plane changes, increase the weight of `previous` for more stability.

**Euclidean Cluster Extraction**

Groups nearby points into clusters using a KD-tree for efficient nearest neighbor search. Two points belong to the same cluster if their distance is less than `clusterTolerance`. Small clusters (below `minClusterSize`) are discarded as noise.

```cpp
ec.setClusterTolerance(0.05); // 5cm — gap between clusters
ec.setMinClusterSize(100);    // Ignore tiny clusters (noise)
ec.setMaxClusterSize(25000);  // Ignore enormous clusters (walls/ceiling)
```

Tuning: increase `clusterTolerance` to merge nearby objects into one cluster, decrease to separate closely spaced objects. Adjust `minClusterSize` based on how far away obstacles are (distant objects produce fewer points).

**Centroid Calculation**

Computes the arithmetic mean of all (x, y, z) coordinates in each cluster. The result is a single point representing the approximate 3D center of each obstacle in the `camera_depth_optical_frame` coordinate frame.

---

## Tuning Parameters

| Parameter | Default | Effect of Increasing | Effect of Decreasing |
|---|---|---|---|
| `voxel leaf size` | 0.03m | Faster, coarser | Slower, more detail |
| `MeanK` (outlier) | 50 | More aggressive denoising | Less denoising |
| `StddevMulThresh` | 1.0 | Keep more points | Remove more points |
| `distanceThreshold` | 0.03m | Remove more ground | Risk leaving ground points |
| `maxIterations` | 3000 | More accurate plane | Slower |
| `clusterTolerance` | 0.05m | Merge nearby objects | Split single objects |
| `minClusterSize` | 100 | Ignore smaller objects | More noise clusters |
| `maxClusterSize` | 25000 | Include large objects | Miss large obstacles |
| Temporal blend (prev) | 0.7 | More stable, slower response | Faster response, more jitter |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `Could not estimate a ground plane` every frame | Floor may not be visible. Tilt the camera down, or reduce `distanceThreshold` |
| No clusters detected | Try reducing `minClusterSize` or increasing `clusterTolerance`. Check `above_ground_points` has data first |
| Too many false clusters | Increase `minClusterSize` or decrease `clusterTolerance` |
| Processing too slow | Increase voxel leaf size to 0.05m or 0.1m. Reduce `maxIterations` to 1000 |
| Build error: PCL headers not found | Run `sudo apt install libpcl-dev ros-jazzy-pcl-ros ros-jazzy-pcl-conversions` |
| `/above_ground_points` topic empty | Confirm `/camera/camera/depth/color/points` is publishing: `ros2 topic hz /camera/camera/depth/color/points` |
| Ground not fully removed | Increase `distanceThreshold` to 0.05 or 0.08 for uneven surfaces |
| Obstacles being merged into one cluster | Decrease `clusterTolerance` from 0.05 to 0.03 |

---

## Published Topics Summary

| Topic | Type | Description |
|---|---|---|
| `/above_ground_points` | `sensor_msgs/msg/PointCloud2` | All non-ground points after filtering and ground removal |
| `/obstacle_centroids` | `sensor_msgs/msg/PointCloud2` | One XYZ point per detected obstacle cluster |

---

## Next Steps

- **Fuse with ArUco** — combine centroid positions with ArUco marker detections to identify and localize tagged obstacles
- **Add bounding boxes** — use `pcl::getMinMax3D` on each cluster to compute 3D bounding boxes and publish as `visualization_msgs/msg/MarkerArray` for RViz2
- **Distance filtering** — add a `pcl::PassThrough` filter before clustering to ignore points beyond a certain range (e.g. beyond 3m)
- **Height filtering** — add a second `PassThrough` on the Z axis to ignore points above a certain height (e.g. ceiling)
- **Object tracking** — associate clusters across frames by matching centroids to track moving obstacles over time
- **Record to rosbag** — record `/above_ground_points` and `/obstacle_centroids` alongside the raw point cloud for offline analysis
