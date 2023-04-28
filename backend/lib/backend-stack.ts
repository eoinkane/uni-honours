import * as cdk from '@aws-cdk/core';
import * as path from 'path';
import * as dotenv from 'dotenv';
import { Function, Code, Runtime } from '@aws-cdk/aws-lambda';
import { AuthorizationType, CfnMethod, LambdaRestApi, TokenAuthorizer } from '@aws-cdk/aws-apigateway';
import { BlockPublicAccess, Bucket, BucketEncryption } from '@aws-cdk/aws-s3';
import {
  CachePolicy,
  Distribution,
  OriginAccessIdentity
} from '@aws-cdk/aws-cloudfront';
import { S3Origin } from '@aws-cdk/aws-cloudfront-origins';
import { Vpc } from '@aws-cdk/aws-ec2';

dotenv.config();

const cdkStack = process.env.CDK_STACK || 'BackendStack';
const cdkId = process.env.CDK_ID || 'BackendStack';
const authToken = process.env.AUTH_TOKEN || 'test-token';
const jenkinsApiUrl = process.env.JENKINS_API_URL || 'url';
const awsVpcId = process.env.AWS_VPC_ID || 'vpc-id';
const awsSubnetName = process.env.AWS_SUBNET_NAME || 'subnet-name';
const awsSubnetIds = (process.env.AWS_SUBNET_IDS || 'subnet-id1,subnet-id2').split(',');
const awsAvailabilityZones = (process.env.AWS_AVAILABILITY_ZONES || 'zone-1,zone2').split(',');

export class BackendStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const awsVpc = Vpc.fromVpcAttributes(this, `${cdkId}AwsSubnet`, {
      availabilityZones: awsAvailabilityZones,
      vpcId: awsVpcId,
      privateSubnetIds: awsSubnetIds,
      privateSubnetNames: [awsSubnetName]
    })

    const handlerLambda = new Function(this, `${cdkId}HandlerLambda`, {
      runtime: Runtime.PYTHON_3_9,
      handler: 'src.app.handler',
      code: Code.fromAsset(path.join(__dirname, '../build', 'handler-lambda')),
      functionName: `${cdkStack}-handler-lambda`,
      environment: {
        JENKINS_API_URL: jenkinsApiUrl
      },
      vpc: awsVpc,
      vpcSubnets: { subnetName: awsSubnetName }
    });

    const authLambda = new Function(this, `${cdkId}AuthLambda`, {
      functionName: `${cdkStack}-auth-lambda`,
      runtime: Runtime.PYTHON_3_9,
      code: Code.fromAsset(path.join(__dirname, '../build', 'auth-lambda')),
      handler: 'src.app.handler',
      environment: {
        AUTH_TOKEN: authToken
      }
    });

    const authoriser = new TokenAuthorizer(this, `${cdkId}ApiGatewayAuth`,{
      handler: authLambda,
      identitySource:'method.request.header.Authorization',
      resultsCacheTtl: cdk.Duration.seconds(0),
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

    new cdk.CfnOutput(this, `${cdkId}UiCloudfrontDns`, {
      value: uiCloudfront.distributionDomainName
    });
  };
};
