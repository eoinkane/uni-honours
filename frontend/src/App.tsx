import React, { useState } from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import RefreshIcon from '@mui/icons-material/Refresh';

interface DeploymentFrequencyData {
  numberOfDeployments: number;
  latestBuildDatetime: string;
  firstBuildDatetime: string;
  timeBetweenLatestAndFirstBuild: string;
}

interface LeadTimeForChangesData {
  meanDurationInSeconds: number;
  meanDurationInDuration: string;
}

interface ChangeFailureRateData {
  percentageOfChangeFailures: number;
}

interface TimeToRestoreServiceData {
    meanTimeToRecoverySeconds: number;
    meanTimeToRecoveryDuration: string;
}

interface MetricData {
  deploymentFrequency: DeploymentFrequencyData;
  leadTimeForChanges: LeadTimeForChangesData;
  changeFailureRate: ChangeFailureRateData;
  timeToRestoreService: TimeToRestoreServiceData;
}

const App = () => {
  const [metricData, setMetricData] = useState<MetricData | null>(null);

  const loadHandler = async () => {
    setMetricData({
      deploymentFrequency: {
        numberOfDeployments: 7,
        latestBuildDatetime: '2023-03-10T10:10:30.000000+00:00',
        firstBuildDatetime: '2023-03-17T10:10:30.000000+00:00',
        timeBetweenLatestAndFirstBuild: '7 days, 0 hr(s), 0 min(s), 0 sec(s)',
      },
      leadTimeForChanges: {
        meanDurationInSeconds: 1800.0,
        meanDurationInDuration: '0 hr(s), 30 min(s), 0 sec(s)',
      },
      changeFailureRate: {
        percentageOfChangeFailures: 30,
      },
      timeToRestoreService: {
        meanTimeToRecoverySeconds: 3600.0,
        meanTimeToRecoveryDuration: '0 days, 1 hr(s), 0 min(s), 0 sec(s)',
      }
    });
  };

  const renderContent = () => (
    <>
      <p>Deployment Frequency</p>
      <p>Number of Deployments: {metricData?.deploymentFrequency?.numberOfDeployments}</p>
      <p>
        First Deployment:{' '}
        {new Date(metricData?.deploymentFrequency?.firstBuildDatetime || 'null').toUTCString()}
      </p>
      <p>
        Latest Deployment:{' '}
        {new Date(metricData?.deploymentFrequency?.latestBuildDatetime || 'null').toUTCString()}
      </p>
      <p>
        Time Between Latest and First Deployment:
        <br />
        {metricData?.deploymentFrequency?.timeBetweenLatestAndFirstBuild}
      </p>
      <p>Lead Time For Changes</p>
      <p>
        Average Duration of Deployments in Seconds:
        <br />
        {Math.round(metricData?.leadTimeForChanges?.meanDurationInSeconds || 0.0)} second(s)
      </p>
      <p>
        Average Time of Deployment:
        <br />
        {metricData?.leadTimeForChanges?.meanDurationInDuration}
      </p>
      <p>Change Failure Rate</p>
      <p>
        Percentage of Changes That Resulted in Failures:{' '}
        {metricData?.changeFailureRate?.percentageOfChangeFailures}%
      </p>
      <p>Time to Restore Service</p>
      <p>
        Average Time to Restore Service in Seconds:
        <br />
        {Math.round(metricData?.timeToRestoreService?.meanTimeToRecoverySeconds || 0.0)} second(s)
      </p>
      <p>
        Average Time to Restore Service:
        <br />
        {metricData?.timeToRestoreService?.meanTimeToRecoveryDuration}
      </p>
    </>
  );

  return (
    <>
      <AppBar position="static" component="header" sx={{ mb: 5 }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            DORA Metrics Dashboard
          </Typography>
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="menu"
            sx={{ mr: 2 }}
            onClick={loadHandler}
          >
            <RefreshIcon />
          </IconButton>
        </Toolbar>
      </AppBar>
      {renderContent()}
    </>
  );
};

export default App;
