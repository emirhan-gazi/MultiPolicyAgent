import argparse
import ray
import os
from ray.tune import run_experiments, register_env
from agents.HeavyAttack import HeavyAttack

os.environ['CUDA_VISIBLE_DEVICES'] = "1"


parser = argparse.ArgumentParser(description='Cadet Agents')
parser.add_argument('map', metavar='map', type=str,
                    help='Select Map to Train')
parser.add_argument('--mode', metavar='mode', type=str, default="Sim",
                    help='Select Mode[Train,Sim]')
parser.add_argument('--agentBlue', metavar='agentBlue', type=str,
                    help='Class name of Blue Agent')
parser.add_argument('--agentRed', metavar='agentRed', type=str,
                    help='Class name of Red Agent')
parser.add_argument('--numOfMatch', metavar='numOfMatch', type=int, nargs='?', default=1,
                    help='Number of matches to play between agents')
parser.add_argument('--render', action='store_true',
                    help='Render the game')
parser.add_argument('--gif', action='store_true',
                    help='Create a gif of the game, also sets render')
parser.add_argument('--img', action='store_true',
                    help='Save images of each turn, also sets render')

args = parser.parse_args()
agents = [None, args.agentRed]

def main():
    ray.init(num_gpus=1, log_to_driver=True)
    register_env("ray", lambda config: HeavyAttack(args, agents))
    config= {"use_critic": True,
            "log_level": "WARN",
             "num_workers": 1,
             "use_gae": True,
             "lambda": 0.995,
             "kl_coeff": 0.2,
             "rollout_fragment_length": 200,
             "train_batch_size": 4000,
             "sgd_minibatch_size": 128,
             "shuffle_sequences": True,
             "num_sgd_iter": 30,
             "lr": 5e-5,
             "vf_loss_coeff": 0.5,
             "framework": "torch",
             "entropy_coeff": 0.01,
             "entropy_coeff_schedule": None,
             "clip_param": 0.3,
             "vf_clip_param": 10.0,
             "grad_clip": 0.5,
             "kl_target": 0.01,
             "batch_mode": "truncate_episodes",
             "observation_filter": "NoFilter",
             "num_envs_per_worker": 1}
    run_experiments({
        "risky_ppo_recruit": {
            "run": "PPO",
            "env": "ray",
            "stop": {
                "training_iteration": 5e7,
            },
            "config": config,
            "checkpoint_freq": 10,
            # "restore": "/Users/yusufarukguld/Desktop/Project/model/checkpoint_000070/checkpoint-70"
        },
     })
if __name__ == "__main__":
    main()
