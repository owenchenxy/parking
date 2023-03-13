#!/bin/bash

import subprocess
import sys
sys.path.append('..')
from tools import *

#workers = ["edge0", "edge1", "edge2"]
workers = ["kind-worker", "kind-worker2", "kind-worker3"]

# 创建三个pod， app标签分别是car1/car2/car3
for pod_yaml in ["pod3-1.yaml", "pod3-2.yaml", "pod3-3.yaml"]:
    subprocess.run(f"kubectl apply -f {pod_yaml}", shell=True, check=True)

# 创建一个无关的pod， 没有app标签，表示它不对应一个车辆
subprocess.run("kubectl apply -f pod_dummy.yaml", shell=True, check=True)

# 初始化环境，将三个pod都先迁到第一个worker上去
set_node_space(workers[0], 10)
set_node_space(workers[1], 10)
set_node_space(workers[2], 10)

migrate_pod_to_node("busybox1", workers[0])
migrate_pod_to_node("busybox2", workers[0])
migrate_pod_to_node("busybox3", workers[0])

# 将所有node的可用容量设为2
set_node_space(workers[0], 2)
set_node_space(workers[1], 1)
set_node_space(workers[2], 1)

# 运行主程序，开始调度
all_pods = get_all_vehicles()
for pod in all_pods:
    migrate_pod_to_node(pod, find_target_node(pod))