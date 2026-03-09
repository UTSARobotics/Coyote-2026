# ArUco Marker Detection with ROS 2 Jazzy
### Setup Guide for Ubuntu 24.04 (Noble) — March 2026

---

## Overview

This guide walks through setting up ArUco marker detection in ROS 2 Jazzy on Ubuntu 24.04. By the end you will have a working system that detects ArUco markers from a USB webcam and publishes their 3D position and orientation in real time.

---

## System Requirements

| Component | Required Version |
|---|---|
| Operating System | Ubuntu 24.04 LTS (Noble Numbat) |
| ROS 2 Distribution | Jazzy Jalisco (NOT Humble — that requires Ubuntu 22.04) |
| Python | 3.12 (comes with Ubuntu 24.04) |
| Camera | USB webcam or laptop built-in camera |
| ArUco Markers | Physical printed markers or ArUco cube |

> **NOTE:** If you are on Ubuntu 24.04 and try to install `ros-humble-*` packages, they will not be found. Ubuntu 24.04 requires ROS 2 Jazzy.

---

## Step 1: Set Up ROS 2 Jazzy Repository

### 1.1 Clean Up Old Repos

Check for conflicting repo files (a common issue is having both `ros2.list` and `ros2.sources`):

```bash
ls /etc/apt/sources.list.d/

# Remove ALL ros2 repo files
sudo rm -f /etc/apt/sources.list.d/ros2.list
sudo rm -f /etc/apt/sources.list.d/ros2.sources
```

### 1.2 Add Correct Jazzy Repository

```bash
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu noble main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
```

---

## Step 2: Install ROS 2 Jazzy

```bash
sudo apt install ros-jazzy-desktop
sudo apt install ros-jazzy-tf-transformations
sudo apt install ros-jazzy-cv-bridge
sudo apt install ros-jazzy-vision-opencv
sudo apt install ros-jazzy-usb-cam
sudo apt install python3-opencv python3-numpy
```

> **NOTE:** Do NOT install `ros-jazzy-opencv-tests` — this package does not exist. The apt `python3-opencv` on Ubuntu 24.04 has a broken ArUco module — we fix this in Step 3.

---

## Step 3: Fix OpenCV for ArUco

The system apt OpenCV 4.6 on Ubuntu 24.04 has a broken ArUco `detectMarkers` function (causes segfaults). Install OpenCV 4.10 via pip instead:

```bash
# Remove pip opencv if previously installed
pip3 uninstall opencv-contrib-python opencv-python -y --break-system-packages 2>/dev/null

# Install working version
pip3 install opencv-contrib-python==4.10.0.84 --break-system-packages
```

Verify the installation works:

```bash
python3 -c "
import sys
sys.path.insert(0, '/home/$USER/.local/lib/python3.12/site-packages')
import cv2, numpy as np
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_250)
detector = cv2.aruco.ArucoDetector(dictionary, cv2.aruco.DetectorParameters())
img = np.zeros((480, 640), dtype=np.uint8)
corners, ids, rejected = detector.detectMarkers(img)
print('ArUco OK!')
"
```

---

## Step 4: Create ROS 2 Workspace

```bash
mkdir -p ~/aruco_ws/src
cd ~/aruco_ws/src
git clone https://github.com/JMU-ROBOTICS-VIVA/ros2_aruco.git
```

---

## Step 5: Patch ArUco Node for OpenCV 4.10

The `ros2_aruco` package was written for an older OpenCV API. Apply the following patches:

### 5.1 Fix generate marker script

```bash
sed -i 's/cv2.aruco.Dictionary_get/cv2.aruco.getPredefinedDictionary/g' \
  ~/aruco_ws/src/ros2_aruco/ros2_aruco/ros2_aruco/aruco_generate_marker.py

sed -i 's/cv2.aruco.drawMarker(dictionary, args.id, args.size, image, 1)/cv2.aruco.generateImageMarker(dictionary, args.id, args.size, image, 1)/g' \
  ~/aruco_ws/src/ros2_aruco/ros2_aruco/ros2_aruco/aruco_generate_marker.py
```

### 5.2 Patch aruco_node.py

Run this Python script to apply all patches at once:

```bash
python3 << 'EOF'
import os
filepath = os.path.expanduser('~/aruco_ws/src/ros2_aruco/ros2_aruco/ros2_aruco/aruco_node.py')
with open(filepath, 'r') as f:
    content = f.read()

# 1. Add sys.path fix to load pip OpenCV instead of broken apt OpenCV
old_import = "import rclpy\nimport rclpy.node"
new_import = (
    "import sys\n"
    "sys.path.insert(0, '/home/" + os.environ['USER'] + "/.local/lib/python3.12/site-packages')\n"
    "import rclpy\nimport rclpy.node"
)
content = content.replace(old_import, new_import)

# 2. Fix Dictionary_get -> getPredefinedDictionary
content = content.replace('cv2.aruco.Dictionary_get', 'cv2.aruco.getPredefinedDictionary')

# 3. Use new ArucoDetector class
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

# 4. Replace detectMarkers with new API
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

---

## Step 6: Build the Workspace

```bash
cd ~/aruco_ws
colcon build --symlink-install
```

> **NOTE:** Ignore warnings about `pytest-repeat egg-info` — these are harmless.

---

## Step 7: Configure Environment

Add these lines to `~/.bashrc` so every new terminal is ready automatically:

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "source ~/aruco_ws/install/setup.bash" >> ~/.bashrc
echo "export ROS_DOMAIN_ID=0" >> ~/.bashrc
echo "export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST" >> ~/.bashrc
source ~/.bashrc
```

> **NOTE:** `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` is important — without it, cross-terminal node discovery may not work reliably on Ubuntu 24.04.

---

