if __name__ == "__main__":

    parser = argparse.ArgumentParser("Task Executor")
    parser.add_argument("input_string", help="Input String", type=str)
    args = parser.parse_args()

    job_id = uuid.uuid4()
    pod_id = job_id

    """ Steps 1 to 3 is the equivalent of the ./manifestfiles/shuffler_job.yaml """

    # Kubernetes instance
    k8s = Kubernetes()

    # STEP1: CREATE A CONTAINER
    _image = "osama21/osamaor:shuffler"
    _name = "shuffler"
    _pull_policy = "Never"

    shuffler_container = k8s.create_container(_image, _name, _pull_policy, args.input_string)

    # STEP2: CREATE A POD TEMPLATE SPEC
    _pod_name = f"my-job-pod-{pod_id}"
    _pod_spec = k8s.create_pod_template(_pod_name, shuffler_container)

    # STEP3: CREATE A JOB
    _job_name = f"my-job-{job_id}"
    _job = k8s.create_job(_job_name, _pod_spec)

    # STEP4: CREATE NAMESPACE
    _namespace = "jobdemonamespace"
    k8s.create_namespace(_namespace)

    # STEP5: EXECUTE THE JOB
    batch_api = client.BatchV1Api()
    batch_api.create_namespaced_job(_namespace, _job)