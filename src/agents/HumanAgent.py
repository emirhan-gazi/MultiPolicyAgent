class HumanAgent:
    def __init__(self,team,action_lenght):
        self.tagToString = {
        1: "Truck",
        2: "LightTank",
        3: "HeavyTank",
        4: "Drone",
        }
        self.movement_grid = [[(0,0),(-1,0),(0,-1),(1,0),(1,1),(0,1),(-1,1)],
        [(0,0),(-1,-1),(0,-1),(1,-1),(1,0),(0,1),(-1,0)]]
        self.team = team
        self.enemy_team = (team+1)%2
        self.action_lenght = action_lenght
    def decode_state(self, state):
        
        score = state['score']
        turn = state['turn']
        max_turn = state['max_turn']
        units = state['units']
        hps = state['hps']
        bases = state['bases']
        res = state['resources']
        load = state['loads']

        self.y_max, self.x_max = res.shape
        self.my_units = []
        self.enemy_units = []
        self.resources = []
        for i in range(self.y_max):
            for j in range(self.x_max):
                if units[self.team][i][j]<6 and units[self.team][i][j] != 0:
                    self.my_units.append(
                    {   
                        'unit': units[self.team][i][j],
                        'tag': self.tagToString[units[self.team][i][j]],
                        'hp': hps[self.team][i][j],
                        'location': (i,j),
                        'load': load[self.team][i][j]
                    }
                    )
                if units[self.enemy_team][i][j]<6 and units[self.enemy_team][i][j] != 0:
                    self.enemy_units.append(
                    {   
                        'unit': units[self.enemy_team][i][j],
                        'tag': self.tagToString[units[self.enemy_team][i][j]],
                        'hp': hps[self.enemy_team][i][j],
                        'location': (i,j),
                        'load': load[self.enemy_team][i][j]
                    }
                    )
                if res[i][j]==1:
                    self.resources.append((i,j))
                if bases[self.team][i][j]:
                    self.my_base = (i,j)
                if bases[self.enemy_team][i][j]:
                    self.enemy_base = (i,j)

    def action(self, state):
        self.decode_state(state)
        movement = []
        target = []
        location = []
        print('HumanAgent')
        for u in self.my_units:
            location.append(u['location'])
            m = -1
            t_x = -1
            t_y = -1
            if u['hp']>0:
                while m < 0 or m > 6:
                    m = int(input("Movement for "+ u['tag']+":"))
                    if m < 0 or m > 6:
                        print("Movement should be between [0-6]")
                if u['tag'] != 'Truck' and m==0:
                    while t_x<0 or t_y<0 or t_x>self.x_max-1 or t_y>self.y_max-1:
                        y,x = input("Target for "+ u['tag']+"(y,x):").split()
                        t_y = int(y)
                        t_x = int(x)
                        if t_x<0 or t_y<0 or t_x>self.x_max-1 or t_y>self.y_max-1:
                            print("Target should be between y:[0-"+str(self.y_max-1)+"], x:[0-"+str(self.x_max-1)+"]")
            movement.append(m)
            target.append((t_y,t_x))
        assert len(movement) == self.action_lenght and len(target) == self.action_lenght
        train = 0
        return (location,movement,target, train)