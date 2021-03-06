from hierarchical_state_naive import *
from hierarchical_mcts import *
import random


def line(start: (int, int), increment: (int, int), length: int) -> set:
    return set([(start[0] + k * increment[0], start[1] + k * increment[1]) for
                k in range(length + 1)])


def circle(center: (int, int), radius: int = 1):
    return set([(i, j)
                for i in range(center[0] - radius, center[0] + radius + 1)
                for j in range(center[1] - radius, center[1] + radius + 1)
                if (i - center[0]) ** 2 + (j - center[1]) ** 2 <= radius ** 2])


def hierarchical_example():

    xlim = (0, 10)
    ylim = (0, 10)


    #ridge_targets = {(0, 0): 1, (2, 2): 1, (4, 4): 1, (6, 6): 1, (8, 8): 1, (10, 10): 1}
    ridge_targets = {}
    for i in range(xlim[0], xlim[1]):
        for j in range(ylim[0], ylim[1]):
            #if (i, j) not in ridge_targets.keys():
            #if random.random() < abs(i - xlim[1]/2) / 5.0:
            #    ridge_targets[(i, j)] = 1
            #else:
                ridge_targets[(i, j)] = 0


    ridge_state = KolumboState(time_remains=10)
    target_locs = list(ridge_targets.keys())
    for i in range(len(target_locs)):
        ridge_state.add_location(i, ridge_targets[target_locs[i]], target_locs[i])
    for i in range(len(target_locs)):
        if i+xlim[1] < len(target_locs):
            neighbor = i+xlim[1]
            ridge_state.add_path(i, neighbor, 1)
        if i-xlim[1] > 0:
            neighbor = i-xlim[1]
            ridge_state.add_path(i, neighbor, 1)
        if i % xlim[1] != xlim[1]-1:
            neighbor = i+1
            ridge_state.add_path(i, neighbor, 1)
        if i % xlim[1] != 0:
            neighbor = i-1
            ridge_state.add_path(i, neighbor, 1)
    ridge_state.add_agent(12)

    #caldera_targets = {(0, 3): 1, (0, 5): 1, (0, 7): 1, (2, 9): 1, (4, 9): 1, (6, 9): 1,
    #                    (9, 8): 1, (9, 7): 1, (9, 5): 1, (9, 3): 1, (7, 1): 1,
    #                    (5, 1): 1, (3, 1): 1}
    caldera_targets = {}
    for i in range(xlim[0], xlim[1]):
        for j in range(ylim[0], ylim[1]):
            #if (i, j) not in caldera_targets.keys():
            #if random.random() < ((i - xlim[1]/2)**2 + (j - ylim[1]/2)**2)**0.5 / 10.0:
            #    caldera_targets[(i, j)] = 2
            #else:
            caldera_targets[(i, j)] = 0
            if i == 6 and j == 6:
                caldera_targets[(i, j)] = 100
    #caldera_env = KolumboEnvironment(xlim=(0, 20), ylim=(0, 20), obstacles={},
    #                      targets=caldera_targets, is_border_obstacle_filled=True)
    caldera_state = KolumboState(time_remains=10)
    target_locs = list(caldera_targets.keys())#[(i, j) for i in range(xlim[0], xlim[1]) for j in range(xlim[0], xlim[1])]
    for i in range(len(target_locs)):
        #print(i, caldera_targets[target_locs[i]], target_locs[i])
        caldera_state.add_location(i, caldera_targets[target_locs[i]], target_locs[i])
    for i in range(len(target_locs)):
        if i+xlim[1] < len(target_locs):
            neighbor = i+xlim[1]
            caldera_state.add_path(i, neighbor, 1)
        if i-xlim[1] > 0:
            neighbor = i-xlim[1]
            caldera_state.add_path(i, neighbor, 1)
        if i % xlim[1] != xlim[1]-1:
            neighbor = i+1
            caldera_state.add_path(i, neighbor, 1)
        if i % xlim[1] != 0:
            neighbor = i-1
            caldera_state.add_path(i, neighbor, 1)
    caldera_state.add_agent(1)


    xlimf = (0, 4)
    ylimf = (0, 4)

    falkor_regions = {(1, 1): 'R', (1, 2): 'R', (1, 3): 'R', (1, 4): 'R',
                    (2, 1): 'R', (2, 2): 'C', (2, 3): 'C', (2, 4): 'R',
                    (3, 1): 'R', (3, 2): 'C', (3, 3): 'C', (3, 4): 'R',
                    (4, 1): 'R', (4, 2): 'R', (4, 3): 'R', (4, 4): 'R'}

    falkor_targets = {(1, 1): 'R', (1, 2): 'R', (1, 3): 'R', (1, 4): 'R',
                    (2, 1): 'R', (2, 2): 'C', (2, 3): 'C', (2, 4): 'R',
                    (3, 1): 'R', (3, 2): 'C', (3, 3): 'C', (3, 4): 'R',
                    (4, 1): 'R', (4, 2): 'R', (4, 3): 'R', (4, 4): 'R'}

    #falkor_env = FalkorEnvironment(xlim=(1, 3), ylim=(1, 3), obstacles={},
    #                      feature_map=falkor_targets, is_border_obstacle_filled=True, primitive_states={'C': caldera_state, 'R': ridge_state}, 
    #                      simulation_function = simulate)

    primitive_states = {'C': caldera_state, 'R': ridge_state}
    meta_action_rewards = {'C': 0, 'R': 0}

    for meta_action in primitive_states.keys():
        print(meta_action)
        sim_result = simulate(primitive_states[meta_action])
        sim_result.visualize()
        print(sim_result.reward)
        meta_action_rewards[meta_action] = sim_result.reward

    for target in falkor_targets:
        falkor_targets[target] = meta_action_rewards[falkor_targets[target]]


    print(falkor_regions)
    falkor_state = FalkorState(time_remains=70, region_types=falkor_regions)

    target_locs = list(falkor_targets.keys())
    for i in range(len(target_locs)):
        falkor_state.add_location(i, falkor_targets[target_locs[i]], target_locs[i])
    for i in range(len(target_locs)):
        if i+xlimf[1] < len(target_locs):
            neighbor = i+xlimf[1]
            falkor_state.add_path(i, neighbor, 2)
        if i-xlimf[1] > 0:
            neighbor = i-xlimf[1]
            falkor_state.add_path(i, neighbor, 2)
        if i % xlimf[1] != xlimf[1]-1:
            neighbor = i+1
            falkor_state.add_path(i, neighbor, 2)
        if i % xlimf[1] != 0:
            neighbor = i-1
            falkor_state.add_path(i, neighbor, 2)
    falkor_state.add_agent(1)

    return falkor_state


def simulate(initial_state: KolumboState) -> KolumboState:

    mcts = MonteCarloSearchTree(initial_state)
    state = initial_state.__copy__()
    while not state.is_terminal:
        actions = mcts.search_for_actions(search_depth=3)
        time = state.time_remains
        print("Time remaining: {0}".format(time))
        action = actions[0]
        print(action)
        state = state.execute_action(action)
        mcts.update_root(action)
        if state.is_terminal:
            break
    return state



if __name__ == "__main__":
    print("===== Start of Example 1 =====")

    simulate(initial_state=hierarchical_example()).visualize()
