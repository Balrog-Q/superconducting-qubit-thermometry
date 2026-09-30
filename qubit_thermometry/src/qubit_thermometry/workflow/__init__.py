"""Custom LabOne Q Applications-style experiment/analysis workflows.

Modeled on `laboneq_applications`'s `experiments/` + `analysis/` split:

- `workflow.experiments`: `@workflow.task`-decorated `create_*_experiment`
  pulse-sequence builders and their `@workflow.workflow`-decorated
  `*_experiment_workflow` (compile + run), for experiments that
  `laboneq_applications` does not already provide.
- `workflow.analysis`: fitting/plotting functions called from the template
  notebooks after a workflow has run, kept separate so a notebook cell can
  stay a short "create -> run -> analyze" sequence.
"""
