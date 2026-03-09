# ArUco Marker Detection with ROS 2 Jazzy + Intel RealSense D435I
### Setup Guide for Ubuntu 24.04 (Noble) — March 2026

---

## Overview

This guide walks through setting up ArUco marker detection in ROS 2 Jazzy using an Intel RealSense D435I depth camera on Ubuntu 24.04. All steps in this guide have been verified on real hardware.

The D435I provides RGB, depth, infrared stereo, and IMU streams — all exposed as ROS 2 topics — giving you much more accurate 3D pose estimation than a basic USB webcam.

**What you get with the D435I over a USB webcam:**
- Accurate depth per pixel — no fake calibration file needed
- Aligned depth-to-color frames
- Colored point cloud
- Infrared stereo streams (infra1 + infra2)
- Built-in IMU — accelerometer + gyroscope (the "I" in D435I)
- Hardware-synced streams
- Real camera intrinsics published automatically

---

## System Requirements

| Component | Verified Version |
|---|---|
| Operating System | Ubuntu 24.04 LTS (Noble Numbat) |
| ROS 2 Distribution | Jazzy Jalisco |
| Python | 3.12 |
| Camera | Intel RealSense D435I |
| USB Port | **USB 3.0 or higher required** (blue port) |
| librealsense2 | 2.56.4 |
| RealSense ROS wrapper | 4.56.4 |
| Camera Firmware | 5.17.0.10 |

> **CRITICAL:** Always plug the D435I into a **USB 3.0 or higher (blue) port**. USB 2.x cannot sustain the bandwidth for multiple streams and will cause frame corruption and overflow errors. Confirm `Usb Type Descriptor: 3.2` in `rs-enumerate-devices` output.

---

## Step 1: Set Up ROS 2 Jazzy Repository

Skip this step if you already have ROS 2 Jazzy installed.

### 1.1 Clean Up Old Repos

```bash
sudo rm -f /etc/apt/sources.list.d/ros2.list
sudo rm -f /etc/apt/sources.list.d/ros2.sources
```

### 1.2 Add Jazzy Repository

```bash
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu noble main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
```

### 1.3 Install ROS 2 Core Packages

```bash
sudo apt install ros-jazzy-desktop
sudo apt install ros-jazzy-tf-transformations
sudo apt install ros-jazzy-cv-bridge
sudo apt install ros-jazzy-vision-opencv
sudo apt install python3-opencv python3-numpy
```

---

## Step 2: Install RealSense SDK and ROS 2 Wrapper

Remove the old `usb_cam` driver — the RealSense has its own ROS 2 node:

```bash
sudo apt remove ros-jazzy-usb-cam -y
```

Install librealsense2 and the ROS 2 wrapper:

```bash
sudo apt install ros-jazzy-librealsense2* -y
sudo apt install ros-jazzy-realsense2-camera -y
sudo apt install ros-jazzy-realsense2-description -y
```

Plug in your D435I to a USB 3.0 port, then verify the SDK sees it:

```bash
source /opt/ros/jazzy/setup.bash
rs-enumerate-devices
```

Confirm the output shows:
- Your device name and serial number
- `Usb Type Descriptor: 3.2` — if this shows 2.x, switch USB ports
- Stream profiles for Stereo Module, RGB Camera, and Motion Module

---

## Step 3: Fix OpenCV for ArUco

The apt OpenCV 4.6 on Ubuntu 24.04 has a broken ArUco `detectMarkers` (causes segfaults). Install OpenCV 4.10 via pip:

```bash
pip3 uninstall opencv-contrib-python opencv-python -y --break-system-packages 2>/dev/null
pip3 install opencv-contrib-python==4.10.0.84 --break-system-packages
```

Verify the correct version is loading and ArUco works:

```bash
python3 -c "
import sys
sys.path.insert(0, '/home/$USER/.local/lib/python3.12/site-packages')
import cv2, numpy as np
print('OpenCV version:', cv2.__version__)
print('OpenCV location:', cv2.__file__)
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
detector = cv2.aruco.ArucoDetector(dictionary, cv2.aruco.DetectorParameters())
img = np.zeros((480, 640), dtype=np.uint8)
corners, ids, rejected = detector.detectMarkers(img)
print('ArUco OK!')
"
```

Expected output:
```
OpenCV version: 4.10.0
OpenCV location: /home/<user>/.local/lib/python3.12/site-packages/cv2/__init__.py
ArUco OK!
```

