#include "realsense_driver.h"
#include <librealsense2/rs.hpp>
#include <cstdio>
#include <cstdlib>

// Global variables for ROS3 and RealSense
static rose_node *g_node = nullptr;
static rose_publisher *g_rgb_pub = nullptr;
static rose_publisher *g_depth_pub = nullptr;
static rose_publisher *g_pointcloud_pub = nullptr;
static rs2::pipeline *g_pipeline = nullptr;
static rs2::pointcloud *g_pointcloud = nullptr;
static rs2::decimation_filter *g_decimate_filter = nullptr;

int realsense_driver_init(int argc, char **argv) {
    // Initialize ROS3 node
    char node_name[] = "realsense_driver";
    g_node = rose_init((char)argc, argv, node_name, nullptr, nullptr);
    if (!g_node) {
        std::fprintf(stderr, "Failed to initialize ROS3 node\n");
        return -1;
    }

    // Create publishers
    g_rgb_pub = rose_create_pub(g_node, (char*)TOPIC_RGB, -1, RGB_MESSAGE_SIZE, RGB_MESSAGE_RATE);
    g_depth_pub = rose_create_pub(g_node, (char*)TOPIC_DEPTH, -1, DEPTH_MESSAGE_SIZE, DEPTH_MESSAGE_RATE);
    g_pointcloud_pub = rose_create_pub(g_node, (char*)TOPIC_POINTCLOUD, -1, POINTCLOUD_MESSAGE_SIZE, POINTCLOUD_MESSAGE_RATE);

    if (!g_rgb_pub || !g_depth_pub || !g_pointcloud_pub) {
        std::fprintf(stderr, "Failed to create ROS3 publishers\n");
        rose_shutdown(g_node);
        return -2;
    }

    // Initialize RealSense
    try {
        g_pipeline = new rs2::pipeline();
        g_pointcloud = new rs2::pointcloud();
        
        // Initialize decimation filter if enabled
#if ENABLE_DECIMATION_FILTER
        g_decimate_filter = new rs2::decimation_filter();
        g_decimate_filter->set_option(RS2_OPTION_FILTER_MAGNITUDE, DECIMATION_MAGNITUDE);
        std::printf("Decimation filter enabled (magnitude: %.1f)\n", DECIMATION_MAGNITUDE);
#endif
        
        // Configure streams
        rs2::config config;
        config.enable_stream(RS2_STREAM_COLOR, REALSENSE_RGB_WIDTH, REALSENSE_RGB_HEIGHT, RS2_FORMAT_RGB8, REALSENSE_RGB_FPS);
        config.enable_stream(RS2_STREAM_DEPTH, REALSENSE_DEPTH_WIDTH, REALSENSE_DEPTH_HEIGHT, RS2_FORMAT_Z16, REALSENSE_DEPTH_FPS);
        
        // Start pipeline
        g_pipeline->start(config);
        
        // Configure emitter (IR projector)
        rs2::device device = g_pipeline->get_active_profile().get_device();
        // Get the depth sensor to configure emitter options
        rs2::sensor depth_sensor = device.first<rs2::depth_sensor>();
        if (depth_sensor.supports(RS2_OPTION_EMITTER_ENABLED)) {
            depth_sensor.set_option(RS2_OPTION_EMITTER_ENABLED, ENABLE_EMITTER ? 1.0f : 0.0f);
        }
        if (depth_sensor.supports(RS2_OPTION_LASER_POWER)) {
            depth_sensor.set_option(RS2_OPTION_LASER_POWER, EMITTER_POWER);
        }
        
        std::printf("RealSense D435 driver initialized successfully\n");
        std::printf("Emitter: %s (Power: %.1f mW)\n", ENABLE_EMITTER ? "Enabled" : "Disabled", EMITTER_POWER);
        std::printf("RGB: %dx%d @ %d FPS\n", REALSENSE_RGB_WIDTH, REALSENSE_RGB_HEIGHT, REALSENSE_RGB_FPS);
        std::printf("Depth: %dx%d @ %d FPS\n", REALSENSE_DEPTH_WIDTH, REALSENSE_DEPTH_HEIGHT, REALSENSE_DEPTH_FPS);
        std::printf("Publishing to: %s, %s, %s\n", TOPIC_RGB, TOPIC_DEPTH, TOPIC_POINTCLOUD);
        
        return 0;
    } catch (const rs2::error &e) {
        std::fprintf(stderr, "RealSense error: %s\n", e.what());
        rose_shutdown(g_node);
        return -3;
    } catch (const std::exception &e) {
        std::fprintf(stderr, "Standard error: %s\n", e.what());
        rose_shutdown(g_node);
        return -4;
    }
}

