import React, { useState } from 'react';
import axios from 'axios';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import RefreshIcon from '@mui/icons-material/Refresh';
import LinearProgress from '@mui/material/LinearProgress';

const API_URL = process.env.REACT_APP_API_URL || 'url';
const API_AUTH_TOKEN = process.env.REACT_APP_API_AUTH_TOKEN || 'token';

type STATE = 'startup' | 'loading' | 'loaded' | 'error';

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

class RequestFailureError extends Error {
  constructor(message: string) {
    super(message);
    Object.setPrototypeOf(this, RequestFailureError.prototype);
  }
}

const App = () => {
  const [metricData, setMetricData] = useState<MetricData | null>(null);
  const [state, setState] = useState<STATE>('startup');

  const pathHandler = (path: string) => async () => {
    try {
      const response = await axios.get(`${API_URL}${path}`, {
        headers: {
          Authorization: `${API_AUTH_TOKEN}`,
          'Content-Type': 'application/json',
        },
      });
      return response;
    } catch (error) {
      return {
        status: -1,
        data: {},
      };
    }
  };

  const fetchMetricsHandler = async () => {
    const [
      deploymentFrequencyResponse,
      leadTimeForChangesResponse,
      changeFailureRateResponse,
      timeToRestoreServiceResponse,
    ] = await Promise.all([
      pathHandler('/deployment-frequency')(),
      pathHandler('/lead-time-for-changes')(),
      pathHandler('/change-failure-rate')(),
      pathHandler('/mean-time-to-recovery')(),
    ]);

    const statuses = [
      deploymentFrequencyResponse,
      leadTimeForChangesResponse,
      changeFailureRateResponse,
      timeToRestoreServiceResponse,
    ].map((response) => response.status);

    if (
      statuses.every((value, _, array) => value === array[0]) &&
      statuses[0] === 200
    ) {
      setMetricData({
        deploymentFrequency: deploymentFrequencyResponse.data,
        leadTimeForChanges: leadTimeForChangesResponse.data,
        changeFailureRate: changeFailureRateResponse.data,
        timeToRestoreService: timeToRestoreServiceResponse.data,
      });
    } else if (statuses.includes(-1)) {
      throw new RequestFailureError('network request failed');
    }
  };

  const loadHandler = async () => {
    setState('loading');
    try {
      await fetchMetricsHandler();
    } catch (err) {
      if (err instanceof RequestFailureError) {
        setState('error');
        return;
      }
    }
    setState('loaded');
  };

  const renderContent = () => {
    switch (state) {
      case 'loading':
        return <LinearProgress />;
      case 'loaded':
        return (
          <>
            <p>Deployment Frequency</p>
            <p>
              Number of Deployments:{' '}
              {metricData?.deploymentFrequency?.numberOfDeployments}
            </p>
            <p>
              First Deployment:{' '}
              {new Date(
                metricData?.deploymentFrequency?.firstBuildDatetime || 'null'
              ).toUTCString()}
            </p>
            <p>
              Latest Deployment:{' '}
              {new Date(
                metricData?.deploymentFrequency?.latestBuildDatetime || 'null'
              ).toUTCString()}
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
              {Math.round(
                metricData?.leadTimeForChanges?.meanDurationInSeconds || 0.0
              )}{' '}
              second(s)
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
              {Math.round(
                metricData?.timeToRestoreService?.meanTimeToRecoverySeconds ||
                  0.0
              )}{' '}
              second(s)
            </p>
            <p>
              Average Time to Restore Service:
              <br />
              {metricData?.timeToRestoreService?.meanTimeToRecoveryDuration}
            </p>
          </>
        );
      default:
        return null;
    }
  };

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
