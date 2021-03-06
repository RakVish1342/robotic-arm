import time

import numpy as np



def split_observations(observations):
    curr_observations = [observations_[:-1] for observations_ in observations]
    next_observations = [observations_[1:] for observations_ in observations]
    return curr_observations, next_observations


def discount_return(rewards, gamma):
    return np.dot(rewards, gamma ** np.arange(len(rewards)))


def discount_returns(rewards, gamma):
    return [discount_return(rewards_, gamma) for rewards_ in rewards]


def do_rollouts(env, pol, num_trajs, num_steps, target_distance=0,
                output_dir=None, image_visualizer=None, record_file=None,
                verbose=False, gamma=0.9, seeds=None, reset_states=None,
                cv2_record_file=None, image_transformer=None, ret_rewards_only=False, close_env=False):
    """
    image_transformer is for the returned observations and for cv2's video writer
    """
    random_state = np.random.get_state()
    if reset_states is None:
        reset_states = [None] * num_trajs
    else:
        num_trajs = min(num_trajs, len(reset_states))

    start_time = time.time()
    if verbose:
        errors_header_format = '{:>30}{:>15}'
        errors_row_format = '{:>30}{:>15.4f}'
        print(errors_header_format.format('(traj_iter, step_iter)', 'reward'))
    if ret_rewards_only:
        rewards = []
    else:
        states, observations, actions, rewards = [], [], [], []
    frame_iter = 0
    done = False
    for traj_iter, state in enumerate(reset_states):
        if verbose:
            print('=' * 45)
        if seeds is not None and len(seeds) > traj_iter:
            np.random.seed(seed=seeds[traj_iter])
        if ret_rewards_only:
            rewards_ = []
        else:
            states_, observations_, actions_, rewards_ = [], [], [], []

        obs = env.reset(state)
        frame_iter += 1
        if state is None:
            state = env.get_state()
        if target_distance:
            raise NotImplementedError
        for step_iter in range(num_steps):
            try:
                if not ret_rewards_only:
                    # observations_.append(preprocess_image(obs))
                    observations_.append(obs)
                    states_.append(state)
                # if container:
                #     container.add_datum(traj_iter, step_iter, state=state, **obs)
                # if cv2_record_file:
                #     vis_image = obs['image'].copy()
                #     vis_image = cv2.cvtColor(vis_image, cv2.COLOR_RGB2BGR)
                #     vis_image = image_transformer.preprocess(vis_image)
                #     video_writer.write(vis_image)

                action = pol.act(obs)
                prev_obs = obs
                s, obs, reward, episode_done = env.step(action)  # action is updated in-place if needed
                frame_iter += 1

                if verbose:
                    print(errors_row_format.format(str((traj_iter, step_iter)), reward))
                prev_state, state = state, env.get_state()
                if not ret_rewards_only:
                    actions_.append(action)
                rewards_.append(reward)
                if step_iter == (num_steps - 1) or episode_done:
                    if not ret_rewards_only:
                        # observations_.append(preprocess_image(obs))
                        observations_.append(obs)
                        states_.append(state)

                if done or episode_done:
                    break
            except KeyboardInterrupt:
                break
        if verbose:
            print('-' * 45)
            print(errors_row_format.format('discounted return', discount_return(rewards_, gamma)))
            print(errors_row_format.format('return', discount_return(rewards_, 1.0)))
        if not ret_rewards_only:
            states.append(states_)
            observations.append(observations_)
            actions.append(actions_)
        rewards.append(rewards_)
        if done:
            break
    # if cv2_record_file:
    #     video_writer.release()
    if verbose:
        print('=' * 45)
        print(errors_row_format.format('mean discounted return', np.mean(discount_returns(rewards, gamma))))
        print(errors_row_format.format('mean return', np.mean(discount_returns(rewards, 1.0))))
    else:
        discounted_returns = discount_returns(rewards, gamma)
        print('mean discounted return: %.4f (%.4f)' % (np.mean(discounted_returns),
                                                       np.std(discounted_returns) / np.sqrt(len(discounted_returns))))
        returns = discount_returns(rewards, 1.0)
        print('mean return: %.4f (%.4f)' % (np.mean(returns),
                                            np.std(returns) / np.sqrt(len(returns))))
    if close_env:
        env.close()
    # if record_file:
    #     writer.finish()
    # if container:
    #     container.close()
    end_time = time.time()
    if verbose:
        print("average FPS: {}".format(frame_iter / (end_time - start_time)))
    np.random.set_state(random_state)
    if ret_rewards_only:
        return rewards
    else:
        return states, observations, actions, rewards
