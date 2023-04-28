import * as cdk from 'aws-cdk-lib';
import * as path from 'path';
import * as dotenv from 'dotenv';
import { Construct } from 'constructs';
import { Function, Code, Runtime } from 'aws-cdk-lib/aws-lambda';
import { AuthorizationType, CfnMethod, LambdaRestApi, TokenAuthorizer } from 'aws-cdk-lib/aws-apigateway';
import { Vpc } from 'aws-cdk-lib/aws-ec2';


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
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
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
      code: Code.fromAsset(path.join(__dirname, '../build', 'handler-lambda')),
      functionName: `${cdkStack}-handler-lambda`,
      environment: {
        JENKINS_API_URL: jenkinsApiUrl
      },
      vpc: awsVpc,
      vpcSubnets: { subnetGroupName: awsSubnetName },
      timeout: cdk.Duration.minutes(1)
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
  }
}
