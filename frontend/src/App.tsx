import React, { useState } from 'react';
import axios from 'axios';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import ClearAllIcon from '@mui/icons-material/ClearAll';
import RefreshIcon from '@mui/icons-material/Refresh';
import LinearProgress from '@mui/material/LinearProgress';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Grid from '@mui/material/Grid';
import Container from '@mui/material/Container';

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

  const clearHandler = () => {
    setState('startup');
    setMetricData(null);
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
      case 'startup':
        return (
          <Typography variant="h6">
            Please click the refresh icon to fetch the metrics
          </Typography>
        );
      case 'loading':
        return <LinearProgress />;
        case 'loaded':
          if (metricData !== null) {
            return (
              <Box sx={{ mx: 10 }}>
                <Grid container spacing={2} sx={{ mb: 1 }}>
                  <Grid item md={6} >
                    <Paper elevation={12} sx={{ p: 5 }}>
                      <Typography variant="h5" gutterBottom>
                        Deployment Frequency
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        Number of Deployments:{' '}
                        {metricData.deploymentFrequency.numberOfDeployments}
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        First Deployment:{' '}
                        {new Date(
                          metricData.deploymentFrequency.firstBuildDatetime
                        ).toUTCString()}
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        Latest Deployment:{' '}
                        {new Date(
                          metricData.deploymentFrequency.latestBuildDatetime
                        ).toUTCString()}
                      </Typography>
                      <Typography variant="body1" sx={{}} gutterBottom>
                        Time Between Latest and First Deployment:
                        <br />
                        {
                          metricData.deploymentFrequency
                            .timeBetweenLatestAndFirstBuild
                        }
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item md={6}>
                    <Paper elevation={12} sx={{ p: 5, height: '70%' }}>
                      <Typography variant="h5" gutterBottom>
                        Lead Time For Changes
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        Average Duration of Deployments in Seconds:
                        <br />
                        {Math.round(
                          metricData.leadTimeForChanges.meanDurationInSeconds
                        )} second(s)
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        Average Time of Deployment:
                        <br />
                        {metricData.leadTimeForChanges.meanDurationInDuration}
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>
                <Grid container spacing={2} sx={{ mt: 1 }}>
                  <Grid item md={6} >
                    <Paper elevation={12} sx={{ p: 5, height: '70%' }}>
                      <Typography variant="h5" gutterBottom>
                        Change Failure Rate
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        Percentage of Changes That Resulted in Failures:
                        {' '}
                        {metricData.changeFailureRate.percentageOfChangeFailures}%
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item md={6}>
                    <Paper elevation={12} sx={{ p: 5, height: '70%' }}>
                      <Typography variant="h5" gutterBottom>
                        Time to Restore Service
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        Average Time to Restore Service in Seconds:
                        <br />
                        {Math.round(
                          metricData.timeToRestoreService.meanTimeToRecoverySeconds
                        )} second(s)
                      </Typography>
                      <Typography variant="body1" gutterBottom>
                        Average Time to Restore Service:
                        <br />
                        {metricData.timeToRestoreService.meanTimeToRecoveryDuration}
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>
              </Box>
            );
          } else {
            return <Typography variant="h6">A problem occured.</Typography>;
          }
      case 'error':
        return (
          <Typography variant="h6">
            An error occured while fetching the metrics
          </Typography>
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
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="menu"
            sx={{ mr: 2 }}
            onClick={clearHandler}
          >
            <ClearAllIcon />
          </IconButton>
        </Toolbar>
      </AppBar>
      <Container>{renderContent()}</Container>
    </>
  );
};

export default App;
