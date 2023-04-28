import * as cdk from '@aws-cdk/core';
import * as path from 'path';
import * as dotenv from 'dotenv';
import { Function, Code, Runtime } from '@aws-cdk/aws-lambda';
import { LambdaRestApi } from '@aws-cdk/aws-apigateway'

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
  }
};
