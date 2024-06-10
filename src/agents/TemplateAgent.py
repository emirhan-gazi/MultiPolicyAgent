class TemplateAgent:
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

    def action(self, state):
        y_max, x_max = state["resources"].shape
        location = [] # (y,x) list of tuples
        movement = [] # [0,6] list of integers
        target = [] # (y,x) list of tuples
        train = [] # integer
        '''
        '''
        assert len(movement) == self.action_lenght and len(target) == self.action_lenght
        return (location,movement,target,train)
