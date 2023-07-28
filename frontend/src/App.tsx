import React, { useState, useEffect } from 'react';

const App = () => {
  const [deploymentFrequency, setDeploymentFrequency] = useState<any>();

  useEffect(() => {
    setDeploymentFrequency({
        numberOfDeployments: 7,
        latestBuildDatetime: '2023-03-10T10:10:30.000000+00:00',
        firstBuildDatetime: '2023-03-17T10:10:30.000000+00:00',
        timeBetweenLatestAndFirstBuild:
          '7 days, 0 hr(s), 0 min(s), 0 sec(s)',
    })
  }, []);


  return (
    <>
      <h2>DORA Metrics Dashboard</h2>
      <p>Deployment Frequency</p>
      <p>
        Number of Deployments:{' '}
        {deploymentFrequency?.numberOfDeployments}
      </p>
      <p>
        First Deployment:{' '}
        {new Date(
          deploymentFrequency?.firstBuildDatetime
        ).toUTCString()}
      </p>
      <p>
        Latest Deployment:{' '}
        {new Date(
          deploymentFrequency?.latestBuildDatetime
        ).toUTCString()}
      </p>
      <p>
        Time Between Latest and First Deployment:
        <br />
        {deploymentFrequency?.timeBetweenLatestAndFirstBuild}
      </p>
    </>
  );
};

export default App;
