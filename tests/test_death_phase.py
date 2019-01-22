import unittest
from scipy.integrate import odeint
import numpy as np
from impact import TimeCourse

class TestFindDeathPhase(unittest.TestCase):
    def test_find_death_phase(self):
        def dFBA(y, t0, mu=0.4):
            X, mu = y
            dydt = [mu * X, -0.1]
            return dydt

        x = np.linspace(0, 10, 200)
        y = odeint(dFBA, [0.05, 0.8], x)
        y = np.array(y).transpose()

        dp = TimeCourse.find_death_phase_static(y[0])

        self.assertEqual(dp, 159)

        # import impact.plotting as implot
        # traces = [implot.go.Scatter(x=x,y=y[i],mode='lines+markers') for i in range(2)]
        # traces.append(implot.go.Scatter(x=[x[dp]]*20,y=np.linspace(0,1.5,20)))
        # implot.plot(traces)

if __name__ == '__main__':
    unittest.main()