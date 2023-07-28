import React, { useState, useEffect } from 'react';

const App = () => {
  const [deploymentFrequency, setDeploymentFrequency] = useState<any>();
  const [leadTimeForChanges, setLeadTimeForChanges] = useState<any>();
  const [changeFailureRate, setChangeFailureRate] = useState<any>();
  const [timeToRestoreService, setTimeToRestoreService] = useState<any>();

  useEffect(() => {
    setDeploymentFrequency({
      numberOfDeployments: 7,
      latestBuildDatetime: '2023-03-10T10:10:30.000000+00:00',
      firstBuildDatetime: '2023-03-17T10:10:30.000000+00:00',
      timeBetweenLatestAndFirstBuild: '7 days, 0 hr(s), 0 min(s), 0 sec(s)',
    });
    setLeadTimeForChanges({
      meanDurationInSeconds: 1800.0,
      meanDurationInDuration: '0 hr(s), 30 min(s), 0 sec(s)',
    });
    setChangeFailureRate({
      percentageOfChangeFailures: 30,
    });
    setTimeToRestoreService({
      meanTimeToRecoverySeconds: 3600.0,
      meanTimeToRecoveryDuration: '0 days, 1 hr(s), 0 min(s), 0 sec(s)',
    });
  }, []);

  return (
    <>
      <h2>DORA Metrics Dashboard</h2>
      <p>Deployment Frequency</p>
      <p>Number of Deployments: {deploymentFrequency?.numberOfDeployments}</p>
      <p>
        First Deployment:{' '}
        {new Date(deploymentFrequency?.firstBuildDatetime).toUTCString()}
      </p>
      <p>
        Latest Deployment:{' '}
        {new Date(deploymentFrequency?.latestBuildDatetime).toUTCString()}
      </p>
      <p>
        Time Between Latest and First Deployment:
        <br />
        {deploymentFrequency?.timeBetweenLatestAndFirstBuild}
      </p>
      <p>Lead Time For Changes</p>
      <p>
        Average Duration of Deployments in Seconds:
        <br />
        {Math.round(leadTimeForChanges?.meanDurationInSeconds)} second(s)
      </p>
      <p>
        Average Time of Deployment:
        <br />
        {leadTimeForChanges?.meanDurationInDuration}
      </p>
      <p>Change Failure Rate</p>
      <p>
        Percentage of Changes That Resulted in Failures:{' '}
        {changeFailureRate?.percentageOfChangeFailures}%
      </p>
      <p>Time to Restore Service</p>
      <p>
        Average Time to Restore Service in Seconds:
        <br />
        {Math.round(timeToRestoreService?.meanTimeToRecoverySeconds)} second(s)
      </p>
      <p>
        Average Time to Restore Service:
        <br />
        {timeToRestoreService?.meanTimeToRecoveryDuration}
      </p>
    </>
  );
};

export default App;
