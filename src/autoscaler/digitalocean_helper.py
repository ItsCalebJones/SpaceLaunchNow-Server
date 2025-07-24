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