void realsense_driver_run() {
    if (!g_node || !g_pipeline) {
        return;
    }

    // Create message buffers
    mirage_msg *rgb_msg = mirage_create(RGB_MESSAGE_SIZE, nullptr);
    mirage_msg *depth_msg = mirage_create(DEPTH_MESSAGE_SIZE, nullptr);
    mirage_msg *pointcloud_msg = mirage_create(POINTCLOUD_MESSAGE_SIZE, nullptr);

    if (!rgb_msg || !depth_msg || !pointcloud_msg) {
        std::fprintf(stderr, "Failed to create message buffers\n");
        return;
    }

    while (rose_ok(g_node)) {
        try {
            // Wait for frames
            rs2::frameset frames = g_pipeline->wait_for_frames();
            
            // Get color frame
            rs2::video_frame color_frame = frames.get_color_frame();
            if (color_frame) {
                // Encode RGB image as numeric array (includes size info)
                mirage_write_start(rgb_msg);
                int64_t rgb_size = color_frame.get_width() * color_frame.get_height() * 3;
                int64_t rgb_dims[] = {rgb_size};
                mirage_write_numericarray(rgb_msg, MIRAGE_ARRAY_U8, 1, rgb_dims, 
                                         (const uint8_t*)color_frame.get_data());
                rose_publish(g_rgb_pub, rgb_msg);
            }

            // Get depth frame
            rs2::depth_frame depth_frame = frames.get_depth_frame();
            if (depth_frame) {
                // Apply decimation filter if enabled
#if ENABLE_DECIMATION_FILTER
                depth_frame = g_decimate_filter->process(depth_frame);
#endif
                
                // Encode depth image as numeric array (includes size info)
                mirage_write_start(depth_msg);
                int64_t depth_size = depth_frame.get_width() * depth_frame.get_height();
                int64_t depth_dims[] = {depth_size};
                mirage_write_numericarray(depth_msg, MIRAGE_ARRAY_U16, 1, depth_dims, 
                                         (const uint8_t*)depth_frame.get_data());
                rose_publish(g_depth_pub, depth_msg);
                
                // Get color frame for point cloud texturing
                rs2::video_frame color_frame = frames.get_color_frame();
                if (color_frame) {
                    // Map pointcloud to color frame
                    g_pointcloud->map_to(color_frame);
                }
                
                // Generate and publish point cloud
                rs2::points points = g_pointcloud->calculate(depth_frame);
                if (points.size() > 0) {
                    // Get vertices as float array (XYZ coordinates)
                    const rs2::vertex* vertices = points.get_vertices();
                    mirage_write_start(pointcloud_msg);
                    int64_t pointcloud_size = points.size() * 3; // 3 coordinates per point (X,Y,Z)
                    int64_t pointcloud_dims[] = {pointcloud_size};
                    mirage_write_numericarray(pointcloud_msg, MIRAGE_ARRAY_F32, 1, pointcloud_dims,
                                              (const uint8_t*)vertices);
                    rose_publish(g_pointcloud_pub, pointcloud_msg);
                }
            }

        } catch (const rs2::error &e) {
            std::fprintf(stderr, "RealSense error in main loop: %s\n", e.what());
            break;
        } catch (const std::exception &e) {
            std::fprintf(stderr, "Standard error in main loop: %s\n", e.what());
            break;
        }
    }

    // Cleanup message buffers
    mirage_destroy(&rgb_msg, nullptr);
    mirage_destroy(&depth_msg, nullptr);
    mirage_destroy(&pointcloud_msg, nullptr);
}

void realsense_driver_shutdown() {
    if (g_pipeline) {
        try {
            g_pipeline->stop();
        } catch (...) {
            // Ignore errors during shutdown
        }
        delete g_pipeline;
        g_pipeline = nullptr;
    }

    if (g_pointcloud) {
        delete g_pointcloud;
        g_pointcloud = nullptr;
    }

#if ENABLE_DECIMATION_FILTER
    if (g_decimate_filter) {
        delete g_decimate_filter;
        g_decimate_filter = nullptr;
    }
#endif

    if (g_node) {
        rose_shutdown(g_node);
        g_node = nullptr;
    }

    std::printf("RealSense driver shutdown complete\n");
}