> **NOTE:** The version string shows `4.10.0` not `4.10.0.84` — this is normal. What matters is the location shows `.local/lib/python3.12/site-packages`, confirming it is the pip version not the broken apt one.

---

## Step 4: Create ROS 2 Workspace and Clone ArUco Package

```bash
mkdir -p ~/your_ws/src
cd ~/your_ws/src
git clone https://github.com/JMU-ROBOTICS-VIVA/ros2_aruco.git
```

> Replace `your_ws` with your actual workspace name throughout this guide.

---

## Step 5: Patch ArUco Node for OpenCV 4.10

The `ros2_aruco` package was written for an older OpenCV API. Apply the following patches:

### 5.1 Verify file locations

```bash
ls ~/your_ws/src/ros2_aruco/ros2_aruco/ros2_aruco/
# Should show: aruco_generate_marker.py  aruco_node.py  __init__.py
```

### 5.2 Fix generate marker script

```bash
sed -i 's/cv2.aruco.Dictionary_get/cv2.aruco.getPredefinedDictionary/g' \
  ~/your_ws/src/ros2_aruco/ros2_aruco/ros2_aruco/aruco_generate_marker.py

sed -i 's/cv2.aruco.drawMarker(dictionary, args.id, args.size, image, 1)/cv2.aruco.generateImageMarker(dictionary, args.id, args.size, image, 1)/g' \
  ~/your_ws/src/ros2_aruco/ros2_aruco/ros2_aruco/aruco_generate_marker.py
```

### 5.3 Patch aruco_node.py

Run this Python script to apply all patches at once:

```bash
python3 << 'EOF'
import os
filepath = os.path.expanduser('~/your_ws/src/ros2_aruco/ros2_aruco/ros2_aruco/aruco_node.py')
with open(filepath, 'r') as f:
    content = f.read()

old_import = "import rclpy\nimport rclpy.node"
new_import = (
    "import sys\n"
    "sys.path.insert(0, '/home/" + os.environ['USER'] + "/.local/lib/python3.12/site-packages')\n"
    "import rclpy\nimport rclpy.node"
)
content = content.replace(old_import, new_import)
content = content.replace('cv2.aruco.Dictionary_get', 'cv2.aruco.getPredefinedDictionary')

old_init = (
    "        self.aruco_dictionary = cv2.aruco.getPredefinedDictionary(dictionary_id)\n"
    "        self.aruco_parameters = cv2.aruco.DetectorParameters()\n"
    "        self.bridge = CvBridge()"
)
new_init = (
    "        self.aruco_dictionary = cv2.aruco.getPredefinedDictionary(dictionary_id)\n"
    "        self.aruco_parameters = cv2.aruco.DetectorParameters()\n"
    "        self.aruco_detector = cv2.aruco.ArucoDetector(self.aruco_dictionary, self.aruco_parameters)\n"
    "        self.bridge = CvBridge()"
)
content = content.replace(old_init, new_init)

old_detect = (
    "        corners, marker_ids, rejected = cv2.aruco.detectMarkers(\n"
    "            cv_image, self.aruco_dictionary, parameters=self.aruco_parameters\n"
    "        )\n"
    "        if marker_ids is not None:\n"
    "            if cv2.__version__ > \"4.0.0\":\n"
    "                rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(\n"
    "                    corners, self.marker_size, self.intrinsic_mat, self.distortion\n"
    "                )\n"
    "            else:\n"
    "                rvecs, tvecs = cv2.aruco.estimatePoseSingleMarkers(\n"
    "                    corners, self.marker_size, self.intrinsic_mat, self.distortion\n"
    "                )"
)
new_detect = (
    "        corners, marker_ids, rejected = self.aruco_detector.detectMarkers(cv_image)\n"
    "        if marker_ids is not None:\n"
    "            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(\n"
    "                corners, self.marker_size, self.intrinsic_mat, self.distortion\n"
    "            )"
)
content = content.replace(old_detect, new_detect)

with open(filepath, 'w') as f:
    f.write(content)
print("Patches applied!")
EOF
```

### 5.4 Verify patches landed correctly

```bash
grep -n "import sys\|aruco_detector\|detectMarkers" \
  ~/your_ws/src/ros2_aruco/ros2_aruco/ros2_aruco/aruco_node.py
```

Expected output (line numbers may vary):
```
32: import sys
154: self.aruco_detector = cv2.aruco.ArucoDetector(...)
186: corners, marker_ids, rejected = self.aruco_detector.detectMarkers(cv_image)
```

