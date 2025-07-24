from sdk.src.job import Job
from sdk.src.river import River, default_sandbox_creator, sandbox_forker
from sdk.src.task import bash
from sdk.src.sandbox.docker_sandbox import DockerSandboxManager


class CreateHelloFileJob(Job):
    def __init__(self, name: str, sandbox_creator=None):
        super().__init__(name, sandbox_creator=sandbox_creator)

    def main(self):
        bash("echo 'Hello, river!' > hello_river.txt")
        bash("mkdir /test")
        bash("touch /test/aaa")

class CatHelloFileJob(Job):
    def __init__(self, name: str, create_job: CreateHelloFileJob):
        super().__init__(
            name,
            sandbox_creator=sandbox_forker(create_job),
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
        sandbox_creator=default_sandbox_creator(),
    )
    job2 = CatHelloFileJob(
        "cat_hello_file",
        create_job=job1,
    )

    river = River(
        "hello_reiver",
        sandbox_manager=DockerSandboxManager(),
        default_sandbox_config="ubuntu",
        outlets={
            "default": job2,
            "only_create": job1
        }
    )

    river.flow()

if __name__ == "__main__":
    main()