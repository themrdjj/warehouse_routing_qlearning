import numpy as np
import random
import time
from itertools import chain, combinations
from more_itertools import sort_together
from math import comb  # Leave this for alternative calculation of number of states, might be useful for debugging
import termtables as tt
import matplotlib.pyplot as plt
import pandas as pd


class Warehouse:
    """Warehouse class, capacitated version. Includes single agent. Does not include any training methods."""
    def __init__(self, n_shelve_units=2, unit_width=1, n_pick_pts=1, capacity=1, pick_pts_rand=True):
        if n_shelve_units % 2 or unit_width < 1:  # check inputs
            raise ValueError("Invalid inputs for warehouse dimensions/layout!")
        self.n_shelve_units = n_shelve_units  # number of shelve units, must be even
        self.unit_width = unit_width  # width of each shelve unit
        self.n_pick_pts = n_pick_pts  # number of pick points
        self.grid_size = (1 + n_shelve_units//2*3, unit_width*2 + 3)  # grid size of warehouse: (rows, columns)
        self.corridors, self.possible_actions, self.action_symbols = self.get_corridors()  # get corridor fields
        self.shelves = np.setdiff1d(range(np.prod(self.grid_size)), self.corridors)  # get shelve fields
        if pick_pts_rand:
            self.pick_pts = np.random.choice(self.shelves, n_pick_pts, replace=False)  # choose pick points randomly
        else:
            self.pick_pts = [13, 17, 18]  # for the report
        self.capacity = capacity  # capacity of agent, each pick point has a load of 1
        self.start = np.prod(self.grid_size) - self.grid_size[1]//2 - 1  # starting field
        self.states = self.get_states()  # get states
        self.action_str = ["up", "right", "down", "left"]
        self.actions = range(len(self.action_str))
        self.n_states = len(self.states)
        self.n_actions = len(self.actions)
        self.position = self.start  # set starting position
        self.state = (self.position, 0, ())  # set starting state

    def get_states(self):
        """Return list of all states. A state has the format (x, l, (a, b)) where x is the index of the current,
        position, l the current loading and (a, b) a sorted tuple of the pick position that have been visited."""
        # following line could be shortened with more_itertools.powerset as done in warehouse.py, left here as example
        pick_pt_comb = list(chain(*(list(combinations(self.pick_pts, i)) for i in range(len(self.pick_pts) + 1))))
        return [(corridor, loading, tuple(sorted(ppc)))
                for corridor in self.corridors for loading in range(self.capacity+1) for ppc in pick_pt_comb]

    def get_corridors(self):
        """Return list of corridor fields, associated list of possible actions and associated list of action unicode
        symbols. Sorted by assorting field index."""
        # Assign columns from left to right (always 3). Take into account special cases.
        cols, col_actions, col_action_symbols = [], [], []
        for i in range(3):
            col_start_idx = [0, self.grid_size[1]//2, self.grid_size[1]-1]
            cols += np.arange(col_start_idx[i], np.prod(self.grid_size), self.grid_size[1]).tolist()
            col_i_actions = [(0, 2)] * self.grid_size[0]
            col_i_action_symbols = [8597] * self.grid_size[0]
            if i == 0:  # first column
                col_i_actions[0], col_i_action_symbols[0] = (1, 2), 8600  # UL corner
                for j in range(self.n_shelve_units//2):
                    col_i_actions[(j+1)*3], col_i_action_symbols[(j+1)*3] = (0, 1, 2), 8614  # intermediate corners
                col_i_actions[-1], col_i_action_symbols[-1] = (0, 1), 8599  # BL corner
            if i == 1:  # second column
                col_i_actions[0], col_i_action_symbols[0] = (1, 2, 3), 8615  # upper intermediate corner
                for j in range(self.n_shelve_units//2):
                    col_i_actions[(j+1)*3], col_i_action_symbols[(j+1)*3] = (0, 1, 2, 3), 8623  # intermediate corners
                col_i_actions[-1], col_i_action_symbols[-1] = (0, 1, 3), 8613  # bottom intermediate corner (start)
            if i == 2:  # second column
                col_i_actions[0], col_i_action_symbols[0] = (2, 3), 8601  # UR corner
                for j in range(self.n_shelve_units//2):
                    col_i_actions[(j+1)*3], col_i_action_symbols[(j+1)*3] = (0, 2, 3), 8612  # intermediate corners
                col_i_actions[-1], col_i_action_symbols[-1] = (0, 3), 8598  # BR corner
            col_actions += col_i_actions
            col_action_symbols += col_i_action_symbols

        # Assign rows, leave out columns
        rows = []
        row_starts = range(0, 3*self.grid_size[1]*(self.n_shelve_units//2+1), 3*self.grid_size[1])
        for i in range(self.n_shelve_units//2+1):
            row_i = list(range(row_starts[i] + 1, row_starts[i] + self.grid_size[1] - 1))
            rows += row_i[:len(row_i)//2] + row_i[len(row_i)//2+1:]
        row_actions = [(1, 3)] * len(rows)
        row_action_symbols = [8596] * len(rows)

        # Collect all, sort by index and return
        return sort_together([cols+rows, col_actions+row_actions, col_action_symbols+row_action_symbols])

    def pos_tuple(self, idx):
        """Convert single field index to grid position tuple."""
        return idx//self.grid_size[1], idx % self.grid_size[1]

    def reset(self):
        """Reset position of agent and reset state."""
        self.position = self.start
        self.state = (self.position, 0, ())

    def render(self):
        """Render current state of warehouse as table in console."""
        repr = np.empty(self.grid_size, dtype="<U2")  # initialise warehouse
        for shelf in self.shelves:  # show shelves
            repr[self.pos_tuple(shelf)] = chr(9633)
        for pt in self.pick_pts:  # show pick points
            repr[self.pos_tuple(pt)] = chr(9635)
        repr[self.pos_tuple(self.position)] = "x"  # show current position of agent
        tt.print(repr)

    def render_possible_actions(self):
        """Render warehouse with possible actions for each corridor field."""
        repr = np.empty(self.grid_size, dtype="<U2")  # initialise warehouse
        for shelf in self.shelves:  # show shelves
            repr[self.pos_tuple(shelf)] = chr(9633)
        for pt in self.pick_pts:  # show pick points
            repr[self.pos_tuple(pt)] = chr(9635)
        for i, corridor in enumerate(self.corridors):
            repr[self.pos_tuple(corridor)] = chr(self.action_symbols[i])
        tt.print(repr)

    def step(self, action):
        """Take step. Update state. Return new state, reward and episode termination boolean."""
        done = False

        # Determine new position
        if action in self.possible_actions[self.corridors.index(self.state[0])]:  # if action is valid for current field
            reward = -1  # general reward for motion
            if action == 0:  # up
                new_position = self.state[0] - self.grid_size[1]
            if action == 1:  # right
                new_position = self.state[0] + 1
            if action == 2:  # down
                new_position = self.state[0] + self.grid_size[1]
            if action == 3:  # left
                new_position = self.state[0] - 1
        else:  # action was invalid, so no movement
            reward = -2
            new_position = self.state[0]

        # Check if new position is above or below unvisited pick point and the agent has free capacity or if episode is
        # done (arrived at start having visited all pick points)
        if new_position + self.grid_size[1] in np.setdiff1d(self.pick_pts, self.state[2]) and \
                self.state[1] < self.capacity:  # if above
            new_pick_state = tuple(sorted(self.state[2] + tuple([new_position + self.grid_size[1]])))
            new_loading = self.state[1] + 1
            reward = 10
        elif new_position - self.grid_size[1] in np.setdiff1d(self.pick_pts, self.state[2]) and \
                self.state[1] < self.capacity:  # if below
            new_pick_state = tuple(sorted(self.state[2] + tuple([new_position - self.grid_size[1]])))
            new_loading = self.state[1] + 1
            reward = 10
        elif new_position == self.start:  # if agent at starting point
            new_loading = 0  # unload
            new_pick_state = self.state[2]  # don't change pick state
            if not np.setdiff1d(self.pick_pts, self.state[2]).any():  # if episode is done
                new_pick_state = self.state[2]
                reward = 100
                done = True
            else:  # reward for unloading if not done yet?
                pass
                # reward = ?
        else:  # don't change pick and loading state
            _, new_loading, new_pick_state = self.state

        # Set new position and new state
        self.position = new_position
        new_state = (new_position, new_loading, new_pick_state)
        self.state = new_state

        return new_state, reward, done


def q_table_to_action_list(q_table, env):
    """Get optimal list of actions from q-table."""
    env.reset()
    actions = []
    done = False
    while not done:
        action = np.argmax(q_table[env.states.index(env.state), :])
        actions.append(action)
        done = env.step(action)[-1]
    return actions


if __name__ == "__main__":
    env = Warehouse(2, 4, 3, 2, False)  # create warehouse
    #  n_shelve_units, unit_width, n_pick_pts, capacity):
    env.render()

    q_table = np.zeros((env.n_states, env.n_actions))  # initialise q table

    n_episodes = 10000  # number of episodes
    n_steps = 100  # maximum number of steps per episode

    l_rate = 0.75  # learning rate
    d_rate = 0.99  # discount rate
    e_rate = 1  # exploration rate
    max_e_rate = 1
    min_e_rate = 0.001
    e_d_rate = 0.1  # exploration decay route

    rewards = []

    dones = 0
    max_r = 0

    start_time = time.time()
    # For each episode
    for episode in range(n_episodes):
        # Initialise episode
        env.reset()  # reset environment
        done = False
        rewards_current = 0
        actions_current = []

        # For each step in episode
        for step in range(n_steps):
            # Pick action
            if random.uniform(0, 1) > e_rate:  # exploit
                action = np.argmax(q_table[env.states.index(env.state), :])  # pick best action from current state
            else:  # explore
                action = random.choice(env.actions)  # choose random action

            # Take action - get new state, reward and termination boolean
            old_state_idx = env.states.index(env.state)
            new_state, reward, done = env.step(action)
            actions_current.append(action)

            # Update q_table
            q_table[old_state_idx, action] = q_table[old_state_idx, action] * (1 - l_rate) \
                + l_rate * (reward + d_rate * np.max(q_table[env.states.index(new_state), :]))

            # Add reward
            rewards_current += reward

            # Break loop if done
            if done:
                dones += 1
                break

        # Add episode reward to list
        rewards.append(rewards_current)

        # Update exploration rate
        e_rate = min_e_rate + (max_e_rate-min_e_rate) * np.exp(-e_d_rate*episode)

        if rewards_current > max_r:
            max_r = rewards_current
            actions_max = actions_current

        if not episode % 1000 and episode > 0:
            print(episode, rewards[-1], len(actions_current), e_rate)

    print("Done in {} seconds.".format(round(time.time() - start_time, 3)))

    plt.plot(range(n_episodes), rewards)
    plt.show()

    q_table_pd = pd.DataFrame(q_table, index=env.states, columns=env.action_str).round(3)
    # print(q_table_pd)

    print(q_table_to_action_list(q_table, env))
