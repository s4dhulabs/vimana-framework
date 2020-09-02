# -*- coding: utf-8 -*-
    
def switchAgent():
    from random import choice, shuffle
    import os

    user_agents = []
    ua_dir = os.path.dirname(os.path.abspath(__file__))
    agents_def = os.path.join(ua_dir, 'UA.vmn')
    Agents = open(agents_def, 'r')

    for agent in Agents:
        user_agents.append(agent.strip('\t\n\r'))
    shuffle(user_agents)
    
    return (choice(user_agents))

if (__name__ == "__main__"):
	try:switchAgent()
	except(TypeError):pass	

