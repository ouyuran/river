from sdk.src.job import Job
from sdk.src.task import bash
from sdk.src.sandbox.docker_sandbox import DockerSandboxManager


docker_sandbox_manager = DockerSandboxManager("ubuntu")

class CreateHelloFileJob(Job):
    def __init__(self, name: str, sandbox_creator=None):
        super().__init__(name, sandbox_creator=sandbox_creator)

    def main(self):
        bash("echo 'Hello, river!' > hello_river.txt")
        bash("mkdir /test")
        bash("touch /test/aaa")

class CatHelloFileJob(Job):
    def __init__(self, name: str, create_job: CreateHelloFileJob, sandbox_creator=None):
        super().__init__(name,
            sandbox_creator=sandbox_creator,
            upstreams=[create_job]
        )

    def main(self):
        result = bash("cat hello_river.txt")
        print(result)
        result = bash("ls", cwd="/test")
        print(result)
        result = bash("echo $TEST_ENV", env={"TEST_ENV": "test env"})
        print(result)

def main():

    job1 = CreateHelloFileJob(
        "create_hello_file",
        sandbox_creator=docker_sandbox_manager.creator(image="ubuntu")
    )
    job2 = CatHelloFileJob(
        "cat_hello_file",
        create_job= job1,
        sandbox_creator=docker_sandbox_manager.forker(job1)
    )

    job2.run()

if __name__ == "__main__":
    main()