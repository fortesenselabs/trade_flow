from rl_fts.strategies.sinewaveSH.strategy1 import create_env
from tensortrade.env.generic import TradingEnv

# TESTS
"""
    Test case - 0`
    description: test case which was causing an exception
    reason: the precision of the instrument was too low, 
    issue: this caused the enter order to be cancelled, but the short hold action scheme thought that the action was
    successful, which allowed the simulator to attempt to exit a position that was never entered
    resolution: pushed up my instrument precision to from 2 decimal points to 8
    NOTE: pay attention to the terminal output on a crash.
"""

def test_0():
    return [
    {'price': 149.99993819142986, 'action': -1},
    {'price': 149.97274489145346, 'action': 0},
    {'price': 149.89613575141215, 'action': 0},
    {'price': 149.77018652670063, 'action': 1},
    {'price': 149.59502176294384, 'action': 0},
    {'price': 149.37081467283946, 'action': 1},
    {'price': 149.09778696487533, 'action': 0},
    {'price': 148.77620862409194, 'action': 0},
    {'price': 148.40639764510593, 'action': 0},
    {'price': 147.98871971765945, 'action': 0},
    {'price': 147.5235878650056, 'action': 0},
    {'price': 147.01146203548797, 'action': 1},
    {'price': 146.45284864771816, 'action': 1},
    {'price': 145.84830008980066, 'action': 1},
    {'price': 145.19841417310082, 'action': 0},
    {'price': 144.5038335410953, 'action': 0},
    {'price': 143.76524503389066, 'action': 1},
    {'price': 142.98337900903726, 'action': 0},
    {'price': 142.15900861931112, 'action': 0},
    {'price': 141.29294904817715, 'action': 1},
    {'price': 140.38605670369037, 'action': 1},
    {'price': 139.43922837163157, 'action': 1},
    {'price': 138.45340032871584, 'action': 1},
    {'price': 137.42954741674953, 'action': 1},
    {'price': 136.36868207865245, 'action': 1},
    {'price': 135.27185335729766, 'action': 0},
    {'price': 134.14014585815946, 'action': 0},
    {'price': 132.9746786767948, 'action': 0},
    {'price': 131.77660429221922, 'action': 1},
    {'price': 130.54710742727116, 'action': 0},
    {'price': 129.28740387709198, 'action': 0},
    {'price': 127.99873930687977, 'action': 1},
    {'price': 126.68238802010613, 'action': 1},
    {'price': 125.33965169841365, 'action': 0},
    {'price': 123.9718581144405, 'action': 0},
    {'price': 122.58035981884477, 'action': 0},
    {'price': 121.16653280282672, 'action': 1},
    {'price': 119.73177513747206, 'action': 1},
    {'price': 118.27750559126098, 'action': 1},
    {'price': 116.80516222711081, 'action': 1},
    {'price': 115.31620098033919, 'action': 1},
    {'price': 113.81209421895372, 'action': 1},
    {'price': 112.29432928769253, 'action': 0},
    {'price': 110.76440703725454, 'action': 0},
    {'price': 109.22384034017463, 'action': 1},
    {'price': 107.67415259481083, 'action': 1},
    {'price': 106.11687621892287, 'action': 1},
    {'price': 104.55355113433205, 'action': 0},
    {'price': 102.98572324416051, 'action': 1},
    {'price': 101.41494290415591, 'action': 0},
    {'price': 99.8427633896132, 'action': 0},
    {'price': 98.27073935940916, 'action': 1},
    {'price': 96.70042531866899, 'action': 0},
    {'price': 95.13337408158489, 'action': 0},
    {'price': 93.57113523590658, 'action': 0},
    {'price': 92.01525361062255, 'action': 1},
    {'price': 90.4672677483468, 'action': 0},
    {'price': 88.92870838392206, 'action': 1},
    {'price': 87.40109693074376, 'action': 0},
    {'price': 85.88594397630142, 'action': 0},
    {'price': 84.38474778842554, 'action': 1},
    {'price': 82.89899283371659, 'action': 1},
    {'price': 81.4301483096216, 'action': 1},
    {'price': 79.97966669160982, 'action': 1},
    {'price': 78.54898229688368, 'action': 1},
    {'price': 77.13950986604607, 'action': 0},
    {'price': 75.75264316412563, 'action': 1},
    {'price': 74.38975360234429, 'action': 0},
    {'price': 73.0521888819892, 'action': 0},
    {'price': 71.7412716617304, 'action': 1},
    {'price': 70.45829824970211, 'action': 0},
    {'price': 69.20453732164104, 'action': 0},
    {'price': 67.9812286663487, 'action': 0},
    {'price': 66.78958195971931, 'action': 0},
    {'price': 65.63077556854451, 'action': 1},
    {'price': 64.50595538527858, 'action': 1},
    {'price': 63.4162336949161, 'action': 1},
    {'price': 62.36268807510227, 'action': 1},
    {'price': 61.346360330564124, 'action': 1},
    {'price': 60.36825546291576, 'action': 0},
    {'price': 59.42934067685673, 'action': 0},
    {'price': 58.53054442374588, 'action': 0},
    {'price': 57.67275548349698, 'action': 1},
    {'price': 56.85682208570347, 'action': 1},
    {'price': 56.08355107086158, 'action': 1},
    {'price': 55.35370709252158, 'action': 1},
    {'price': 54.668011861155534, 'action': 1},
    {'price': 54.027143430489744, 'action': 0},
    {'price': 53.4317355270073, 'action': 1},
    {'price': 52.88237692328407, 'action': 0},
    {'price': 52.37961085577744, 'action': 0},
    {'price': 51.923934487643734, 'action': 1},
    {'price': 51.51579841711562, 'action': 0},
    {'price': 51.15560623192538, 'action': 1},
    {'price': 50.84371411021479, 'action': 1},
    {'price': 50.58043046832636, 'action': 1},
    {'price': 50.366015655823986, 'action': 0},
    {'price': 50.20068169804478, 'action': 0},
    {'price': 50.084592086436594, 'action': 1},
    {'price': 50.0178616168885, 'action': 0},
    {'price': 50.0005562762143, 'action': 0},
    {'price': 50.032693176900956, 'action': 1},
    {'price': 50.11424054018693, 'action': 1},
    {'price': 50.245117727486694, 'action': 0},
    {'price': 50.425195320130754, 'action': 0},
    {'price': 50.654295247342, 'action': 0},
    {'price': 50.93219096232202, 'action': 0},
    {'price': 51.25860766627328, 'action': 1},
    {'price': 51.63322258013549, 'action': 1},
    {'price': 52.05566526376751, 'action': 0},
    {'price': 52.525517982259316, 'action': 0},
    {'price': 53.0423161190116, 'action': 1},
    {'price': 53.60554863517453, 'action': 1},
    {'price': 54.214658574991525, 'action': 0},
    {'price': 54.86904361654828, 'action': 1},
    {'price': 55.5680566673822, 'action': 0},
    {'price': 56.31100650436355, 'action': 1},
    {'price': 57.097158457215606, 'action': 0},
    {'price': 57.92573513499748, 'action': 0},
    {'price': 58.79591719483177, 'action': 0},
    {'price': 59.706844152116524, 'action': 1},
    {'price': 60.657615231420486, 'action': 0},
    {'price': 61.64729025722006, 'action': 1},
    {'price': 62.67489058359737, 'action': 0},
    {'price': 63.67489058359737, 'action': 0}
]

