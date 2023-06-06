#!/bin/bash

# Run awless list with the --roles flag and save the output to a temporary file
awless list users --format=json > json-files/users.json

# Run awless list with the --policies flag and append the output to the temporary file
awless list policies --format=json > json-files/policies.json

#remove the unnecessary policies
jq 'del(.[] | select(.Name == "AWSSSOServiceRolePolicy"))' json-files/policies.json > json-files/temp.json && mv json-files/temp.json json-files/policies.json
jq 'del(.[] | select(.Name == "AWSElasticLoadBalancingServiceRolePolicy"))' json-files/policies.json > json-files/temp.json && mv json-files/temp.json json-files/policies.json
jq 'del(.[] | select(.Name == "AmazonRDSServiceRolePolicy"))' json-files/policies.json > json-files/temp.json && mv json-files/temp.json json-files/policies.json
jq 'del(.[] | select(.Name == "AWSOrganizationsServiceTrustPolicy"))' json-files/policies.json > json-files/temp.json && mv json-files/temp.json json-files/policies.json
jq 'del(.[] | select(.Name == "AdministratorAccess"))' json-files/policies.json > json-files/temp.json && mv json-files/temp.json json-files/policies.json
jq 'del(.[] | select(.Name == "AWSSupportServiceRolePolicy"))' json-files/policies.json > json-files/temp.json && mv json-files/temp.json json-files/policies.json
jq 'del(.[] | select(.Name == "AWSTrustedAdvisorServiceRolePolicy"))' json-files/policies.json > json-files/temp.json && mv json-files/temp.json json-files/policies.json

# Run awless list with the --users flag and append the output to the temporary file
awless list roles --format=json > json-files/roles.json

#remove unnecessary roles
jq 'del(.[] | select(.Name == "AWSServiceRoleForTrustedAdvisor"))' json-files/roles.json > json-files/temp.json && mv json-files/temp.json json-files/roles.json
jq 'del(.[] | select(.Name == "AWSServiceRoleForElasticLoadBalancing"))' json-files/roles.json > json-files/temp.json && mv json-files/temp.json json-files/roles.json
jq 'del(.[] | select(.Name == "AWSServiceRoleForRDS"))' json-files/roles.json > json-files/temp.json && mv json-files/temp.json json-files/roles.json
jq 'del(.[] | select(.Name == "AWSServiceRoleForOrganizations"))' json-files/roles.json > json-files/temp.json && mv json-files/temp.json json-files/roles.json
jq 'del(.[] | select(.Name == "AWSServiceRoleForSupport"))' json-files/roles.json > json-files/temp.json && mv json-files/temp.json json-files/roles.json
jq 'del(.[] | select(.Name == "AWSServiceRoleForSupport"))' json-files/roles.json > json-files/temp.json && mv json-files/temp.json json-files/roles.json
jq 'del(.[] | select(.Name == "AWSServiceRoleForSSO"))' json-files/roles.json > json-files/temp.json && mv json-files/temp.json json-files/roles.json

awless list instances -r us-east-1 --format=json > json-files/instances.json

awless list instanceprofiles -r us-east-1 --format=json > json-files/profiles.json

awless list groups --format=json > json-files/groups.json

awless list functions --format=json > json-files/functions.json

awless list databases --format=json > json-files/databases.json

awless list volumes --format=json > json-files/volumes.json

awless list buckets --format=json > json-files/buckets.json
awless list s3objects --format=json > json-files/s3objects.json
awless list keypairs --format=json > json-files/keypairs.json
