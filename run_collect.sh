export CARLA_ROOT=carla
export LEADERBOARD_ROOT=leaderboard
export SCENARIO_RUNNER_ROOT=scenario_runner
export EXPERTS_ROOT=experts
export DEPENDENCY=pytorch-image-models
export PYTHONPATH=$PYTHONPATH:${LEADERBOARD_ROOT}:${SCENARIO_RUNNER_ROOT}:${EXPERTS_ROOT}:${DEPENDENCY}

python ./experts/agents/replay/run_data_collect.py