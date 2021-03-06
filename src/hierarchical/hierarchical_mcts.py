import math
import random
from hierarchical_state_naive import AbstractState, AbstractAction


class Node(object):
    def __init__(self, state):
        # type: (AbstractState) -> None
        """ Create a Node object with given state
        """
        self._state = state
        self._parent = None
        self._untried_edges = self._state.possible_actions
        self.children = {}  # {AbstractAction: AbstractState}
        self.tot_reward = 0
        self.num_samples = 0

    @property
    def state(self):
        # type: () -> AbstractState
        return self._state

    @property
    def is_terminal(self):
        return self._state.is_terminal

    @property
    def parent(self):
        # type: () -> Node
        return self._parent

    @property
    def depth(self):
        # type: () -> int
        """ The depth (distance to the root, whose parent is None, plus 1) of
            the node
        """
        depth = 0
        node = self
        while node:
            depth += 1
            node = node.parent
        return depth

    @property
    def unused_edges(self):
        # type: () -> list
        return self._untried_edges

    @property
    def is_expanded(self):
        # type: () -> bool
        """ Whether all possible actions have been tried
        """
        return len(self._untried_edges) == 0

    def add_child(self, action):
        # type: (AbstractAction) -> Node
        """ Add a child node and set the parent of the child node and return the
            child node
        :param action: The action that would lead the current node to the child
            node
        :return: The child node
        """
        child = Node(self._state.execute_action(action))
        if action in self._untried_edges:
            self._untried_edges.remove(action)
        self.children[action] = child
        child._parent = self
        return child

    def remove_child(self, child):
        # type: (Node) -> Node
        """ Remove a child node from this node
        :param child: The child node
        """
        act = None
        for action, node in self.children.items():
            if node == child:
                #child._parent = None
                act = action
        if act:
            del self.children[act]
        else:
            raise ValueError("The node does not have the given child node")
        return self

    def __eq__(self, other):
        # type: (Node) -> bool
        return (self.__class__ == other.__class__ and
                self._state == other._state and self._parent == other._parent)

    def __str__(self):
        # type: () -> str
        return str(self._state)


def select(node, exploration_const=1.0):
    # type: (Node, float) -> (AbstractAction, Node)
    """ Select the best child node based on UCB; if there are multiple
        child nodes with the max UCB, randomly select one
    :param node: The parent node
    :param exploration_const: The exploration constant in UCB formula
    :return: The action and the corresponding best child node
    """
    max_val = -float('inf')
    max_actions = []
    for action, child in node.children.items():
        node_val = (child.tot_reward / child.num_samples
                    + exploration_const *
                    math.sqrt(2.0 * math.log(node.num_samples) /
                              child.num_samples))
        if node_val > max_val:
            max_val = node_val
            max_actions = [action]
        elif node_val == max_val:
            max_actions.append(action)
    max_action = random.choice(max_actions)
    return max_action, node.children[max_action]


def expand(node):
    # type: (Node) -> Node
    """ Randomly select an untried action and create a child node based on it
        Return the new child node
    :param node: The parent node
    :return: The child node
    """
    if node.is_expanded:
        raise Exception("Should not expand a node that has already"
                        " been expanded")
    action = random.choice(node.unused_edges)
    return node.add_child(action)


def random_rollout_policy(state):
    # type: (AbstractState) -> float
    """ The default policy for simulation is to randomly (uniform distribution)
        select an action to update the state and repeat the simulation until
        a terminal state is reached
    :param state: The starting state
    :return: The reward at the terminal node
    """
    while not state.is_terminal:
        action = random.choice(state.possible_actions)
        state = state.execute_action(action)
    return state.reward

def clone_rollout_policy(state, meta_action, meta_action_root, depth):
    # type: (AbstractState) -> float
    """ The cloning rollout policy selects the actions the meta-action tree would have taken
        at a given depth.
    :param state: The starting state
    :param meta_action: The meta-action name
    :param meta_action_root: The root node of the meta-action search tree over primitives
    :param depth: the depth to which the search has already gone
    :return: The reward at the terminal node
    """

    # 

    cur = meta_action_root

    # search meta action policy to appropriate depth
    for i in range(depth):
        if len(cur.children) == 0:
            return random_rollout_policy(cur.state)
        action = select(cur)[0]
        cur =cur.children[action]

    # follow meta action policy from depth to termination
    while not state.is_terminal:
        if len(cur.children) == 0:
            return random_rollout_policy(cur.state)
        action = select(cur)[0]
        state = state.execute_action(action)
        cur = cur.children[action]
    return state.reward

def backpropagate(node, reward=0.0):
    # type: (Node, float) -> None
    """ Propagate the reward and sample count from the specified leaf node
        back all the way to the root node (the node with no parent)
    :param node: The node where the reward starts
    :param reward: The reward at the terminal state
    """
    while node is not None:
        node.num_samples += 1
        node.tot_reward += reward
        node = node.parent