> **NOTE:** The `sys.path.insert` line won't appear in `head -5` because the file starts with a docstring. Always use `grep` as shown above to confirm patches landed correctly.

---

## Step 6: Build the Workspace

```bash
cd ~/your_ws
colcon build --symlink-install
```

Expected output:
```
Summary: 2 packages finished [~16s]
  1 package had stderr output: ros2_aruco
```

> **NOTE:** The `pytest-repeat egg-info` warning in stderr is harmless.

---

## Step 7: Configure Environment

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "source ~/your_ws/install/setup.bash" >> ~/.bashrc
echo "export ROS_DOMAIN_ID=0" >> ~/.bashrc
echo "export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST" >> ~/.bashrc
source ~/.bashrc
```

Verify the workspace is visible to ROS:

```bash
ros2 pkg list | grep aruco
# Should show:
# ros2_aruco
# ros2_aruco_interfaces
```

> **NOTE:** If migrating from a previous workspace, update the `source` line in `~/.bashrc` to point to the new workspace. Having two workspace source lines will cause conflicts.

---

## Step 8: Create the RealSense + ArUco Launch File

> **IMPORTANT:** The `ros2_aruco` node uses **parameters** (not ROS remappings) for topic names. The `image_topic` and `camera_info_topic` parameters must be set explicitly to the RealSense topic paths. Using remappings in the launch file will not work.

Write the launch file using Python to avoid heredoc formatting issues in the terminal:

```bash
python3 << 'EOF'
content = '''from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution

def generate_launch_description():
    realsense_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('realsense2_camera'),
                'launch', 'rs_launch.py'
            ])
        ]),
        launch_arguments={
            'enable_color':               'true',
            'enable_depth':               'true',
            'enable_infra1':              'true',
            'enable_infra2':              'true',
            'align_depth.enable':         'true',
            'pointcloud.enable':          'true',
            'enable_accel':               'true',
            'enable_gyro':                'true',
            'enable_sync':                'true',
            'rgb_camera.color_profile':   '640x480x30',
            'depth_module.depth_profile': '640x480x30',
            'depth_module.infra_profile': '640x480x30',
        }.items()
    )

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

    return LaunchDescription([realsense_launch, aruco_node])
'''

import os
path = os.path.expanduser('~/your_ws/src/ros2_aruco/ros2_aruco/launch/aruco_realsense.launch.py')
with open(path, 'w') as f:
    f.write(content)
print("Launch file written!")
EOF
```

Rebuild to register the new launch file:

```bash
cd ~/your_ws && colcon build --symlink-install
source ~/.bashrc
```

---

## Step 9: Running the System

```bash
# Kill any old instances first
pkill -f realsense2_camera_node; pkill -f aruco_node; sleep 2

# Launch everything in background
ros2 launch ros2_aruco aruco_realsense.launch.py &

# Wait for camera to initialise
sleep 6

# Echo ArUco detections — hold a marker up to the camera
ros2 topic echo /aruco_markers
```

### To stop everything

Press `Ctrl+C` to stop the echo, then:

```bash
pkill -f realsense2_camera_node; pkill -f aruco_node
```

---

## Step 10: Expected Output

When a marker is detected you should see output like this:

```
header:
  stamp:
    sec: 1773082767
    nanosec: 695953125
  frame_id: camera_color_optical_frame
marker_ids:
- 3
poses:
- position:
    x: 0.047030272209782405   # meters left/right of camera center
    y: -0.03419500311922467   # meters up/down
    z: 0.1557851034772402     # meters distance from camera
  orientation:
    x: -0.5913555339610655
    y: -0.4113294239905445
    z: 0.5216795238336517
    w: 0.4571183783506461