"""
    Test case - 1
    description: test case which was causing an exception
    reason:  
    issue: 
    NOTE: pay attention to the terminal output on a crash.
"""

def test_1(): 
    return [
        {'price': 149.89114003390026, 'action': -1},
        {'price': 147.30212967930973, 'action': 0},
        {'price': 141.43546854184092, 'action': 1},
        {'price': 132.69766826484837, 'action': 1},
        {'price': 121.69418695587792, 'action': 1},
        {'price': 109.18747589082851, 'action': 0},
        {'price': 96.04414787532875, 'action': 0},
        {'price': 83.17492806386298, 'action': 0},
        {'price': 71.47154815384225, 'action': 0},
        {'price': 61.74495667093458, 'action': 1},
        {'price': 54.66912686760935, 'action': 1},
        {'price': 50.73435588802513, 'action': 1},
        {'price': 50.21329118524827, 'action': 1},
        {'price': 53.14203828227674, 'action': 0},
        {'price': 59.31765895454203, 'action': 1},
        {'price': 68.31223318938419, 'action': 1},
        {'price': 79.50251054369734, 'action': 0},
        {'price': 92.11309630312817, 'action': 0},
        {'price': 105.27017999514237, 'action': 0},
        {'price': 118.06208330935766, 'action': 0},
        {'price': 129.60243194938195, 'action': 1}
    ]

"""
    Test case - 2
    Price movement: 150, 151, 152,
    actions: enter short, exit short,
    starting Networth: 200
    ending Networth: ?
    descriptions: Testing that entering and exiting work as expected when price is going up
    expectation: money should be lost to trading fees and price difference
"""

"""
    Test case - 3
    Price movement: 150, 149, 148, 147, 146, 145
    actions: enter short, hold, hold, hold, hold, exit short
    starting Networth: 200
    ending Networth: ?
    descriptions: Testing that entering, holding and exiting work as expected
    expectation: money should be made due to price moving down
"""

"""
    Test case - 4
    Price movement:  150, 151, 152, 153, 154, 155
    actions: enter short, hold, hold, hold, hold, exit short
    starting Networth: 10
    ending Networth: ?
    descriptions:
    expectation: money should be completely lost due to price going up
"""

def main():
    config = {
        "type": "train",
        "period": 10,
        "window_size": 30,
        "min_periods": 30,
        "max_allowed_loss": 1,
        "trading_days": 120
    }

    env: TradingEnv = create_env(config)

    trading_simulations = []
    trading_simulations.append(test_1())
    for simulation in trading_simulations:
        for row in simulation:
            action = row['action']
            env.step(action=action)
    print("done")

main()