def execute_round(root, max_tree_depth=15,
                  tree_select_policy=select, tree_expand_policy=expand,
                  rollout_policy=random_rollout_policy,
                  backpropagate_method=backpropagate,
                  meta_action=None, meta_action_root=None, depth_cur=0):
    # type: (Node, int, callable, callable, callable, callable) -> None
    """ Perform selection, expansion, simulation and backpropagation with
        one sample
        :param root: The Node object from which the select step starts
        :param max_tree_depth: Expansion will not occur if the maximum tree
            depth is reached
        :param tree_select_policy: The selection part of tree policy
        :type tree_select_policy: A function that takes a Node object as input
            and returns the selected (Action, Node) tuple
        :param tree_expand_policy: The expansion part of tree policy
        :type tree_expand_policy: A function that takes a Node object as input,
            add a new dict item to its children member and returns the generated
            Node object
        :param rollout_policy: The policy used to perform simulation
        :type rollout_policy: The function that takes a State as input, simulate
            by Monte Carlo method until a terminal state is met, and returns
            the reward of the terminal state
        :param backpropagate_method: The method to update visit count and
            reward from the simulation result
        :type backpropagate_method: The function that takes a Node (where
            the simulation starts) as input, performs simulation and returns
            the final reward
    """
    cur = root
    while cur.is_expanded and cur.depth < max_tree_depth:
        act, cur = tree_select_policy(cur, exploration_const=1.0)
    simulation_node = tree_expand_policy(
        cur) if max_tree_depth > cur.depth else cur

    #if meta_action:# and random.random() < 0.5: # tunable parameter adjusts meta policy following rate
    #    reward = clone_rollout_policy(simulation_node.state, meta_action, meta_action_root, depth_cur)
    #else:
    reward = rollout_policy(simulation_node.state)

    backpropagate_method(simulation_node, reward)


class MonteCarloSearchTree:
    def __init__(self, initial_state, samples=1000, max_tree_depth=1000,
                 tree_select_policy=select, tree_expand_policy=expand,
                 rollout_policy=random_rollout_policy,
                 backpropagate_method=backpropagate, meta_action=None, meta_action_root=None):
        # type: (AbstractState, int, int, callable, callable, callable, callable) -> None
        """ Create a MonteCarloSearchTree object
        :param initial_state: The initial state
        :param samples: The number of samples to generate to obtain the best
                action
        :param max_tree_depth: The maximal allowable number of nodes in the tree
        :param tree_select_policy: The selection part of tree policy
        :type tree_select_policy: A function that takes a Node object as input
            and returns the selected (Action, Node) tuple
        :param tree_expand_policy: The expansion part of tree policy
        :type tree_expand_policy: A function that takes a Node object as input,
            add a new dict item to its children member and returns the generated
            Node object
        :param rollout_policy: The simulation function
        :type: A function that takes a state as input, perform simulation until
                a terminal state, and returns the reward of the final state
        :param backpropagate_method: The method to update visit count and
            reward from the simulation result
        :type backpropagate_method: The function that takes a Node (where
            the simulation starts) as input, performs simulation and returns
            the final reward
        """
        if samples <= 0 or max_tree_depth <= 1:
            raise ValueError("The number of samples must be positive")
        self._max_samples = samples
        self._tree_select_policy = tree_select_policy
        self._tree_expand_policy = tree_expand_policy
        self._rollout_policy = rollout_policy
        self._back_propagate_policy = backpropagate_method
        self._root = Node(initial_state)
        self._depth_cur = 0
        self._max_tree_depth = max_tree_depth
        self._meta_action = meta_action
        self._meta_action_root=meta_action_root

    def _search(self, node, search_depth=1):
        # type: (Node, int) -> (float, list)
        """ Recursively search for a best sequence of actions
            :return: The reward of the last (deepest child node) and the
                     sequence of actions that leads to the optimal child node
        """
        if not node.children or search_depth == 0:
            print('err')    
            return node.tot_reward / node.num_samples, []
        elif search_depth == 1:
            max_val = -float('inf')
            max_actions = []
            for action, child in node.children.items():
                node_val = child.tot_reward / child.num_samples
                if node_val > max_val:
                    max_val = node_val
                    max_actions = [action]
                elif node_val == max_val:
                    max_actions.append(action)
            max_action = random.choice(max_actions)
            child = node.children[max_action]
            return child.tot_reward / child.num_samples, [max_action]
        best_reward = -math.inf
        best_act_seq = []
        for action, child in node.children.items():
            child_reward, child_act_seq = self._search(child, search_depth - 1)
            if child_reward > best_reward:
                best_act_seq = [action] + child_act_seq
                best_reward = child_reward
        return best_reward, best_act_seq

    def search_for_actions(self, search_depth=1, random_seed=None):
        # type: (int, int) -> list
        """ With given initial state, obtain the best actions to take by MCTS
        :param search_depth: How many steps of actions are wanted
        :param random_seed: When not None, set the random seed before running
        :return: The best actions
        :rtype: A list of AbstractAction objects
        """
        if random_seed is not None:
            random.seed(random_seed)
        for _ in range(self._max_samples):
            execute_round(self._root, max_tree_depth=self._max_tree_depth,
                          tree_select_policy=self._tree_select_policy,
                          tree_expand_policy=self._tree_expand_policy,
                          rollout_policy=self._rollout_policy,
                          backpropagate_method=self._back_propagate_policy,
                          meta_action=self._meta_action,
                          meta_action_root=self._meta_action_root,
                          depth_cur=self._depth_cur)
        return self._search(self._root, search_depth)[1]

    def update_root(self, action):
        # type: (AbstractAction) -> MonteCarloSearchTree
        """ Update the root node to reflect the new state after an action is
            taken
        :param action: The action that brings a new state
        """
        if action in self._root.children:
            new_root = self._root.children[action]
        else:
            new_root = self._root.add_child(action)
        #self._root.remove_child(new_root) # remove ?????
        self._root = new_root
        self._depth_cur += 1
        return self

    def revert_top_root(self):
        toproot = self._root
        while self._root.parent:
            self._root = self._root.parent
        return toproot
