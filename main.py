from functools import partial
from sdk.src.job import Job
from sdk.src.task import bash
from sdk.src.sandbox.docker_sandbox import DockerSandboxManager


docker_sandbox_manager = DockerSandboxManager("ubuntu")

def main():

    def create_hello_file():
        result = bash("echo 'Hello, river!' > hello_river.txt")
        bash("mkdir /test")
        bash("touch /test/aaa")

    job1 = Job(
        "create_hello_file",
        main=create_hello_file,
        sandbox_creator=docker_sandbox_manager.creator(image="ubuntu")
    )

    def cat_hello_file():
        result = bash("cat hello_river.txt")
        print(result)
        result = bash("ls", cwd="/test")
        print(result)
        result = bash("echo $TEST_ENV", env={"TEST_ENV": "test env"})
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