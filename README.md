# 🌊 River – Programmable Job Orchestration System

**River** is a lightweight, Python-native orchestration system designed to automate and compose complex task workflows across distributed sandboxes. Inspired by systems like Ansible, Pulumi, and Prefect, River lets you describe task execution logic in Python while centralizing job orchestration in a controller — where all jobs eventually flow toward a final product, like a river.

---

## 🚀 Project Goals

- Use **pure Python** to describe task orchestration logic (Job, Task, conditions, loops, etc.)
- Execute **simple, atomic Tasks** on distributed Sandbox nodes (e.g., shell commands)
- Centralize **Job execution logic** in the Controller for full observability and control
- Keep Sandbox nodes **stateless, secure, and minimal**
- Allow complex, dynamic Task construction at runtime without sacrificing stability

---

## 🧠 Key Concepts

| Concept       | Description |
|---------------|-------------|
| `Task`        | A single unit of work (e.g., shell command), with metadata like environment |
| `Job`         | A collection of `Task` objects, possibly with dependencies or conditional execution |
| `Project`     | A DAG of multiple Jobs that together build a full pipeline |
| `Controller`  | Central brain that executes Job logic, schedules Tasks |
| `Sandbox`     | Remote executor node that receives and runs individual Tasks |

---


##  ✨ Why Controller-Executed Jobs?
Unlike systems that push logic to remote nodes (like Pulumi), River executes the full Job logic on the controller side. This offers:

- ✅ Full Python expressiveness in orchestration (if, for, classes, functions)
- ✅ Centralized control and scheduling logic
- ✅ Fine-grained observability for each Task (start, success, failure)
- ✅ Better security by minimizing logic on Sandbox nodes
- ✅ Easier debugging and reproducibility

## 🧩 Design Principles
Python-native DSL: Users write orchestration logic in Python, not YAML or JSON

Simple execution units: Tasks are atomic and declarative

Separation of concerns: Controller = orchestration, Sandbox = execution

Full observability: Every Task is tracked

Modular and composable: Jobs can form larger DAGs via Projects

## 🔮 Roadmap Highlights
- Python SDK
    - River
    - Job
        - Class inheritant base
        - Fork
        - Copy file: can be interface based, decouple jobs
        - Upstream list -> map
    - Task
        - ShellTask
    - Rich console status
        - Work with log
    - Secret handling
    - Open Telemetry
- Controller
- Runner
    - Local runner
    - Docker runner
    - K8s runner
- Sandbox
    - Block disk, network, env access (python job part should be considered)
    - Container
        - Docker
        - Podman
        - Pod
    - Virtual machine
- Cache
    - Input
    - Job is also an input
        - Analysis job files and 3rd dependencies
- River join river
    - cross languages

## 📦 Project Status
River is under active design and development.

We welcome contributions, feedback, and ideas as we build a robust, expressive automation platform — where all your tasks eventually flow to the final product.