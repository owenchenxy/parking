import subprocess
import yaml
import shlex
import json

def set_node_space(node_name, space):
    subprocess.run(f"kubectl label node {node_name} space={space} --overwrite", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def set_node_position(node_name, position):
    subprocess.run(f"kubectl label node {node_name} position={position} --overwrite", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_all_vehicles():
    # Get all pods with "app" label
    output = subprocess.check_output('kubectl get pods -l app -o json', shell=True).decode()
    pods = json.loads(output)["items"]

    # Get the value of the "position" label for each pod
    vehicles = [(p["metadata"]["name"], p["metadata"]["labels"]["app"], get_pod_position(p["metadata"]["name"])) for p in pods]

    # Filter out pods with missing or invalid position label
    vehicles = [(v[0], v[1], v[2]) for v in vehicles if v[2] is not None]

    # Sort the list of pods by position label in descending order
    vehicles.sort(key=lambda v: v[2], reverse=True)

    # Extract the list of pod names
    return [v[0] for v in vehicles]

def migrate_pod_to_node(pod_name: str, node: str):
    if not node:
        return

    print(f"migrating {pod_name} to {node}")

    # Get the YAML manifest for the pod
    pod_yaml = subprocess.check_output(f"kubectl get pod {pod_name} -o yaml", shell=True).decode()

    # Parse the YAML into a dictionary
    pod_dict = yaml.safe_load(pod_yaml)

    # Update the nodeSelector field to specify the node with the name "mynode"
    old_node = pod_dict["spec"]["nodeName"]
    pod_dict["spec"]["nodeName"] = node

    # Serialize the dictionary back to YAML
    updated_yaml = yaml.dump(pod_dict)

    quoted_yaml = shlex.quote(updated_yaml)

    # Delete the old pod
    subprocess.run(f"kubectl delete pod {pod_name} --force", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Apply the updated YAML manifest
    subprocess.run(f"echo {quoted_yaml}  | kubectl apply -f - ", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Update the value of the "space" label for the node
    space_of_old_node = get_node_space(old_node) + 1
    set_node_space(old_node, space_of_old_node)

    space_of_new_node = get_node_space(node) - 1
    set_node_space(node, space_of_new_node)

def get_node_position(node_name):
    try:
        # Get the value of the "position" label for the node
        label_value = subprocess.check_output(f"kubectl get node {node_name} -o jsonpath='{{.metadata.labels.position}}'", shell=True).decode()

        # Convert the label value to an integer
        position = int(label_value)
        return position
    except subprocess.CalledProcessError:
        # Handle errors when kubectl command fails
        print(f"Error: failed to get position for node {node_name}")
        return None
    except ValueError:
        # Handle errors when label value cannot be converted to integer
        print(f"Error: position label for node {node_name} is not a valid integer")
        return None

def is_control_plan(node_name):
    output = subprocess.check_output(f"kubectl get node {node_name} -o json", shell=True).decode()
    node_info = json.loads(output)["metadata"]
    if "labels" in node_info and "node-role.kubernetes.io/control-plane" in node_info["labels"]:
        return True
    return False

def get_node_space(node_name):
    try:
        # Get the value of the "position" label for the node
        label_value = subprocess.check_output(f"kubectl get node {node_name} -o jsonpath='{{.metadata.labels.space}}'", shell=True).decode()

        # Convert the label value to an integer
        space = int(label_value)
        return space
    except subprocess.CalledProcessError:
        # Handle errors when kubectl command fails
        print(f"Error: failed to get space for node {node_name}")
        return None
    except ValueError:
        # Handle errors when label value cannot be converted to integer
        print(f"Error: space label for node {node_name} is not a valid integer")
        return None
        
def get_pod_position(pod_name):
    try:
        # Get the value of the "position" label for the pod
        label_value = subprocess.check_output(f"kubectl get pod {pod_name} -o jsonpath='{{.metadata.labels.position}}'", shell=True).decode()

        # Convert the label value to an integer
        position = int(label_value)

        return position
    except subprocess.CalledProcessError as e:
        # Handle errors when kubectl command fails
        print(f"Error: failed to get position for pod {pod_name}")
        print(e)
        return None
    except ValueError:
        # Handle errors when label value cannot be converted to integer
        print(f"Error: position label for pod {pod_name} is not a valid integer")
        return None

def find_target_node(pod_name):
    # Get the current node of the pod
    current_node = subprocess.check_output(f"kubectl get pod {pod_name} -o jsonpath='{{.spec.nodeName}}'", shell=True).decode()

    # Get the position of the pod
    pod_position = get_pod_position(pod_name)

    # Get a list of candidate nodes
    nodes = subprocess.check_output("kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}\n{end}'", shell=True).decode().splitlines()

    # Filter nodes where position is greater than pod's position, and the node is not full
    filtered_nodes = []
    for node_name in nodes:
        if is_control_plan(node_name):
            continue
        node_position = get_node_position(node_name)
        node_space = get_node_space(node_name)
        if node_position is not None and int(node_position) > pod_position and node_space > 0:
            filtered_nodes.append((node_name, node_position))

    # Find the target node with the smallest position
    target_node = None
    for node_name, node_position in filtered_nodes:
        if target_node is None or node_position < get_node_position(target_node):
            target_node = node_name

    if target_node is None:
        print(f"No suitable node found for pod {pod_name}")
        return None

    if target_node == current_node:
        print(f"Pod {pod_name} is already on node {current_node}")
        return None

    return target_node
