from sdk.src.job import Job
from sdk.src.task import ShellTask
from runner.src.local_executor import LocalExecutor

def main():

    init_job = Job("my_init_job", lambda: print("init_job"))

    def job1_main():
        print("job1_main")
        rc, stdout, stderr = ShellTask("""
            echo 'Hello, World!'
        """).execute()
        # print(rc, stdout, stderr)
        return rc, stdout, stderr

    job1 = Job(
        "my_first_job",
        job1_main,
        upstreams=[init_job],
        executor=LocalExecutor()
    )
    job2 = Job(
        "my_final_job", 
        main = lambda my_first_job: print(my_first_job.name, my_first_job._upstreams),
        upstreams=[
            job1,
            init_job
        ]
    )

    job2.run()

if __name__ == "__main__":
    main()