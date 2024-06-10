# MultiPolicyAgent

### Important Files 
- `MultiPolicyAgent.py` : The main file that contains the implementation of the MultiPolicyAgent class. You can find this file in the `submissions/Agent` directory. In order to show appropriate modular design of this file we put this file in `src/agents` directory also. This class works with `src/TwoBotsPlay.py` correctly on this modular design. 
- `utilities.py` : This file contains the implementation of the utilities functions that are used in the MultiPolicyAgent class. You can find this file in the `submissions/Agent` directory. In order to show appropriate modular design of this file we put this file in `src/agents` directory also.

- `Truck.py` : This file contains the implementation of the Truck class. Initially, we have implemented this file as learnable agent. After learning process we are using its function in MultiPolicyAgent class. You can find this file in the `submissions/Agent/agents/Truck` directory. In order to show appropriate modular design of this file we put this file in `src/agents/agents/Truck` directory also.

- `LightTank.py` : This file contains the implementation of the LightTank class. Initially, we have implemented this file as learnable agent. After learning process we are using its function in MultiPolicyAgent class. You can find this file in the `submissions/Agent/agents/LightTank` directory. In order to show appropriate modular design of this file we put this file in `src/agents/agents/LightTank` directory also.

- `HeavyTank.py` : This file contains the implementation of the HeavyTank class. Initially, we have implemented this file as learnable agent. After learning process we are using its function in MultiPolicyAgent class. You can find this file in the `submissions/Agent/agents/HeavyTank` directory. In order to show appropriate modular design of this file we put this file in `src/agents/agents/HeavyTank` directory also.

- `Drone.py` : This file contains the implementation of the Drone class. Initially, we have implemented this file as learnable agent. After learning process we are using its function in MultiPolicyAgent class. You can find this file in the `submissions/Agent/agents/Drone` directory. In order to show appropriate modular design of this file we put this file in `src/agents/agents/Drone` directory also.

- `utilities_truck.py` : This file contains the implementation of the utilities functions that are used in the Truck class. You can find this file in the `submissions/Agent/agents/Truck` directory. In order to show appropriate modular design of this file we put this file in `src/agents/agents/Truck` directory also.

- `utilities_light_tank.py` : This file contains the implementation of the utilities functions that are used in the LightTank class. You can find this file in the `submissions/Agent/agents/LightTank` directory. In order to show appropriate modular design of this file we put this file in `src/agents/agents/LightTank` directory also.

- `utilities_heavy_tank.py` : This file contains the implementation of the utilities functions that are used in the HeavyTank class. You can find this file in the `submissions/Agent/agents/HeavyTank` directory. In order to show appropriate modular design of this file we put this file in `src/agents/agents/HeavyTank` directory also.

- `utilities_drone.py` : This file contains the implementation of the utilities functions that are used in the Drone class. You can find this file in the `submissions/Agent/agents/Drone` directory. In order to show appropriate modular design of this file we put this file in `src/agents/agents/Drone` directory also.

- `models` : This directory contains the trained models of the Truck, LightTank, HeavyTank and Drone classes. You can find this directory in the `submissions/Agent/models` directory. In order to show appropriate modular design of this file we put this directory in `src/agents/models` directory also.

- `train_scripts` : This directory contains the training scripts which is `traincadet.py` of the Truck, LightTank, HeavyTank and Drone classes. You can find this directory in the `submissions/Agent/train_scripts` directory. In order to show appropriate modular design of this file we put this directory in `src/agents/train_scripts` directory also.

Here is the structure of the `src/agents` directory of our submission:
```
|
|--- agents
|    |--- MultiPolicyAgent.py
|    |--- utilities.py
|    |--- agents
|         |--- Truck 
|         |    |--- Truck.py
|         |    |--- utilities_truck.py
|         |--- LightTank
|         |    |--- LightTank.py
|         |    |--- utilities_light_tank.py
|         |--- HeavyTank
|         |    |--- HeavyTank.py
|         |    |--- utilities_heavy_tank.py
|         |--- Drone
|              |--- Drone.py
|              |--- utilities_drone.py
|    |--- models
|         |--- Truck
|         |    |--- Truck.pth
|         |--- LightTank
|         |    |--- LightTank.pth
|         |--- HeavyTank
|         |    |--- HeavyTank.pth
|         |--- Drone
|              |--- Drone.pth
|
```

Here is the structure of the `submissions/Agent` directory of our submission:
```
|
|--- Agent
|    |--- MultiPolicyAgent.py
|    |--- utilities.py
|    |--- agents
|         |--- Truck
|         |    |--- Truck.py
|         |    |--- utilities_truck.py
|         |--- LightTank
|         |    |--- LightTank.py
|         |    |--- utilities_light_tank.py
|         |--- HeavyTank
|         |    |--- HeavyTank.py
|         |    |--- utilities_heavy_tank.py
|         |--- Drone
|              |--- Drone.py
|              |--- utilities_drone.py
|    |--- models
|         |--- Truck
|         |    |--- Truck.pth
|         |--- LightTank
|         |    |--- LightTank.pth
|         |--- HeavyTank
|         |    |--- HeavyTank.pth
|         |--- Drone
|              |--- Drone.pth
|    |--- train_scripts
|         |--- traincadet_truck.py
|         |--- traincadet_light_tank.py
|         |--- traincadet_heavy_tank.py
|         |--- traincadet_drone.py
```


### How to run the code

- First, you need to install the required packages. You can install the required packages by running the following command:
```
pip install -r requirements.txt
```

- Then, you can run the `TwoBotsPlay.py` file to see the performance of the MultiPolicyAgent. You can run the following command to see the performance of the MultiPolicyAgent:
```
python src/TwoBotsPlay.py RiskyValley --agentBlue MultiPolicyAgent --agentRed RandomAgent --render
```

