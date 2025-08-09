from river_common import JobStatus, RiverStatus, Status, TaskStatus
from time import sleep
import sys

r = RiverStatus(
    id='000',
    name='river'
)

j1 = JobStatus(
    id='111',
    name='job-1',
    parent_id='000'
)

j2 = JobStatus(
    id='222',
    name='job-2',
    parent_id='000'
)

r.export()
j1.export()
j2.export()
sleep(1)
r.set_status(Status.RUNNING)
r.export()

j1.set_status(Status.RUNNING)
j1.export()
# job1
t1 = TaskStatus(
    id='t1',
    name="task-1",
    parent_id="111"
)

t1.set_status(Status.RUNNING)
t1.export()
sleep(1)
t1.set_status(Status.SUCCESS)
t1.export()

t2 = TaskStatus(
    id='t2',
    name="task-2",
    parent_id="111"
)
t2.set_status(Status.RUNNING)
t2.export()
sleep(1)
t2.set_status(Status.FAILED)
t2.export()
j1.set_status(Status.FAILED)
j1.export()
# job2
t1 = TaskStatus(
    id='t3',
    name="task-a",
    parent_id="222"
)

t1.set_status(Status.RUNNING)
t1.export()
sleep(0.5)
t1.set_status(Status.SUCCESS)
t1.export()

for i in range(10):
    TaskStatus(
        id=f"{i}",
        name="task-a",
        parent_id="222"
    ).export()
    sleep(0.5)

t2 = TaskStatus(
    id='t4',
    name="task-b",
    parent_id="222"
)
t2.set_status(Status.RUNNING)
t2.export()
sleep(1)
t2.set_status(Status.SUCCESS)
t2.export()
j2.set_status(Status.SUCCESS)
j2.export()
