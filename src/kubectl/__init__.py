from .clean_up_zombie_pods import clean_up_zombie_pods
from .cmd import k8s

# import os
# import time
#
# import click
# import yaml
# from kubernetes import client, config, watch
#
# pod_name = "mr-scale-you-up"
#
#
# @click.group()
# def k8s():
#     pass
#
#
# def load_pod_manifest():
#     pod_yaml = f"""
# apiVersion: v1
# kind: Pod
# metadata:
#   name: {pod_name}
# spec:
#   containers:
#     - name: my-container
#       image: nginx
#       resources:
#         requests:
#           memory: "8Gi"
#         limits:
#           memory: "8Gi"
# """
#     return yaml.safe_load(pod_yaml)
#
#
# def create_pod(pod_manifest):
#     config.load_kube_config()
#     v1 = client.CoreV1Api()
#     v1.create_pod(body=pod_manifest)
#     click.echo(
#         f"Pod {pod_manifest['metadata']['name']} created successfully with 8Gi memory."
#     )
#
#
# def get_current_namespace(context: str = None) -> str | None:
#     ns_path = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
#     if os.path.exists(ns_path):
#         with open(ns_path) as f:
#             return f.read().strip()
#     try:
#         contexts, active_context = config.list_kube_config_contexts()
#         if context is None:
#             return active_context["context"]["namespace"]
#         selected_context = next(ctx for ctx in contexts if ctx["name"] == context)
#         return selected_context["context"]["namespace"]
#     except (KeyError, StopIteration):
#         return "default"
#
#
# def wait_for_scale_up():
#     v1 = client.CoreV1Api()
#     w = watch.Watch()
#     click.echo("Waiting for a scale-up event...")
#
#     for event in w.stream(v1.list_namespaced_event, namespace=get_current_namespace()):
#         event_type = event["type"]
#         event_obj = event["object"]
#
#         if "scale" in event_obj.reason.lower():
#             click.echo("Scale-up event detected!")
#             w.stop()
#             break
#
#
# def delete_pod():
#     v1 = client.CoreV1Api()
#     click.echo("Deleting the nginx pod...")
#     v1.delete_namespaced_pod(name=pod_name, namespace=get_current_namespace())
#     click.echo("Pod deleted successfully.")
#
#
# @k8s.command()
# def force_scale_up():
#     """
#     Runs a large pod to force a scale-up event
#     """
#     pod_manifest = load_pod_manifest()
#     v1 = client.CoreV1Api()
#     v1.create_namespaced_pod(body=pod_manifest, namespace=get_current_namespace())
#     wait_for_scale_up()
#     delete_pod()
