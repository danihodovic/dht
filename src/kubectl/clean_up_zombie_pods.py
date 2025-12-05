# $ kubectl get po -o json


from kubernetes import client, config

from .cmd import k8s


@k8s.command()
def clean_up_zombie_pods():
    """
    List all pods in the current namespace (default) and print their names and statuses.
    """
    config.load_kube_config()
    # Get the current context's namespace (fallback to "default")
    _, active_context = config.list_kube_config_contexts()
    namespace = active_context.get("context", {}).get("namespace", "default")

    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace=namespace)

    breakpoint()

    # dicom-adapter-send-to-staging-99964997c-zkcts           0/1     ContainerStatusUnknown   1               36h
    # dicom-adapter-send-to-staging-99964997c-zmwwd           0/1     Error                    0               13h

    for pod in pods.items:
        name = pod.metadata.name
        phase = pod.status.phase
        print(f"- {name}: {phase}")
