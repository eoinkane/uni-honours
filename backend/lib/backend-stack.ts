import * as cdk from '@aws-cdk/core';
import * as path from 'path';
import * as dotenv from 'dotenv';
import { Function, Code, Runtime } from '@aws-cdk/aws-lambda';
import { LambdaRestApi } from '@aws-cdk/aws-apigateway';
import { BlockPublicAccess, Bucket, BucketEncryption } from '@aws-cdk/aws-s3';
import {
  Distribution,
  OriginAccessIdentity
} from '@aws-cdk/aws-cloudfront';
import { S3Origin } from '@aws-cdk/aws-cloudfront-origins';

dotenv.config();

const cdkStack = process.env.CDK_STACK || 'BackendStack';
const cdkId = process.env.CDK_ID || 'BackendStack';

export class BackendStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const handlerLambda = new Function(this, `${cdkId}HandlerLambda`, {
      runtime: Runtime.PYTHON_3_9,
      handler: 'src.app.handler',
      code: Code.fromAsset(path.join(__dirname, '../build', 'handler-lambda')),
      functionName: `${cdkStack}-handler-lambda`
    });

    new LambdaRestApi(this, `${cdkId}Api`, {
      handler: handlerLambda,
      restApiName: `${cdkStack}-api`
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
        origin: uiBucketOrigin
      },
    });

    new cdk.CfnOutput(this, `${cdkId}UiCloudfrontDns`, {
      value: uiCloudfront.distributionDomainName
    });
  };
};
