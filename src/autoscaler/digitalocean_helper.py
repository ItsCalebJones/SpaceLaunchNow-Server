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

MINIMUM_POD_COUNT_SINGLE_NODE = 3  # Conservative for single node scenario
# Lowered 8 -> 3 on 2026-08-01. Measured peak traffic over 7 days (launches
# included) was 21.1 RPS = ~11 pods at the 2 RPS/pod trigger, against a floor
# that was demanding 40. The floor only needs to cover baseline plus scale-up
# headroom; KEDA still grows on the CPU/RPS/latency triggers from there.
MINIMUM_POD_COUNT_MULTI_NODE = 3  # Idle floor per node
MAX_POD_COUNT = 100  # Absolute ceiling for KEDA maxReplicaCount


def max_pods_per_node(node_count: int) -> int:
    """Return the per-node pod ceiling for the given pool size.

    Recalibrated 2026-08-01 against production reality. The previous tiers
    (18/12/10/8) were derived from an assumed ~390Mi per pod, but the web pods
    request 700M (≈668Mi) and genuinely use it — measured p95 600Mi, peak
    690Mi — so the request is honest and the old model over-committed by ~1.75x.
    That is what left pods Pending on "Insufficient memory" while the scaler
    believed the pool had room.

    Node allocatable is 6561468Ki ≈ 6408Mi, so at 75% for web workloads:
    floor(6408 * 0.75 / 668) ≈ 7 pods/node.

    The curve peaks in the middle rather than decreasing throughout. A 1-2 node
    pool concentrates the fixed overhead — per-node daemonsets plus singletons
    like valkey and pgbouncer — onto very few nodes, so headroom for web pods is
    tighter there, not looser. Mid-size pools spread that overhead best; large
    pools give it back to baseline traffic load.
    """
    if node_count <= 2:
        return 6  # tiny pool — fixed overhead concentrated on few nodes
    elif node_count <= 4:
        return 7  # best case: matches the 75%-allocatable ceiling at 668Mi/pod
    elif node_count <= 6:
        return 6  # larger peak pool, more baseline load
    else:
        return 5  # very large pool — conservative ceiling


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
        - CPU request: 100m (0.1 cores)
        - Memory request: 200M
        - CPU limit: 500m (0.5 cores)
        - Memory limit: 750M

        Typical DigitalOcean node capacity (assuming s-4vcpu-8gb instances):
        - 4 vCPUs, 8GB RAM
        - ~3.0 vCPUs allocatable (after system + daemonset overhead)
        - ~6GB RAM allocatable (after system + daemonset overhead)

        Pod capacity per node (by requests / scheduling):
        - CPU: 3000m / 100m = 30 pods/node
        - Memory: 6000M / 200M = 30 pods/node

        Actual observed memory per pod (production, measured 2026-08-01):
        - Request 700M (≈668Mi); working set p95 600Mi, peak 690Mi — the request
          is honest, so schedule against it rather than against a lower estimate.
        - Node allocatable memory: 6561468Ki ≈ 6408Mi
        - Safe capacity at 75% of allocatable: floor(6408 * 0.75 / 668) ≈ 7 pods/node

        Pod capacity per node (by limits / burst ceiling):
        - CPU: 3000m / 1000m = 3 pods/node (limits are burst headroom, not binding)
        - Memory: 6000M / 896M = 6 pods/node

        Scaling strategy:
        - <=2 nodes: flat MINIMUM_POD_COUNT_SINGLE_NODE pods min — small-pool idle floor
        - 3+ nodes: MINIMUM_POD_COUNT_MULTI_NODE pods per node min
        - Peak scaling: max_pods_per_node(node_count) pods per node max (decreases as pool grows)
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

            # Small-pool floor: at <=2 nodes (cluster sitting at the DO minimum during quiet
            # hours) keep a flat 5-pod baseline rather than scaling pods per-node. Otherwise
            # the 2-node case would mint 16 pods of headroom we don't need at idle.
            # 3+ nodes means real traffic — scale pods proportionally.
            if expected_worker_count <= 2:
                min_pods = MINIMUM_POD_COUNT_SINGLE_NODE
                logger.debug(f"Small pool ({expected_worker_count} nodes): flat floor of {min_pods} pods")
            else:
                pods_per_node = MINIMUM_POD_COUNT_MULTI_NODE
                min_pods = max(3, expected_worker_count * pods_per_node)
                logger.debug(f"Multi-node deployment: max(3, {expected_worker_count} * {pods_per_node}) = {min_pods}")

            # Calculate maximum pods — ceiling shrinks as pool grows
            pods_ceiling = max_pods_per_node(expected_worker_count)
            max_pods = min(MAX_POD_COUNT, expected_worker_count * pods_ceiling)
            logger.debug(
                f"Calculated max_pods: min({MAX_POD_COUNT}, {expected_worker_count} * {pods_ceiling}) = {max_pods}"
            )

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
            logger.info(f"Current KEDA ScaledObject '{name}' settings:")
            logger.info(f"  - minReplicaCount: {current_min}")
            logger.info(f"  - maxReplicaCount: {current_max}")
            logger.debug(f"Current KEDA settings: minReplicaCount={current_min}, maxReplicaCount={current_max}")

            # Log additional KEDA configuration details
            triggers = scaled_object["spec"].get("triggers", [])
            logger.debug(f"KEDA triggers configured: {len(triggers)}")
            for i, trigger in enumerate(triggers):
                trigger_type = trigger.get("type", "unknown")
                logger.debug(f"  Trigger {i + 1}: type={trigger_type}")

            idle_replica_count = scaled_object["spec"].get("idleReplicaCount", "not set")
            polling_interval = scaled_object["spec"].get("pollingInterval", "not set")
            logger.debug(
                f"Additional KEDA settings: idleReplicaCount={idle_replica_count}, pollingInterval={polling_interval}"
            )

            # Update min/max replicas
            scaled_object["spec"]["minReplicaCount"] = min_pods
            scaled_object["spec"]["maxReplicaCount"] = max_pods
            logger.info(f"Updating KEDA ScaledObject '{name}' replica settings:")
            logger.info(f"  - New minReplicaCount: {min_pods} (was: {current_min})")
            logger.info(f"  - New maxReplicaCount: {max_pods} (was: {current_max})")
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