---
```

Note that `frame_id` is `camera_color_optical_frame` — the real RealSense coordinate frame, not the placeholder `default_cam` used with the USB webcam setup.

---

## Step 11: All Available Topics

After launching, the following topics are available. Use `ros2 topic echo <topic>` on any of them.

### ArUco Output
| Topic | Type | Description |
|---|---|---|
| `/aruco_markers` | `ros2_aruco_interfaces/msg/ArucoMarkers` | Detected marker IDs + 6-DOF poses |
| `/aruco_poses` | `geometry_msgs/msg/PoseArray` | Poses for use with TF / RViz |

### Color (RGB)
| Topic | Description |
|---|---|
| `/camera/camera/color/image_raw` | RGB image at 640x480x30 |
| `/camera/camera/color/camera_info` | Real hardware intrinsics |
| `/camera/camera/color/metadata` | Exposure, gain, white balance, etc. |
| `/camera/camera/color/image_raw/compressed` | Compressed RGB |

### Depth
| Topic | Description |
|---|---|
| `/camera/camera/depth/image_rect_raw` | Raw depth image (16-bit Z16, mm units) |
| `/camera/camera/depth/camera_info` | Depth stream intrinsics |
| `/camera/camera/depth/metadata` | Depth stream metadata |
| `/camera/camera/depth/color/points` | Colored XYZRGB point cloud |
| `/camera/camera/aligned_depth_to_color/image_raw` | Depth aligned to color frame |
| `/camera/camera/aligned_depth_to_color/camera_info` | Aligned depth intrinsics |

### Infrared Stereo
| Topic | Description |
|---|---|
| `/camera/camera/infra1/image_rect_raw` | Left IR image (Y8 grayscale) |
| `/camera/camera/infra2/image_rect_raw` | Right IR image (Y8 grayscale) |
| `/camera/camera/infra1/camera_info` | IR1 intrinsics |
| `/camera/camera/infra2/camera_info` | IR2 intrinsics |
| `/camera/camera/infra1/metadata` | IR1 metadata |
| `/camera/camera/infra2/metadata` | IR2 metadata |
| `/camera/camera/aligned_depth_to_infra1/image_raw` | Depth aligned to IR1 |
| `/camera/camera/aligned_depth_to_infra2/image_raw` | Depth aligned to IR2 |

### IMU (D435I only)
| Topic | Description |
|---|---|
| `/camera/camera/accel/sample` | Accelerometer at 63Hz (MOTION_XYZ32F) |
| `/camera/camera/gyro/sample` | Gyroscope at 200Hz (MOTION_XYZ32F) |
| `/camera/camera/accel/imu_info` | Accelerometer intrinsics |
| `/camera/camera/gyro/imu_info` | Gyroscope intrinsics |
| `/camera/camera/accel/metadata` | Accelerometer metadata |
| `/camera/camera/gyro/metadata` | Gyroscope metadata |

### Extrinsics & TF
| Topic | Description |
|---|---|
| `/camera/camera/extrinsics/depth_to_color` | Transform between depth and color sensors |
| `/camera/camera/extrinsics/depth_to_infra1` | Transform between depth and IR1 |
| `/camera/camera/extrinsics/depth_to_infra2` | Transform between depth and IR2 |
| `/camera/camera/extrinsics/depth_to_accel` | Transform between depth and accelerometer |
| `/camera/camera/extrinsics/depth_to_gyro` | Transform between depth and gyroscope |
| `/tf_static` | All static transforms for RViz / navigation |

---

## Step 12: Useful Commands

### Check all active topics
```bash
ros2 topic list
```

### Check topic publishing rate
```bash
ros2 topic hz /camera/camera/color/image_raw
ros2 topic hz /camera/camera/depth/image_rect_raw
ros2 topic hz /camera/camera/gyro/sample
```

### Echo IMU data
```bash
ros2 topic echo /camera/camera/accel/sample
ros2 topic echo /camera/camera/gyro/sample
```

### Run RealSense camera standalone (no ArUco)
```bash
ros2 launch realsense2_camera rs_launch.py \
  enable_color:=true \
  enable_depth:=true \
  align_depth.enable:=true \
  pointcloud.enable:=true \
  enable_accel:=true \
  enable_gyro:=true \
  enable_infra1:=true \
  enable_infra2:=true \
  enable_sync:=true \
  rgb_camera.color_profile:=640x480x30 \
  depth_module.depth_profile:=640x480x30 \
  depth_module.infra_profile:=640x480x30
```

### Record all streams to a rosbag
```bash
ros2 bag record \
  /camera/camera/color/image_raw \
  /camera/camera/color/camera_info \
  /camera/camera/depth/image_rect_raw \
  /camera/camera/aligned_depth_to_color/image_raw \
  /camera/camera/depth/color/points \
  /camera/camera/infra1/image_rect_raw \
  /camera/camera/infra2/image_rect_raw \
  /camera/camera/accel/sample \
  /camera/camera/gyro/sample \
  /aruco_markers \
  /tf_static \
  -o realsense_aruco_recording
