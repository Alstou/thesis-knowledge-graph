#!/bin/bash
if [ -f json-files/polversions.json ]; then
  rm json-files/polversions.json
fi
touch json-files/polversions.json
echo "[" >> json-files/polversions.json
# # Load the JSON data into a variable
json_data=$(cat json-files/policies.json)

# Use jq to extract the value of the "Arn" key from each object
arns=$(echo "$json_data" | jq -r '.[] | .Arn')
ids=$(echo "$json_data" | jq -r '.[] | .ID')

for id in $ids; do
	ids_array+=($id)	
done

count=0
for arn in $arns; do
	result=$(aws iam list-policy-versions --policy-arn "$arn" --profile cloudgoat2)
  versions=$(echo $result | jq '.Versions')
  num_versions=$(echo $versions | jq 'length')

  if [ $num_versions -ne 1 ];
  then
      #echo "there are $num_versions versions of the policy"
       for ((i=1;i<($num_versions+1);i++)); do
      	output=$(aws iam get-policy-version --policy-arn $arn --version-id v$i --profile cloudgoat2)
      	output_with_arn=$(echo "$output" | jq --arg arn "$arn" --arg id "${ids_array[$count]}-v$i" '. | {Arn: $arn, ID: $id, VersionId: .PolicyVersion.VersionId, PolicyVersion: .PolicyVersion}')
  			echo "$output_with_arn," >> json-files/polversions.json
      done
  else
      echo "only 1 version of policy:" "${ids_array[$count]}"
  fi
  (( count++ ))
 done

sed -i '$s/,$//' json-files/polversions.json
echo "]" >> json-files/polversions.json