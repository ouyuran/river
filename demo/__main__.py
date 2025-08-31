from river_sdk import fingerprint, Job, River, bash, DockerSandboxManager, default_sandbox_creator, sandbox_forker
import cloudpickle
from python_utils import to_int
import joblib
import dill
import hashlib
import base64

NUM = 2

class CreateHelloFileJob(Job):
    def __init__(self, name: str, sandbox_creator=None):
        super().__init__(name, sandbox_creator=sandbox_creator)

    def main(self):
        a = to_int(f"{NUM}")
        bash("echo 'Hello, river12!' > hello_river.txt")
        bash("mkdir /test")
        bash("touch /test/aaa")
        def test_print():
            print("========================test")
        return test_print

    def dumps(self):
        return cloudpickle.dumps(self)

class CatHelloFileJob(Job):
    def __init__(self, name: str, create_job: CreateHelloFileJob):
        super().__init__(
            name,
            sandbox_creator=sandbox_forker(create_job),
            upstreams=[create_job]
        )
        self.create_job = create_job
    # TODO, downstream job cannot be cached
    def main(self):
        result = bash("cat hello_river.txt")
        print(result)
        result = bash("ls", cwd="/test")
        print(result)
        result = bash("echo $TEST_ENV", env={"TEST_ENV": "test env"})
        print(result)
        # if self.create_job.result:
        #     self.create_job.result.main_return()
        

def main():
    job1 = CreateHelloFileJob(
        "create_hello_file1",
        # TODO, if none should use default
        sandbox_creator=default_sandbox_creator(),
    )

    job2 = CatHelloFileJob(
        "cat",
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