```

### Playback from a rosbag
```bash
ros2 bag play realsense_aruco_recording
```

### Visualize in RViz2
```bash
rviz2
```

Add these displays in RViz2:
- **Image** → `/camera/camera/color/image_raw` — RGB feed
- **Image** → `/camera/camera/aligned_depth_to_color/image_raw` — depth overlay
- **PointCloud2** → `/camera/camera/depth/color/points` — 3D point cloud
- **PoseArray** → `/aruco_poses` — ArUco marker poses in 3D
- **TF** — all coordinate frames

---

## Step 13: Generating ArUco Markers

```bash
# Generates marker_0001.png in current directory
ros2 run ros2_aruco aruco_generate_marker --id 1 --size 200 --dictionary DICT_4X4_50

xdg-open marker_0001.png
```

> **NOTE:** When printing, use 100% scale (do not scale to fit). Measure the physical printed black square side length in meters and use that value as `marker_size` in the launch file. Even a few mm of error affects pose accuracy.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `rs-enumerate-devices` shows nothing | Camera not detected. Try `sudo apt install librealsense2-udev-rules` then unplug and replug |
| `Usb Type Descriptor: 2.1` in enumerate output | Wrong USB port. Move to a USB 3.0 (blue) port |
| `overflow video frame detected` / `Frame Corrupted` | USB bandwidth overflow — you are on USB 2.x. Switch to USB 3.0 port, or reduce streams/resolution |
| `[realsense2_camera] Error: No device connected` | Unplug and replug. Confirm `rs-enumerate-devices` sees the camera first |
| Depth image all black | `enable_depth:=true` not set, or camera too close (min range ~0.1m) |
| Point cloud topic missing | Add `pointcloud.enable:=true` to launch args |
| IMU topics missing | Add `enable_accel:=true enable_gyro:=true` to launch args |
| `IMU Calibration is not available` warning | Benign — factory IMU calibration not stored on this unit. Default intrinsics used, IMU still works |
| `get_xu(ctrl=1) failed! Device or resource busy` | Benign timing warning from the SDK — does not affect functionality |
| ArUco node shows `/camera/image_raw` not RealSense topics | The node uses parameters not remappings. Set `image_topic` and `camera_info_topic` as parameters in the launch file |
| `No camera info has been received!` on startup | Temporary — clears once first frame arrives. Not an error |
| Segfault in `detectMarkers` | apt OpenCV is broken. Confirm pip `opencv-contrib-python==4.10.0.84` is installed and loading from `.local/lib` |
| `ros2 node list` returns empty | Set `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` and run everything from one terminal |
| Two camera instances conflict | Run `pkill -f realsense2_camera_node` before launching |

---

## Key Differences from USB Webcam Setup

| Feature | USB Webcam | RealSense D435I |
|---|---|---|
| Driver package | `ros-jazzy-usb-cam` | `ros-jazzy-realsense2-camera` |
| Launch file | `aruco_usb.launch.py` | `aruco_realsense.launch.py` |
| Calibration | Fake YAML file required | Real intrinsics from hardware |
| frame_id | `default_cam` | `camera_color_optical_frame` |
| Depth data | None | Yes — aligned depth per pixel |
| Point cloud | No | Yes |
| IR stereo | No | Yes (infra1 + infra2) |
| IMU | No | Yes (accel + gyro) |
| Topic config | Remappings | Parameters (`image_topic`, `camera_info_topic`) |
| Image topic | `/image_raw` | `/camera/camera/color/image_raw` |
| Camera info topic | `/camera_info` | `/camera/camera/color/camera_info` |

---

## Important Notes

- Always use a **USB 3.0 or higher port** — USB 2.x will cause frame overflow and corruption with multiple streams enabled
- The `ros2_aruco` node uses **parameters not ROS remappings** for topic names — set `image_topic` and `camera_info_topic` in the launch file parameters block
- The apt OpenCV 4.6 on Ubuntu 24.04 has a broken ArUco module — always use pip OpenCV 4.10
- The `sys.path.insert` patch in `aruco_node.py` ensures pip OpenCV loads instead of the broken apt version
- `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` is required for reliable cross-terminal node discovery on Ubuntu 24.04
- The `marker_size` parameter must match the physical printed marker size in meters
- `DICT_4X4_50` and `DICT_5X5_250` are the most common dictionaries — markers and detector must use the same one

---

## Next Steps

- Use the aligned depth topic to get hardware-accurate 3D distance to each detected ArUco marker
- Feed `/camera/camera/depth/color/points` into a SLAM package for simultaneous mapping and localization
- Fuse the IMU (`accel` + `gyro`) with visual odometry for robust pose estimation in dynamic environments
- Use the IR stereo pair for odometry in low-light or textureless environments
- Record a rosbag of a full scene and replay it offline for development without needing the physical camera connected
