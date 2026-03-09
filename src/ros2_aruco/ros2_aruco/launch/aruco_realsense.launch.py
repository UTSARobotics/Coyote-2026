from launch import LaunchDescription
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
