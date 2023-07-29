import { Stack, StackProps, Duration, CfnOutput } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as path from 'path';
import * as dotenv from 'dotenv';
import { Function, Code, Runtime } from 'aws-cdk-lib/aws-lambda';
import { AuthorizationType, CfnMethod, LambdaRestApi, TokenAuthorizer } from 'aws-cdk-lib/aws-apigateway';
import { BlockPublicAccess, Bucket, BucketEncryption } from 'aws-cdk-lib/aws-s3';
import {
  CachePolicy,
  Distribution,
  OriginAccessIdentity
} from 'aws-cdk-lib/aws-cloudfront';
import { S3Origin } from 'aws-cdk-lib/aws-cloudfront-origins';
import { Vpc } from 'aws-cdk-lib/aws-ec2';


dotenv.config();

const cdkStack = process.env.CDK_STACK || 'BackendStack';
const cdkId = process.env.CDK_ID || 'BackendStack';

const authToken = process.env.AUTH_TOKEN || 'test-token';

const jenkinsApiUrl = process.env.JENKINS_API_URL || 'url';
const bitbucketApiUrl = process.env.BITBUCKET_API_URL || 'url';
const bitbucketApiUserName = process.env.BITBUCKET_API_USER_NAME || 'url';
const bitbucketApiAppPassword = process.env.BITBUCKET_API_APP_PASSWORD || 'url';

const awsVpcId = process.env.AWS_VPC_ID || 'vpc-id';
const awsSubnetName = process.env.AWS_SUBNET_NAME || 'subnet-name';
const awsSubnetIds = (process.env.AWS_SUBNET_IDS || 'subnet-id1,subnet-id2').split(',');
const awsAvailabilityZones = (process.env.AWS_AVAILABILITY_ZONES || 'zone-1,zone2').split(',');

const jenkinsStJobNames = process.env.JENKINS_ST_JOB_NAMES ?? '';
const jenkinsAtJobNames = process.env.JENKINS_AT_JOB_NAMES ?? '';
const jenkinsPrJobNames = process.env.JENKINS_PR_JOB_NAMES ?? '';
const jenkinsJobNames = process.env.JENKINS_JOB_NAMES ?? '';
const bitbucketWorkspace = process.env.BITBUCKET_WORKSPACE || 'value';
const bitbucketRepoSlugs = process.env.BITBUCKET_REPO_SLUGS ?? '';


export class BackendStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const awsVpc = Vpc.fromVpcAttributes(this, `${cdkId}AwsSubnet`, {
      availabilityZones: awsAvailabilityZones,
      vpcId: awsVpcId,
      privateSubnetIds: awsSubnetIds,
      privateSubnetNames: [awsSubnetName]
    });

    const handlerLambda = new Function(this, `${cdkId}HandlerLambda`, {
      runtime: Runtime.PYTHON_3_9,
      handler: 'src.app.handler',
      code: Code.fromAsset(path.join(__dirname, '../build', 'handler_lambda')),
      functionName: `${cdkStack}-handler-lambda`,
      environment: {
        JENKINS_API_URL: jenkinsApiUrl,
        BITBUCKET_API_URL: bitbucketApiUrl,
        BITBUCKET_API_USER_NAME: bitbucketApiUserName,
        BITBUCKET_API_APP_PASSWORD: bitbucketApiAppPassword,
        JENKINS_ST_JOB_NAMES: jenkinsStJobNames,
        JENKINS_AT_JOB_NAMES: jenkinsAtJobNames,
        JENKINS_PR_JOB_NAMES: jenkinsPrJobNames,
        JENKINS_JOB_NAMES: jenkinsJobNames,
        BITBUCKET_WORKSPACE: bitbucketWorkspace,
        BITBUCKET_REPO_SLUGS: bitbucketRepoSlugs
      },
      vpc: awsVpc,
      vpcSubnets: { subnetGroupName: awsSubnetName },
      timeout: Duration.minutes(1)
    });

    const authLambda = new Function(this, `${cdkId}AuthLambda`, {
      functionName: `${cdkStack}-auth-lambda`,
      runtime: Runtime.PYTHON_3_9,
      code: Code.fromAsset(path.join(__dirname, '../build', 'auth_lambda')),
      handler: 'src.app.handler',
      environment: {
        AUTH_TOKEN: authToken
      }
    });

    const authoriser = new TokenAuthorizer(this, `${cdkId}ApiGatewayAuth`,{
      handler: authLambda,
      identitySource:'method.request.header.Authorization',
      resultsCacheTtl: Duration.seconds(0),
    });

    const api = new LambdaRestApi(this, `${cdkId}Api`, {
      handler: handlerLambda,
      restApiName: `${cdkStack}-api`,
      defaultMethodOptions: {
        authorizer: authoriser,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: ['*'],
        allowHeaders: ['Authorization', 'RandomHeader']
      },
      deployOptions: {
        tracingEnabled: false,
      }
    });

    api.methods
      .filter((method) => method.httpMethod === "OPTIONS")
      .forEach((method) => {
        const methodCfn = method.node.defaultChild as CfnMethod;
        methodCfn.authorizationType = AuthorizationType.NONE;
        methodCfn.authorizerId = undefined;
      });
    
      const uiBucket = new Bucket(this, `${cdkId}UiBucket`, {
        bucketName: `${cdkStack}-ui-bucket`,
        encryption: BucketEncryption.S3_MANAGED,
        blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
        publicReadAccess: false,
      });

      new CfnOutput(this, `${cdkId}UiBucketName`, {
        value: uiBucket.bucketName
      });
  
      const uiBucketOriginAccess = new OriginAccessIdentity(this, `${cdkId}UiBucketOrigin`);
      uiBucket.grantRead(uiBucketOriginAccess);

      const uiBucketOrigin = new S3Origin(
        uiBucket,
        {
          originPath: "/",
          originAccessIdentity: uiBucketOriginAccess,
        }
      );
  
      const uiCloudfront = new Distribution(this, `${cdkId}UiCloudfront`, {
        defaultBehavior: {
          origin: uiBucketOrigin,
          cachePolicy: CachePolicy.CACHING_DISABLED,
        },
      });
  
      new CfnOutput(this, `${cdkId}UiCloudfrontDns`, {
        value: uiCloudfront.distributionDomainName
      });
  }
}
