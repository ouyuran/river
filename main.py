from functools import partial
from sdk.src.job import Job
from sdk.src.task import ShellTask
from sdk.src.sandbox.docker_sandbox import DockerSandboxManager


docker_sandbox_manager = DockerSandboxManager("ubuntu")

class MyJob(Job):
    def __init__(self, create_hell_file_job: Job, version: str):
        self.name = "my_job"
        self._create_hell_file_job = create_hell_file_job
        self._upstreams = [create_hell_file_job]
        self.watch(
            files={
                "x": self._workspace_files("build/123.py"),
                "y": self._create_hell_file_job.archive("/123.txt")
            },
            parameters={
                "version": version
            }
        )

    def main(self):
        result = sh("cat hello_river.txt")
        bash("echo 'Hello, river!' > hello_river.txt")
        python("--version")
        cp("/123", "~")
        cp(self._create_hell_file_job.archive("/123.txt"), "~")


def main():

    def create_hello_file():
        result = ShellTask("echo 'Hello, river!' > hello_river.txt").execute()
        print(result)

    job1 = Job(
        "create_hello_file",
        main=create_hello_file,
        sandbox_creator=docker_sandbox_manager.creator(image="ubuntu")
    )

    def cat_hello_file():
        result = ShellTask("cat hello_river.txt").execute()
        job1.xxx # use closure
        print(result)

    job2 = Job(
        "cat_hello_file",
        main=cat_hello_file,
        sandbox_creator=docker_sandbox_manager.forker(job1),
        upstreams={
            "create_job": job1
        }
    )

    job2.run()

if __name__ == "__main__":
    main()