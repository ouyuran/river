from .job import Job
from .task import ShellTask

def main():
    def test_job_main(job):
        job.run_task(ShellTask("echo 'Hello, World!'"))

    job1 = Job("test", test_job_main)
    job2 = Job("test2", test_job_main)
    job2.join([job1])
    job1.join([job2])

    job2.run()


if __name__ == "__main__":
    main()