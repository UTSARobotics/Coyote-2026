#include <librealsense2/rs.hpp>
#include <iostream>

int main() try {
    // Create pipeline
    rs2::pipeline pipe;
    rs2::config cfg;
    
    // Working configuration: 1280x720 RGB and 640x480 depth @ 6 FPS
    cfg.enable_stream(RS2_STREAM_COLOR, 1280, 720, RS2_FORMAT_RGB8, 6);
    cfg.enable_stream(RS2_STREAM_DEPTH, 640, 480, RS2_FORMAT_Z16, 6);
    
    std::cout << "Starting pipeline..." << std::endl;
    pipe.start(cfg);
    
    std::cout << "Pipeline started successfully!" << std::endl;
    
    // Get one frameset
    rs2::frameset frames = pipe.wait_for_frames();
    std::cout << "Got frames: " << frames.size() << std::endl;
    
    pipe.stop();
    std::cout << "Test completed successfully!" << std::endl;
    return 0;
} catch (const rs2::error &e) {
    std::cerr << "RealSense error: " << e.what() << std::endl;
    return 1;
} catch (const std::exception &e) {
    std::cerr << "Standard error: " << e.what() << std::endl;
    return 1;
}