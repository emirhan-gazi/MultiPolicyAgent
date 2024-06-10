from game import Game
import argparse

parser = argparse.ArgumentParser(description='Agents of Glory')
parser.add_argument('map', metavar='map', type=str,
                    help='Select Map to Play')
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
print(args.map, args.numOfMatch)
red_wins = 0
blue_wins = 0
draws = 0
agents = [args.agentBlue, args.agentRed]

g = Game(args, agents)

for i in range(args.numOfMatch):
    g.reset()
    terminate, blue_score, red_score = g.sim()
    if red_score > blue_score:
        red_wins += 1
    elif blue_score > red_score:
        blue_wins += 1
    else:
        draws += 1
    # print("Blue WinRate: ", (blue_wins)/(args.numOfMatch) * 100)
    if terminate:
        break
    if i % 100 == 0 and i != 0:
        print("Number of match: " + str(i + 1) + "/" + str(args.numOfMatch))
        print("Blue " + "(" + str(args.agentBlue) + ") " + "won " + str(blue_wins) + " games out of " + str(i + 1))
        print("Red " + "(" + str(args.agentRed) + ") " + "won " + str(red_wins) + " games out of " + str(i + 1))
        print("Draw " + str(draws) + " games out of " + str(i + 1))
