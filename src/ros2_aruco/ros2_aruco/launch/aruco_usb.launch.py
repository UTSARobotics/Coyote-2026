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
