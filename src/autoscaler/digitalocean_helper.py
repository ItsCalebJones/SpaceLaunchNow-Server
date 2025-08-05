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
        self.DO_TOKEN = settings
        self.manager = digitalocean.Manager(token=DO_TOKEN)
        self.header = {"Authorization": f"Bearer {DO_TOKEN}"}

    def get_worker_node_count(self):
        return len(self.manager.get_all_droplets(tag_name="prod-worker"))

    def update_node_pools(self, min_nodes, max_nodes):
        pools = self.get_node_pools()

        for pool in pools["node_pools"]:
            if "scalable" in pool["tags"]:
                path = f"/v2/kubernetes/clusters/{K8S_CLUSTER_ID}/node_pools/{pool['id']}"
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
                response = requests.put(url, json=data, headers=self.header)
                if response.status_code == 200 or response.status_code == 202:
                    logger.info(f"{response.status_code} {response.content}")
                else:
                    logger.error(f"{response.status_code} {response.content}")

    def get_node_pools(self):
        path = f"/v2/kubernetes/clusters/{K8S_CLUSTER_ID}/node_pools"
        # Making a get request
        response = requests.get(f"{DIGITAL_OCEAN_URL}{path}", headers=self.header)
        if response.status_code == 200:
            return response.json()

    def get_node_pool_min(self):
        pools = self.get_node_pools()
        for pool in pools["node_pools"]:
            if "scalable" in pool["tags"]:
                return pool["min_nodes"]

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
        try:
            from kubernetes import client, config

            # Load in-cluster config if running in Kubernetes, otherwise local config
            try:
                config.load_incluster_config()
            except Exception:
                logger.warning("In-cluster config not found, loading local kube config.")
                config.load_kube_config()

            custom_api = client.CustomObjectsApi()

            # Calculate pods based on node capacity
            # Conservative estimate: 8 pods per node (CPU limited at 350m request)
            pods_per_node = 8

            # Calculate minimum pods based on worker count
            min_pods = max(3, expected_worker_count * pods_per_node)

            # Calculate maximum pods with scaling headroom
            # Allow up to 12 pods per node during peak scaling
            max_pods_per_node = 12
            max_pods = min(100, expected_worker_count * max_pods_per_node)

            # KEDA ScaledObject details
            namespace = "sln-prod"
            name = "spacelaunchnow-web-comprehensive-scaler"

            # Get current ScaledObject
            scaled_object = custom_api.get_namespaced_custom_object(
                group="keda.sh",
                version="v1alpha1",
                namespace=namespace,
                plural="scaledobjects",
                name=name,
            )

            # Update min/max replicas
            scaled_object["spec"]["minReplicaCount"] = min_pods
            scaled_object["spec"]["maxReplicaCount"] = max_pods

            # Apply the update
            custom_api.patch_namespaced_custom_object(
                group="keda.sh",
                version="v1alpha1",
                namespace=namespace,
                plural="scaledobjects",
                name=name,
                body=scaled_object,
            )

            logger.info(f"Updated KEDA ScaledObject {name}: minReplicaCount={min_pods}, maxReplicaCount={max_pods}")

        except Exception as e:
            logger.error(f"Failed to update KEDA ScaledObject: {e}")
