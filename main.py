import subprocess
import json
import time
from tools import *

def main():
    all_pods = get_all_vehicles()
    for pod in all_pods:
        migrate_pod_to_node(pod, find_target_node(pod))

if __name__ == "__main__":
    main()