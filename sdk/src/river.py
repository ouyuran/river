import inspect
from contextvars import ContextVar
from typing import Callable, Any, Optional, List, Dict, Union
from sdk.src.job import Job
from sdk.src.sandbox.base_sandbox import BaseSandboxManager
from sdk.src.sandbox.docker_sandbox import DockerSandboxManager


# Global ContextVar to store the current River instance and its SandboxManager
river_context = ContextVar('river-context')


class River:
    """
    River orchestration system that manages jobs and sandboxes.
    
    The River class hosts a SandboxManager instance and uses outlets (river exit points)
    to control job execution flow with lifecycle hooks.
    """
    
    def __init__(
        self,
        main: Callable[..., Any],
        sandbox_manager: Optional[BaseSandboxManager] = None,
        init_jobs: Optional[List[Job]] = None,
        before_each: Optional[Callable[[Job], None]] = None,
        after_each: Optional[Callable[[Job], None]] = None,
    ):
        """
        Initialize River orchestration system.
        
        Args:
            main: Main function defining jobs and outlets
            sandbox_manager: Manager for sandbox lifecycle. Defaults to DockerSandboxManager("ubuntu")
            init_jobs: List of jobs to run before others
            before_each: Hook function called before each job execution
            after_each: Hook function called after each job execution
        """
        self.sandbox_manager = sandbox_manager or DockerSandboxManager("ubuntu")
        self.init_jobs = init_jobs or []
        self._main = main
        self.before_each = before_each
        self.after_each = after_each
        self.jobs: Dict[str, Job] = {}
        self.outlets: List[Job] = []
        
    def flow(self, outlets: Optional[Union[Job, List[Job]]] = None):
        """
        Let the river flow to specified outlets (exit points).
        
        Args:
            outlets: Target outlets to flow to. If None, flows to all configured outlets.
        """
        # Set the River context so jobs can access the SandboxManager
        token = river_context.set(self)
        
        try:
            # Run initialization jobs first
            for job in self.init_jobs:
                self._run_job_with_hooks(job)
            
            # Execute main function if provided (to set up jobs and outlets)
            self._main()
            
            # Determine target outlets
            target_outlets = self._resolve_outlets(outlets)
            
            # Flow to each outlet (Job.run() handles dependencies automatically)
            for outlet in target_outlets:
                self._flow_to_outlet(outlet)
                
        finally:
            river_context.reset(token)
    
    def flow_to(self, outlets: Union[Job, List[Job]]):
        """
        Explicitly flow to specified outlets.
        
        Args:
            outlets: Target outlets to flow to
        """
        self.flow(outlets)
    
    def _resolve_outlets(self, outlets: Optional[Union[Job, List[Job]]]) -> List[Job]:
        """Resolve outlets parameter to a list of jobs."""
        if outlets is None:
            return self.outlets
        elif isinstance(outlets, Job):
            return [outlets]
        else:
            return outlets
    
    def _flow_to_outlet(self, outlet: Job):
        """
        Flow to a specific outlet using job hooks.
        
        Args:
            outlet: The outlet job to flow to
        """
        self._run_job_with_hooks(outlet)
    
    def _run_job_with_hooks(self, job: Job):
        """
        Run a job with before_each and after_each hooks.
        
        Args:
            job: The job to execute
        """
        if self.before_each:
            self.before_each(job)
        
        try:
            job.run()
        finally:
            if self.after_each:
                self.after_each(job)
    
    def add_jobs(self, jobs: Dict[str, Job]):
        """
        Add multiple jobs to the river.
        
        Args:
            jobs: Dictionary of job_name -> Job
        """
        self.jobs.update(jobs)
    
    def add_job(self, name: str, job: Job):
        """
        Add a single job to the river.
        
        Args:
            name: Name/key for the job
            job: The job to add
        """
        self.jobs[name] = job
    
    def get_jobs(self) -> Dict[str, Job]:
        """Get all jobs managed by this river."""
        return self.jobs.copy()
    
    def get_job(self, name: str) -> Optional[Job]:
        """Get a specific job by name."""
        return self.jobs.get(name)
    
    def set_outlets(self, outlets: List[Job]):
        """
        Set the river outlets (exit points).
        
        Args:
            outlets: List of jobs that serve as river outlets
        """
        self.outlets = outlets
    
    @classmethod
    def get_current_sandbox_manager(cls) -> Optional[BaseSandboxManager]:
        """
        Get the SandboxManager from the current River context.
        
        Returns:
            The current SandboxManager or None if not in River context
        """
        try:
            river = river_context.get()
            return river.sandbox_manager
        except LookupError:
            return None