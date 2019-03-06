import itertools
import numpy as np
import wombat.choice as choice


class Episode:
    def __init__(self, initial_observation=None, num_possible_actions=None):
        self.observations = [initial_observation] if initial_observation is not None else []
        self.actions = []
        self.rewards = []
        self.finished = False
        self.num_possible_actions = num_possible_actions


    def run(self, model, tf_session, environment, action_chooser):
        '''
        Generator that runs model in OpenAI-gym-like environment until done
        Yield tuples of (observation, reward, done, info, action)
        '''
        if self.num_possible_actions is None:
            self.num_possible_actions = environment.action_space.n
        if len(self.observations) == 0:
            self.observations.append(environment.reset())
        for step_id in itertools.count():
            expected_rewards = choice.expected_rewards(model, tf_session, self.observations[-1], num_possible_actions=self.num_possible_actions)
            action = action_chooser(expected_rewards=expected_rewards, step_id=step_id, episode=self)

            observation, reward, done, info = environment.step(action)
            self.register_step(observation, reward, done, action)
            yield observation, reward, done, info, action
            if done:
                break


    def register_step(self, observation, reward, done, action):
        '''Register step in which action was taken to yield observation and reward'''
        self.observations.append(observation)
        self.actions.append(action)
        self.rewards.append(reward)
        if done:
            self.finished = True


    def train(self, model, tf_session, discount, learning_rate, start_step=0, end_step=None):
        '''Train model on the steps from this episode'''
        if end_step is None:
            end_step = len(self)
        for step in reversed(range(start_step, end_step)): # reverse so that we don't fit to things that will soon be modified
            expected_rewards = choice.expected_rewards(
                model=model,
                tf_session=tf_session,
                observation=self.observations[step + 1],
                num_possible_actions=self.num_possible_actions)
            done = (step + 1 == len(self.actions)) if self.finished else False
            discounted_reward = self.rewards[step] + (0 if done else discount * np.max(expected_rewards))
            feed_dict = {
                model.observations: [self.observations[step]],
                model.actions: [self.actions[step]],
                model.target_expected_rewards: [discounted_reward],
                model.learning_rate: learning_rate}
            tf_session.run(model.optimize, feed_dict=feed_dict)


    def total_reward(self):
        return np.sum(self.rewards)


    def __len__(self):
        '''
        The number of registered steps
        Note that the number of registered observations is one greater than this, due to environments producing initial observations
        '''
        return len(self.rewards)