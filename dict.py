escalation_methods = {
    'CreateNewPolicyVersion': {
        'iam:CreatePolicyVersion': True
    },
    'SetExistingDefaultPolicyVersion': {
        'iam:SetDefaultPolicyVersion': True
    },
    'CreateEC2WithExistingIP': {
        'iam:PassRole': True,
        'ec2:RunInstances': True
    },
    'CreateAccessKey': {
        'iam:CreateAccessKey': True
    },
    'CreateLoginProfile': {
        'iam:CreateLoginProfile': True
    },
    'UpdateLoginProfile': {
        'iam:UpdateLoginProfile': True
    },
    'AttachUserPolicy': {
        'iam:AttachUserPolicy': True
    },
    'AttachGroupPolicy': {
        'iam:AttachGroupPolicy': True
    },
    'AttachRolePolicy': {
        'iam:AttachRolePolicy': True,
        'sts:AssumeRole': True
    },
    'PutUserPolicy': {
        'iam:PutUserPolicy': True
    },
    'PutGroupPolicy': {
        'iam:PutGroupPolicy': True
    },
    'PutRolePolicy': {
        'iam:PutRolePolicy': True,
        'sts:AssumeRole': True
    },
    'AddUserToGroup': {
        'iam:AddUserToGroup': True
    },
    'UpdateRolePolicyToAssumeIt': {
        'iam:UpdateAssumeRolePolicy': True,
        'sts:AssumeRole': True
    },
    'PassExistingRoleToNewLambdaThenInvoke': {
        'iam:PassRole': True,
        'lambda:CreateFunction': True,
        'lambda:InvokeFunction': True
    },
    'PassExistingRoleToNewLambdaThenTriggerWithNewDynamo': {
        'iam:PassRole': True,
        'lambda:CreateFunction': True,
        'lambda:CreateEventSourceMapping': True,
        'dynamodb:CreateTable': True,
        'dynamodb:PutItem': True
    },
    'PassExistingRoleToNewLambdaThenTriggerWithExistingDynamo': {
        'iam:PassRole': True,
        'lambda:CreateFunction': True,
        'lambda:CreateEventSourceMapping': True
    },
    'PassExistingRoleToNewGlueDevEndpoint': {
        'iam:PassRole': True,
        'glue:CreateDevEndpoint': True
    },
    'UpdateExistingGlueDevEndpoint': {
        'glue:UpdateDevEndpoint': True
    },
    'PassExistingRoleToCloudFormation': {
        'iam:PassRole': True,
        'cloudformation:CreateStack': True
    },
    'PassExistingRoleToNewDataPipeline': {
        'iam:PassRole': True,
        'datapipeline:CreatePipeline': True
    },
    'EditExistingLambdaFunctionWithRole': {
        'lambda:UpdateFunctionCode': True
    }
}

