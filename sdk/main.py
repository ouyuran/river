from .job import Job
from .task import ShellTask

def main():

    init_job = Job("my_init_job", lambda: print("init_job"))

    job1 = Job(
        "my_first_job",
        lambda: ShellTask("echo 'Hello, World!'").execute(),
        upstreams=[init_job]
    )
    job2 = Job(
        "my_final_job", 
        main = lambda my_first_job1, my_second_job: print(my_first_job1.name, my_first_job1._upstreams),
        upstreams=[
            job1,
            Job("my_second_job", lambda: ShellTask("echo 'Hello, World!'").execute())
        ]
    )

    job2.run()


if __name__ == "__main__":
    main()