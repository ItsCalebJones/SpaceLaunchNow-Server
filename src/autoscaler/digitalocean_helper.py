import digitalocean
from spacelaunchnow.config import DO_TOKEN


class DigitalOceanHelper:
    def __init__(self):
        self.manager = digitalocean.Manager(token=DO_TOKEN)

    def get_worker_node_count(self):
        return len(self.manager.get_all_droplets(tag_name="prod-worker"))
