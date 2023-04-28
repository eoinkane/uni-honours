import * as cdk from '@aws-cdk/core';
import * as path from 'path';
import { Function, Code, Runtime } from '@aws-cdk/aws-lambda'

export class BackendStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    new Function(this, 'HelloWorldLambda', {
      runtime: Runtime.PYTHON_3_9,
      handler: 'src.app.handler',
      code: Code.fromAsset(path.join(__dirname, '../build', 'hello-world-lambda')),
      functionName: 'hello-world-lambda'
    });
  }
};