## Step 8: Create Camera Calibration File

Without a calibration file, position and orientation will be all zeros. Create a basic calibration file for a 640x480 webcam:

```bash
mkdir -p ~/.ros/camera_info
cat > ~/.ros/camera_info/default_cam.yaml << 'EOF'
image_width: 640
image_height: 480
camera_name: default_cam
camera_matrix:
  rows: 3
  cols: 3
  data: [600, 0, 320, 0, 600, 240, 0, 0, 1]
distortion_model: plumb_bob
distortion_coefficients:
  rows: 1
  cols: 5
  data: [0, 0, 0, 0, 0]
rectification_matrix:
  rows: 3
  cols: 3
  data: [1, 0, 0, 0, 1, 0, 0, 0, 1]
projection_matrix:
  rows: 3
  cols: 4
  data: [600, 0, 320, 0, 0, 600, 240, 0, 0, 0, 1, 0]
EOF
```

> **NOTE:** This is an approximate calibration. For accurate pose measurements, perform proper camera calibration using a printed checkerboard with `ros2 run camera_calibration cameracalibrator`.

---

## Step 9: Create Launch File

Create a single launch file that starts both the camera and ArUco detector together:

```bash
cat > ~/aruco_ws/src/ros2_aruco/ros2_aruco/launch/aruco_usb.launch.py << 'EOF'
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='usb_cam',
            executable='usb_cam_node_exe',
            name='usb_cam',
            parameters=[{'video_device': '/dev/video0'}]
        ),
        Node(
            package='ros2_aruco',
            executable='aruco_node',
            name='aruco_node',
            parameters=[{
                'marker_size': 0.03,
                'aruco_dictionary_id': 'DICT_4X4_50'
            }],
            remappings=[
                ('/camera/image_raw', '/image_raw'),
                ('/camera/camera_info', '/camera_info')
            ]
        ),
    ])
EOF

cd ~/aruco_ws && colcon build --symlink-install
```

---

## Step 10: Running the System

Due to a cross-terminal ROS discovery issue on Ubuntu 24.04, run everything from a single terminal using background processes:

```bash
# Kill any existing instances first
pkill -f usb_cam_node_exe; pkill -f aruco_node; sleep 2

# Launch camera + aruco detector in background
ros2 launch ros2_aruco aruco_usb.launch.py &

# Wait for nodes to start
sleep 5

# Echo detections (hold marker up to camera)
ros2 topic echo /aruco_markers
```

### To stop everything

Press `Ctrl+\` (Ctrl + backslash), then:

```bash
pkill -f usb_cam_node_exe
pkill -f aruco_node
```

---

## Step 11: Expected Output

When a marker is detected you should see output like this:

```
header:
  stamp:
    sec: 1773011900
    nanosec: 1046000
  frame_id: default_cam
marker_ids:
- 17
poses:
- position:
    x: -0.487  # meters left/right of camera center
    y: 0.171   # meters up/down
    z: 1.506   # meters distance from camera
  orientation:
    x: -0.906
    y: -0.025
    z: -0.174
    w: 0.382
---
```

---

## Step 12: Generating ArUco Markers

```bash
# Generates marker_0001.png in current directory
ros2 run ros2_aruco aruco_generate_marker --id 1 --size 200 --dictionary DICT_4X4_50

# Open the generated image
xdg-open marker_0001.png
```

> **NOTE:** When printing, use 100% scale (do not scale to fit). Measure the printed black square side length in meters and use that as the `marker_size` parameter.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `E: Unable to locate package ros-humble-*` | You are on Ubuntu 24.04 which requires `ros-jazzy-*`, not `ros-humble-*` |
| `Conflicting values set for option Signed-By` | Remove both `ros2.list` AND `ros2.sources` from `/etc/apt/sources.list.d/` and re-add the repo |
| Segmentation fault in `detectMarkers` | The apt `python3-opencv` is broken. Install `pip opencv-contrib-python==4.10.0.84` instead |
| Position and orientation all zeros | Camera calibration file is missing. Create `~/.ros/camera_info/default_cam.yaml` |
| `ros2 node list` returns empty | Run everything in one terminal using `&` for background processes. Set `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` |
| `AttributeError: module cv2.aruco has no attribute X` | OpenCV API changed in 4.7+. Make sure the node patches from Step 5 were applied correctly |
| `terminate called after throwing instance of char*` | Two `usb_cam` instances trying to open the same camera. Run `pkill -f usb_cam_node_exe` first |
| numpy conflict errors | Do not mix pip and apt numpy. Use only apt `python3-numpy` for system numpy |

---

## Important Notes

- Always use `ros-jazzy-*` packages on Ubuntu 24.04, never `ros-humble-*`
- The apt OpenCV 4.6 on Ubuntu 24.04 has a broken ArUco module — use pip OpenCV 4.10
- The `sys.path.insert` patch in `aruco_node.py` ensures the pip OpenCV is loaded instead of the broken apt one
- ROS cross-terminal node discovery is unreliable on Ubuntu 24.04 with default settings — always run from one terminal or set `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`
- Camera calibration gives accurate 3D pose. The default calibration file is approximate
- The `marker_size` parameter must match the physical size of the printed marker in meters
- `DICT_4X4_50` and `DICT_5X5_250` are the most common dictionaries — make sure your markers and detector use the same one

---

## Next Steps

Now that ArUco detection is working, you can:

- Perform proper camera calibration with a printed checkerboard for accurate pose measurements
- Visualize marker poses in RViz2 by subscribing to the `/aruco_poses` topic
- Use the `/aruco_markers` topic in your own ROS 2 nodes to drive robot behavior based on marker detection
- Place markers in a known map for robot localization
- Use multiple markers for robust detection from any angle (like an ArUco cube)
