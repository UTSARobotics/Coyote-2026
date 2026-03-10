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
    // Create a subscriber for PointCloud2 data
    subscription_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
      "/camera/camera/depth/color/points", 10, std::bind(&PclNode::pointCloudCallback, this, std::placeholders::_1));

    // Create a publisher for the processed PointCloud2 data (all above-ground points)
    above_ground_publisher_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("above_ground_points", 10);

    // Create a publisher for the centroids of obstacle clusters
    centroids_publisher_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("obstacle_centroids", 10);

    // Initialize previous ground plane coefficients
    previous_coefficients_.reset(new pcl::ModelCoefficients);

    RCLCPP_INFO(this->get_logger(), "PCL ROS2 Node started");
  }

private:
  void pointCloudCallback(const sensor_msgs::msg::PointCloud2::SharedPtr msg) {
    // Convert ROS2 PointCloud2 message to PCL point cloud
    pcl::PointCloud<pcl::PointXYZ>::Ptr cloud(new pcl::PointCloud<pcl::PointXYZ>);
    pcl::fromROSMsg(*msg, *cloud);

    // Apply voxel grid filtering to decimate the point cloud
    pcl::PointCloud<pcl::PointXYZ>::Ptr voxel_filtered_cloud(new pcl::PointCloud<pcl::PointXYZ>);
    pcl::VoxelGrid<pcl::PointXYZ> voxel_filter;
    voxel_filter.setInputCloud(cloud);
    voxel_filter.setLeafSize(0.03f, 0.03f, 0.03f); // Set the size of the voxel grid to 3 cm
    voxel_filter.filter(*voxel_filtered_cloud);

    // Apply statistical outlier removal filter
    pcl::PointCloud<pcl::PointXYZ>::Ptr filtered_cloud(new pcl::PointCloud<pcl::PointXYZ>);
    pcl::StatisticalOutlierRemoval<pcl::PointXYZ> sor;
    sor.setInputCloud(voxel_filtered_cloud);
    sor.setMeanK(50); // Number of nearest neighbors to consider
    sor.setStddevMulThresh(1.0); // Standard deviation multiplier threshold
    sor.filter(*filtered_cloud);

    // Segment the ground plane
    pcl::ModelCoefficients::Ptr coefficients(new pcl::ModelCoefficients);
    pcl::PointIndices::Ptr inliers(new pcl::PointIndices);
    pcl::SACSegmentation<pcl::PointXYZ> seg;
    seg.setOptimizeCoefficients(true);
    seg.setModelType(pcl::SACMODEL_PLANE);
    seg.setMethodType(pcl::SAC_RANSAC);
    seg.setDistanceThreshold(0.03); // Increased distance threshold for better ground plane detection
    seg.setMaxIterations(3000); // Increased number of RANSAC iterations

    seg.setInputCloud(filtered_cloud);
    seg.segment(*inliers, *coefficients);

    if (inliers->indices.size() == 0) {
      RCLCPP_ERROR(this->get_logger(), "Could not estimate a planar model for the given dataset.");
      return;
    }

    // Temporal smoothing: Use previous ground plane coefficients if available
    if (previous_coefficients_->values.size() > 0) {
      // Simple averaging of coefficients for temporal smoothing
      for (size_t i = 0; i < coefficients->values.size(); ++i) {
        coefficients->values[i] = 0.7 * previous_coefficients_->values[i] + 0.3 * coefficients->values[i];
      }
    }
    *previous_coefficients_ = *coefficients;

    // Extract the ground plane points
    pcl::ExtractIndices<pcl::PointXYZ> extract;
    extract.setInputCloud(filtered_cloud);
    extract.setIndices(inliers);
    extract.setNegative(true); // Extract the points that are not part of the ground plane
    extract.filter(*filtered_cloud);

    // Publish all above-ground points
    sensor_msgs::msg::PointCloud2 above_ground_msg;
    pcl::toROSMsg(*filtered_cloud, above_ground_msg);
    above_ground_msg.header = msg->header; // Copy the header from the input message
    above_ground_publisher_->publish(above_ground_msg);

    // Creating the KdTree object for the search method of the extraction
    pcl::search::KdTree<pcl::PointXYZ>::Ptr tree(new pcl::search::KdTree<pcl::PointXYZ>);
    tree->setInputCloud(filtered_cloud);

    std::vector<pcl::PointIndices> cluster_indices;
    pcl::EuclideanClusterExtraction<pcl::PointXYZ> ec;
    ec.setClusterTolerance(0.05); // 5 cm
    ec.setMinClusterSize(100);
    ec.setMaxClusterSize(25000);
    ec.setSearchMethod(tree);
    ec.setInputCloud(filtered_cloud);
    ec.extract(cluster_indices);

    // Create a point cloud to store centroids
    pcl::PointCloud<pcl::PointXYZ>::Ptr centroids(new pcl::PointCloud<pcl::PointXYZ>);

    // Compute the centroid for each cluster
    for (const auto &cluster : cluster_indices) {
      pcl::PointXYZ centroid;
      centroid.x = 0;
      centroid.y = 0;
      centroid.z = 0;
      for (const auto &index : cluster.indices) {
        centroid.x += filtered_cloud->points[index].x;
        centroid.y += filtered_cloud->points[index].y;
        centroid.z += filtered_cloud->points[index].z;
      }
      centroid.x /= cluster.indices.size();
      centroid.y /= cluster.indices.size();
      centroid.z /= cluster.indices.size();
      centroids->points.push_back(centroid);
    }

    // Convert the centroids to ROS2 PointCloud2 message
    sensor_msgs::msg::PointCloud2 centroids_msg;
    pcl::toROSMsg(*centroids, centroids_msg);
    centroids_msg.header = msg->header; // Copy the header from the input message

    // Publish the centroids
    centroids_publisher_->publish(centroids_msg);
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


