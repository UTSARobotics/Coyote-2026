import pyrealsense2 as rs
import cv2.aruco as aruco 
import numpy as np
import cv2

pipe = rs.pipeline()
cfg  = rs.config()

cfg.enable_stream(rs.stream.color, 640,480, rs.format.bgr8, 30)
cfg.enable_stream(rs.stream.depth, 640,480, rs.format.z16, 30)

aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, parameters)

pipe.start(cfg)

while True:
    frame = pipe.wait_for_frames()
    depth_frame = frame.get_depth_frame()
    color_frame = frame.get_color_frame()

    depth_image = np.asanyarray(depth_frame.get_data())
    color_image = np.asanyarray(color_frame.get_data())
    depth_cm = cv2.applyColorMap(cv2.convertScaleAbs(depth_image,
                                     alpha = 0.5), cv2.COLORMAP_JET)

    gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

    corners, ids, rejected = detector.detectMarkers(gray_image)

    if ids is not None:
        for i, corner in enumerate(corners):
            center = tuple(corner[0].mean(axis=0)) 
            depth = depth_frame.get_distance(center[0], center[1])
            intrinsics = depth_frame.profile.as_video_stream_profile().intrinsics
            point_3d = rs.rs2_deproject_pixel_to_point(intrinsics, center, depth)
            distance = np.linalg.norm(point_3d)
            print(f"Distance to marker {ids[i][0]}: {distance:.3f} meters")

    cv2.imshow('ArUco Marker Detection', color_image)

    if cv2.waitKey(1) == ord('q'):
        break

pipe.stop()
