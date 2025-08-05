"""
DigitalOcean Helper for Kubernetes autoscaling operations.

This module provides comprehensive logging for:
- Initialization and configuration
- Worker node discovery and counting
- Node pool management operations
- KEDA ScaledObject updates
- API request/response details
- Error handling and debugging information
"""

import logging

import digitalocean
import requests

from spacelaunchnow import settings

DIGITAL_OCEAN_URL = "https://api.digitalocean.com"
K8S_CLUSTER_ID = settings.DO_CLUSTER_ID
DO_TOKEN = settings.DO_TOKEN

logger = logging.getLogger(__name__)


class DigitalOceanHelper:
    def __init__(self):
        logger.info("Initializing DigitalOceanHelper")
        self.DO_TOKEN = settings
        self.manager = digitalocean.Manager(token=DO_TOKEN)
        self.header = {"Authorization": f"Bearer {DO_TOKEN}"}
        logger.debug(f"DigitalOcean cluster ID: {K8S_CLUSTER_ID}")
        logger.info("DigitalOceanHelper initialized successfully")

    def get_worker_node_count(self):
        logger.debug("Getting worker node count")
        try:
            droplets = self.manager.get_all_droplets(tag_name="prod-worker")
            count = len(droplets)
            logger.info(f"Found {count} worker nodes with 'prod-worker' tag")
            return count
        except Exception as e:
            logger.error(f"Failed to get worker node count: {e}")
            raise

    def update_node_pools(self, min_nodes, max_nodes):
        logger.info(f"Updating node pools: min_nodes={min_nodes}, max_nodes={max_nodes}")

        try:
            pools = self.get_node_pools()
            if not pools or "node_pools" not in pools:
                logger.error("No node pools found or invalid response format")
                return

            logger.debug(f"Retrieved {len(pools['node_pools'])} node pools")

            for pool in pools["node_pools"]:
                if "scalable" in pool["tags"]:
                    pool_id = pool["id"]
                    pool_name = pool["name"]
                    logger.info(f"Updating scalable node pool '{pool_name}' (ID: {pool_id})")

                    path = f"/v2/kubernetes/clusters/{K8S_CLUSTER_ID}/node_pools/{pool_id}"
                    data = {
                        "name": pool["name"],
                        "count": min_nodes,
                        "tags": pool["tags"],
                        "labels": pool["labels"],
                        "taints": pool["taints"],
                        "min_nodes": min_nodes,
                        "max_nodes": max_nodes,
                    }

                    url = f"{DIGITAL_OCEAN_URL}{path}"
                    logger.debug(f"Making PUT request to: {url}")
                    logger.debug(f"Request payload: {data}")

                    response = requests.put(url, json=data, headers=self.header)

                    if response.status_code == 200 or response.status_code == 202:
                        logger.info(f"Successfully updated node pool '{pool_name}': {response.status_code}")
                        logger.debug(f"Response content: {response.content}")
                    else:
                        logger.error(
                            f"Failed to update node pool '{pool_name}': {response.status_code} - {response.content}"
                        )
                else:
                    logger.debug(f"Skipping non-scalable node pool: {pool.get('name', 'unknown')}")

        except Exception as e:
            logger.error(f"Exception occurred while updating node pools: {e}")
            raise

    def get_node_pools(self):
        logger.debug("Fetching node pools from DigitalOcean API")
        path = f"/v2/kubernetes/clusters/{K8S_CLUSTER_ID}/node_pools"
        url = f"{DIGITAL_OCEAN_URL}{path}"

        try:
            logger.debug(f"Making GET request to: {url}")
            response = requests.get(url, headers=self.header)

            if response.status_code == 200:
                result = response.json()
                pool_count = len(result.get("node_pools", []))
                logger.info(f"Successfully retrieved {pool_count} node pools")
                logger.debug(f"Node pools response: {result}")
                return result
            else:
                logger.error(f"Failed to get node pools: {response.status_code} - {response.content}")
                return None

        except Exception as e:
            logger.error(f"Exception occurred while fetching node pools: {e}")
            raise

    def get_node_pool_min(self):
        logger.debug("Getting minimum node count for scalable node pools")

        try:
            pools = self.get_node_pools()
            if not pools or "node_pools" not in pools:
                logger.warning("No node pools found")
                return None

            for pool in pools["node_pools"]:
                if "scalable" in pool["tags"]:
                    min_nodes = pool["min_nodes"]
                    pool_name = pool.get("name", "unknown")
                    logger.info(f"Found scalable node pool '{pool_name}' with min_nodes={min_nodes}")
                    return min_nodes

            logger.warning("No scalable node pools found")
            return None

        except Exception as e:
            logger.error(f"Failed to get node pool minimum: {e}")
            raise

    def update_keda_min_replicas(self, expected_worker_count):
        """
        Update KEDA ScaledObject min/max replicas based on expected traffic load.
        Scale pods proportionally to node count.

        Pod resource requirements (from values-production.yaml):
        - CPU request: 350m (0.35 cores)
        - Memory request: 350M
        - CPU limit: 500m (0.5 cores)
        - Memory limit: 350M

        Typical DigitalOcean node capacity (assuming s-4vcpu-8gb instances):
        - 4 vCPUs, 8GB RAM
        - ~3.5 vCPUs allocatable (after system overhead)
        - ~7GB RAM allocatable (after system overhead)

        Pod capacity per node:
        - CPU constrained: 3.5 cores / 0.35 cores per pod = 10 pods/node
        - Memory constrained: 7GB / 350MB per pod = 20 pods/node
        - Effective: 10 pods per node (CPU is the constraint)

        Conservative scaling: 8 pods per node to leave headroom
        """
        logger.info(f"Updating KEDA min replicas for expected_worker_count={expected_worker_count}")

        try:
            from kubernetes import client, config

            # Load in-cluster config if running in Kubernetes, otherwise local config
            try:
                config.load_incluster_config()
                logger.debug("Successfully loaded in-cluster Kubernetes config")
            except Exception:
                logger.warning("In-cluster config not found, loading local kube config.")
                config.load_kube_config()
                logger.debug("Successfully loaded local Kubernetes config")

            custom_api = client.CustomObjectsApi()

            # Calculate pods based on node capacity
            # Conservative estimate: 8 pods per node (CPU limited at 350m request)
            pods_per_node = 8
            logger.debug(f"Using conservative estimate of {pods_per_node} pods per node")

            # Calculate minimum pods based on worker count
            min_pods = max(3, expected_worker_count * pods_per_node)
            logger.debug(f"Calculated min_pods: max(3, {expected_worker_count} * {pods_per_node}) = {min_pods}")

            # Calculate maximum pods with scaling headroom
            # Allow up to 12 pods per node during peak scaling
            max_pods_per_node = 12
            max_pods = min(100, expected_worker_count * max_pods_per_node)
            logger.debug(f"Calculated max_pods: min(100, {expected_worker_count} * {max_pods_per_node}) = {max_pods}")

            # KEDA ScaledObject details
            namespace = "sln-prod"
            name = "spacelaunchnow-web-comprehensive-scaler"
            logger.info(f"Updating KEDA ScaledObject '{name}' in namespace '{namespace}'")

            # Get current ScaledObject
            logger.debug("Fetching current KEDA ScaledObject configuration")
            scaled_object = custom_api.get_namespaced_custom_object(
                group="keda.sh",
                version="v1alpha1",
                namespace=namespace,
                plural="scaledobjects",
                name=name,
            )

            current_min = scaled_object["spec"].get("minReplicaCount", "unknown")
            current_max = scaled_object["spec"].get("maxReplicaCount", "unknown")
            logger.debug(f"Current KEDA settings: minReplicaCount={current_min}, maxReplicaCount={current_max}")

            # Update min/max replicas
            scaled_object["spec"]["minReplicaCount"] = min_pods
            scaled_object["spec"]["maxReplicaCount"] = max_pods
            logger.debug(f"New KEDA settings: minReplicaCount={min_pods}, maxReplicaCount={max_pods}")

            # Apply the update
            logger.debug("Applying KEDA ScaledObject update")
            custom_api.patch_namespaced_custom_object(
                group="keda.sh",
                version="v1alpha1",
                namespace=namespace,
                plural="scaledobjects",
                name=name,
                body=scaled_object,
            )

            logger.info(
                f"Successfully updated KEDA ScaledObject {name}: minReplicaCount={min_pods}, maxReplicaCount={max_pods}"
            )

        except Exception as e:
            logger.error(f"Failed to update KEDA ScaledObject: {e}")
            logger.debug(f"Exception details: {type(e).__name__}: {str(e)}")
            raise
