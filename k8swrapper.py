import uuid
from kubernetes import client
from kubernetes import config

class Kubernetes:
    def __init__(self):

        # Init Kubernetes
        self.core_api = client.CoreV1Api()
        self.batch_api = client.BatchV1Api()

    def create_namespace(self, namespace):

        namespaces = self.core_api.list_namespace()
        all_namespaces = []
        for ns in namespaces.items:
            all_namespaces.append(ns.metadata.name)

        if namespace in all_namespaces:
            print(f"Namespace {namespace} already exists. Reusing.")
        else:
            namespace_metadata = client.V1ObjectMeta(name=namespace)
            self.core_api.create_namespace(
                client.V1Namespace(metadata=namespace_metadata)
            )
            print(f"Created namespace {namespace}.")

        return namespace
    @staticmethod
    def create_volume(name, path, server):

        nfsVolume = client.V1Volume(
            name=name,
            nfs=client.V1NFSVolumeSource(
                path=path,
                server=server,
                read_only=False
            )
        )
        return nfsVolume
    @staticmethod
    def create_container(image, name, pull_policy, args):
        container = client.V1Container(
            image=image,
            name=name,
            image_pull_policy=pull_policy,
            args=[args],
            command=["python3", "-u"],
            ports=[{"containerPort":1111}],
            volume_mounts=[
                client.V1VolumeMount(
                    name="nfs-volume",
                    mount_path="/home/oreheem/shared/"
                )
            ],
            resources={"requests":{"cpu":"15"}}
        )

        print(
            f"Created container with name: {container.name}, "
            f"image: {container.image} and args: {container.args}"
        )

        return container

    @staticmethod
    def create_pod_template(pod_name, container, volume):
        pod_template = client.V1PodTemplateSpec(
            spec=client.V1PodSpec(restart_policy="Never", containers=[container], volumes=[volume], host_network=True),
            metadata=client.V1ObjectMeta(name=pod_name, labels={"pod_name": pod_name}),
        )

        return pod_template

    @staticmethod
    def create_job(job_name, pod_template):
        metadata = client.V1ObjectMeta(name=job_name, labels={"job_name": job_name})

        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=metadata,
            spec=client.V1JobSpec(backoff_limit=0, template=pod_template),
        )

        return job

class K8SExecutor:
    def __init__(self):
        config.load_kube_config()
        self.image = "osama21/osamaor:latest"
        self.name = "openroad"
        self.pull_policy = "Always"
        self.namespace = "frank"
        self.k8s = Kubernetes()
        self.k8s.create_namespace(self.namespace)
        self.nfs_volume = self.k8s.create_volume("nfs-volume", "/home/oreheem/shared","10.128.0.92")
        self.batch_api = client.BatchV1Api()
    def runJob(self, jobArgs):
        container = self.k8s.create_container(self.image, self.name, self.pull_policy, jobArgs)
        job_id = uuid.uuid4()
        pod_id = job_id
        # STEP2: CREATE A POD TEMPLATE SPEC
        pod_name = f"my-job-pod-{pod_id}"
        pod_spec = self.k8s.create_pod_template(pod_name, container,self.nfs_volume)

        # STEP3: CREATE A JOB
        job_name = f"my-job-{job_id}"
        job = self.k8s.create_job(job_name, pod_spec)
        
        self.batch_api.create_namespaced_job(self.namespace, job)
        return job_name
    def getJobStatus(self, job_name):
        api_response = self.batch_api.read_namespaced_job_status(job_name, self.namespace)
        return api_response.status