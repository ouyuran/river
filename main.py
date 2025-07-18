from functools import partial
from sdk.src.job import Job
from sdk.src.task import ShellTask
from sdk.src.sandbox.docker_sandbox import DockerSandboxManager


docker_sandbox_manager = DockerSandboxManager("ubuntu")
create_ubuntu_sandbox = partial(docker_sandbox_manager.create, image="ubuntu")

def main():

    def create_hello_file():
        result = ShellTask("echo 'Hello, river!' > hello_river.txt").execute()
        print(result)

    job1 = Job(
        "create_hello_file",
        main=create_hello_file,
        sandbox_creator=create_ubuntu_sandbox
    )

    def cat_hello_file():
        result = ShellTask("cat hello_river.txt").execute()
        print(result)

    job2 = Job(
        "cat_hello_file",
        main=cat_hello_file,
        sandbox_creator=docker_sandbox_manager.forker(job1.sandbox),
        upstreams={
            "create_job": job1
        }
    )

    job2.run()

if __name__ == "__main__":
    main()