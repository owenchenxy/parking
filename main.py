import subprocess
import json
import time
from tools import *

def main():
    all_pods = get_all_vehicles()
    for pod in all_pods:
        migrate_pod_to_node(pod, find_target_node(pod))

# migrate_pod_to_node("busybox1", "kind-worker")
# migrate_pod_to_node("busybox2", "kind-worker")
# migrate_pod_to_node("busybox3", "kind-worker")
# set_node_space("kind-worker", 0)
# set_node_space("kind-worker2", 2)
# set_node_space("kind-worker3", 2)
if __name__ == "__main__":
    main()